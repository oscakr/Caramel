"""
Caramel UNIMAR - Sincronizador Nube -> Local (Plan B 100% Offline para Defensa)

Clona en modo SOLO LECTURA desde Supabase (PostgreSQL + Storage) hacia el entorno
local (`caramel.db` + `uploads/`), reescribiendo las URLs del bucket a `/uploads/...`
para que `caramel-local` funcione con datos idénticos a Render incluso sin internet.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, select, text

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

UPLOAD_DIR = os.path.join(PROJECT_DIR, "uploads")
LOCAL_DB_PATH = os.path.join(PROJECT_DIR, "caramel.db")
TEMP_DB_PATH = os.path.join(PROJECT_DIR, "caramel.db.sync_tmp")
BACKUP_DB_PATH = os.path.join(PROJECT_DIR, "caramel.db.bak")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
BUCKET = (os.getenv("SUPABASE_STORAGE_BUCKET", "caramel-uploads") or "caramel-uploads").strip()


def _normalize_pg_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _list_bucket_files(prefix: str = "") -> list[str]:
    """Lista recursivamente todos los archivos almacenados en el bucket de Supabase Storage."""
    found: list[str] = []
    offset = 0
    limit = 1000
    endpoint = f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET}"

    while True:
        payload = json.dumps({"prefix": prefix, "limit": limit, "offset": offset}).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=payload,
            method="POST",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            items = json.loads(resp.read().decode("utf-8"))

        if not items:
            break

        for item in items:
            name = (item.get("name") or "").strip("/")
            if not name or name == ".emptyFolderPlaceholder":
                continue
            rel = f"{prefix}/{name}" if prefix else name
            if item.get("id") is None:
                # Subcarpeta en Supabase Storage
                found.extend(_list_bucket_files(rel))
            else:
                found.append(rel)

        if len(items) < limit:
            break
        offset += limit

    return found


def sync_storage_to_local() -> int:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[AVISO] SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY no definidos en .env; omitiendo descarga de Storage.")
        return 0

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    files = _list_bucket_files("")
    print(f"[1/2] Descargando {len(files)} archivo(s) desde Supabase Storage ('{BUCKET}') hacia uploads/ ...")

    downloaded = 0
    for rel in files:
        quoted = urllib.parse.quote(rel, safe="/")
        url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{quoted}"
        req = urllib.request.Request(
            url,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()

        local_path = os.path.join(UPLOAD_DIR, *rel.split("/"))
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f_out:
            f_out.write(data)
        downloaded += 1
        print(f"      ✓ {rel} ({len(data):,} bytes)")

    return downloaded


def _convert_value(val, public_prefix: str):
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, memoryview):
        return bytes(val)
    if isinstance(val, str) and public_prefix and val.startswith(public_prefix):
        rel = urllib.parse.unquote(val[len(public_prefix):]).lstrip("/")
        return f"/uploads/{rel}"
    if isinstance(val, datetime) and val.tzinfo is not None:
        return val.astimezone(timezone.utc).replace(tzinfo=None)
    return val


def sync_postgres_to_sqlite() -> tuple[int, int]:
    if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
        raise RuntimeError("No se encontró una DATABASE_URL de PostgreSQL/Supabase en .env.")

    # Importar modelos en modo local para construir el esquema exacto sin inicializar datos extra
    os.environ["CARAMEL_DB_MODE"] = "local"
    from app.database import Base, engine as app_local_engine
    import app.models  # noqa: F401
    app_local_engine.dispose()

    cloud_engine = create_engine(_normalize_pg_url(DATABASE_URL), pool_pre_ping=True)

    if os.path.exists(TEMP_DB_PATH):
        os.remove(TEMP_DB_PATH)

    local_engine = create_engine(f"sqlite:///{TEMP_DB_PATH}")
    Base.metadata.create_all(bind=local_engine)

    public_prefix = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/" if SUPABASE_URL else ""
    total_rows = 0
    tables_copied = 0

    print("[2/2] Clonando base de datos Supabase PostgreSQL -> caramel.db (SQLite local) ...")
    try:
        pg_inspector = inspect(cloud_engine)
        pg_table_names = set(pg_inspector.get_table_names(schema="public"))

        with cloud_engine.connect() as pg_conn, local_engine.begin() as sq_conn:
            sq_conn.execute(text("PRAGMA foreign_keys = OFF"))
            for table in Base.metadata.sorted_tables:
                if table.name not in pg_table_names:
                    continue
                pg_col_names = {c["name"] for c in pg_inspector.get_columns(table.name, schema="public")}
                common_cols = [col for col in table.columns if col.name in pg_col_names]
                if not common_cols:
                    continue

                rows = pg_conn.execute(select(*common_cols)).mappings().all()
                tables_copied += 1
                if not rows:
                    continue
                converted = [
                    {col.name: _convert_value(row[col.name], public_prefix) for col in common_cols}
                    for row in rows
                ]
                sq_conn.execute(table.insert(), converted)
                total_rows += len(converted)
                print(f"      ✓ {table.name}: {len(converted)} registro(s)")
            sq_conn.execute(text("PRAGMA foreign_keys = ON"))
    finally:
        cloud_engine.dispose()
        local_engine.dispose()

    # Respaldo previo y reemplazo atómico de caramel.db
    try:
        if os.path.exists(LOCAL_DB_PATH):
            shutil.copy2(LOCAL_DB_PATH, BACKUP_DB_PATH)
        os.replace(TEMP_DB_PATH, LOCAL_DB_PATH)
    except PermissionError:
        if os.path.exists(TEMP_DB_PATH):
            try:
                os.remove(TEMP_DB_PATH)
            except OSError:
                pass
        raise RuntimeError(
            "caramel.db está en uso. Detén primero 'caramel-local' (Ctrl+C) y vuelve a ejecutar 'caramel-sync'."
        )

    return tables_copied, total_rows


def main() -> int:
    print("=================================================================")
    print(" Caramel UNIMAR :: Sincronización Nube (Supabase) -> Local Offline")
    print("=================================================================")
    try:
        files_count = sync_storage_to_local()
        tables_count, rows_count = sync_postgres_to_sqlite()
        print("=================================================================")
        print(f"[OK] Sincronización completada:")
        print(f"     • Archivos descargados a uploads/: {files_count}")
        print(f"     • Tablas clonadas a caramel.db:    {tables_count} ({rows_count} registros)")
        print(f"     • Respaldo anterior guardado en:   caramel.db.bak")
        print("     • URLs de Supabase reescritas a /uploads/... para uso 100% offline.")
        print("[*] Ahora puedes ejecutar 'caramel-local' con copia exacta de producción.")
        print("=================================================================")
        return 0
    except Exception as exc:
        print(f"\n[ERROR] No se pudo completar la sincronización: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
