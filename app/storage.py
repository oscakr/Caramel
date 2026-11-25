"""
Almacenamiento híbrido de archivos para Caramel UNIMAR:
- Modo ONLINE (Supabase PostgreSQL + credenciales configuradas): sube y elimina archivos
  en Supabase Storage (bucket público persistente, inmune a reinicios de Render).
- Modo LOCAL (`caramel-local` / SQLite) o sin credenciales cloud: guarda en carpeta local `uploads/`.
"""
from __future__ import annotations

import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from .database import IS_LOCAL_DB

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
SUPABASE_STORAGE_BUCKET = (os.getenv("SUPABASE_STORAGE_BUCKET", "caramel-uploads") or "caramel-uploads").strip()

_EXTRA_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".txt": "text/plain; charset=utf-8",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def is_cloud_storage_enabled() -> bool:
    """Usa Supabase Storage cuando la app corre en modo online y tiene credenciales válidas."""
    return (not IS_LOCAL_DB) and bool(SUPABASE_URL) and bool(SUPABASE_SERVICE_ROLE_KEY)


def _normalize_rel_path(rel_path: str) -> str:
    clean = rel_path.replace("\\", "/").lstrip("/")
    if not clean or ".." in clean.split("/"):
        raise ValueError(f"Ruta de archivo inválida: {rel_path!r}")
    return clean


def _guess_content_type(rel_path: str, explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    ext = os.path.splitext(rel_path)[1].lower()
    if ext in _EXTRA_MIME_TYPES:
        return _EXTRA_MIME_TYPES[ext]
    guessed, _ = mimetypes.guess_type(rel_path)
    return guessed or "application/octet-stream"


def _cloud_public_prefix() -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/"


def expected_url(rel_path: str) -> str:
    """Devuelve la URL pública final que tendrá el archivo según el modo activo."""
    clean = _normalize_rel_path(rel_path)
    if is_cloud_storage_enabled():
        quoted = urllib.parse.quote(clean, safe="/")
        return f"{_cloud_public_prefix()}{quoted}"
    return f"/uploads/{clean}"


def _write_local(clean_rel_path: str, data: bytes) -> str:
    local_path = os.path.join(UPLOAD_DIR, *clean_rel_path.split("/"))
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f_out:
        f_out.write(data)
    return f"/uploads/{clean_rel_path}"


def upload_bytes(rel_path: str, data: bytes, content_type: Optional[str] = None) -> str:
    """
    Sube bytes a Supabase Storage (modo online) o a `uploads/` (modo local).
    Si ocurre un error de red inesperado en modo online, hace fallback local seguro.
    """
    clean = _normalize_rel_path(rel_path)
    if not is_cloud_storage_enabled():
        return _write_local(clean, data)

    mime = _guess_content_type(clean, content_type)
    quoted = urllib.parse.quote(clean, safe="/")
    endpoint = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_STORAGE_BUCKET}/{quoted}"
    req = urllib.request.Request(
        endpoint,
        data=data,
        method="POST",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": mime,
            "x-upsert": "true",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if 200 <= resp.status < 300:
                return f"{_cloud_public_prefix()}{quoted}"
    except Exception as exc:
        print(f"[Caramel Storage] Error subiendo '{clean}' a Supabase Storage ({exc}); usando fallback local.")

    return _write_local(clean, data)


def extract_managed_rel_path(url: Optional[str]) -> Optional[str]:
    """Extrae la ruta relativa gestionada si la URL pertenece a `/uploads/` o al bucket de Supabase."""
    if not url:
        return None
    if url.startswith("/uploads/"):
        raw = url[len("/uploads/"):].strip()
        try:
            return _normalize_rel_path(raw)
        except ValueError:
            return None
    if SUPABASE_URL:
        prefix = _cloud_public_prefix()
        if url.startswith(prefix):
            raw = urllib.parse.unquote(url[len(prefix):].strip())
            try:
                return _normalize_rel_path(raw)
            except ValueError:
                return None
    return None


def delete_uploaded_url(url: Optional[str]) -> bool:
    """Elimina un archivo gestionado de Supabase Storage o de la carpeta local `uploads/`."""
    rel = extract_managed_rel_path(url)
    if not rel:
        return False

    if url and url.startswith("/uploads/"):
        local_path = os.path.join(UPLOAD_DIR, *rel.split("/"))
        if os.path.isfile(local_path):
            try:
                os.remove(local_path)
                return True
            except OSError:
                return False
        return False

    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        quoted = urllib.parse.quote(rel, safe="/")
        endpoint = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_STORAGE_BUCKET}/{quoted}"
        req = urllib.request.Request(
            endpoint,
            method="DELETE",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return 200 <= resp.status < 300
        except Exception:
            return False
    return False
