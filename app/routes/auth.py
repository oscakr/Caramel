import hashlib
import os
import random
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db, engine, Base
from ..models import User, Usuario, Role, ReviewLike, PasswordResetToken, PasswordResetRequest, DocumentValidation, DEFAULT_AVATARS, DEFAULT_BANNER
from ..security import (
    hash_password,
    verify_password,
    is_bcrypt_hash,
    validate_password_strength,
    validate_institutional_email,
    sign_session_user_id,
    verify_session_cookie,
    SESSION_MAX_AGE_SECONDS,
)

SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "soporte.caramel@unimar.edu.ve").strip()


def _set_signed_session_cookie(response: Response, request: Request, user_id: int) -> None:
    """Emite la cookie de sesión firmada con HMAC-SHA256, HTTP-Only, SameSite=Lax y Secure en HTTPS."""
    response.set_cookie(
        key="caramel_user_id",
        value=sign_session_user_id(user_id),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=(request.url.scheme == "https"),
    )

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

_NOTIF_SCHEMA_READY = False
_RESET_SCHEMA_READY = False


def ensure_notification_schema():
    """Garantiza tablas auxiliares y columnas de notificaciones una sola vez por proceso."""
    global _NOTIF_SCHEMA_READY
    if _NOTIF_SCHEMA_READY:
        return
    try:
        Base.metadata.create_all(
            bind=engine,
            tables=[
                DocumentValidation.__table__,
                ReviewLike.__table__,
                PasswordResetToken.__table__,
                PasswordResetRequest.__table__,
            ],
        )
    except Exception:
        pass
    for ddl in (
        "ALTER TABLE users ADD COLUMN notifications_cleared_at TIMESTAMP",
        "ALTER TABLE documents ADD COLUMN verified_at TIMESTAMP",
        "ALTER TABLE documents ADD COLUMN consensus_state VARCHAR(30) DEFAULT 'pendiente'",
    ):
        try:
            with engine.begin() as conn:
                conn.execute(text(ddl))
        except Exception:
            pass
    # Inicializar consensus_state en documentos históricos ya resueltos antes de esta migración
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE documents SET consensus_state = 'aprobado_definitivo' "
                "WHERE status = 'aprobado' AND (consensus_state IS NULL OR consensus_state = '' OR consensus_state = 'pendiente')"
            ))
            conn.execute(text(
                "UPDATE documents SET consensus_state = 'rechazado' "
                "WHERE status = 'rechazado' AND (consensus_state IS NULL OR consensus_state = '' OR consensus_state = 'pendiente')"
            ))
    except Exception:
        pass
    _NOTIF_SCHEMA_READY = True
    _ensure_reset_tokens_table()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Extrae y valida el usuario autenticado mediante cookie de sesión firmada (HMAC-SHA256)."""
    ensure_notification_schema()
    raw_cookie = request.cookies.get("caramel_user_id")
    verified_user_id = verify_session_cookie(raw_cookie)
    if verified_user_id is not None:
        try:
            user = db.query(User).filter(User.id == verified_user_id).first()
            if user:
                try:
                    from .feed import get_contextual_notifications
                    notifs = get_contextual_notifications(user, db)
                    user.has_notifications = len(notifs) > 0
                    user.notifications_count = len(notifs)
                    sig_raw = "|".join(str(n.get("notif_id", "")) for n in notifs)
                    user.notifications_signature = (
                        hashlib.sha1(sig_raw.encode("utf-8")).hexdigest()[:16] if sig_raw else ""
                    )
                except Exception:
                    db.rollback()
                    user.has_notifications = False
                    user.notifications_count = 0
                    user.notifications_signature = ""
                return user
        except Exception:
            db.rollback()
    return None

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    """Pantalla 1 del prototipo Figma: Iniciar sesión institucional."""
    try:
        failed_attempts = int(request.cookies.get("caramel_login_fails", 0))
    except Exception:
        failed_attempts = 0
    reset_param = request.query_params.get("reset", "")
    reset_success = reset_param in ("success", "password", "email_and_password")
    reset_email_updated = reset_param == "email_and_password"
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "current_user": None,
            "error": None,
            "failed_attempts": failed_attempts,
            "username_val": "",
            "reset_success": reset_success,
            "reset_email_updated": reset_email_updated,
            "support_email": SUPPORT_EMAIL,
        }
    )

@router.post("/login")
def login_submit(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Autenticación institucional bajo estándar ISO/IEC 27001 & ISO 21001:
    - Búsqueda por correo institucional o username en base de datos (sin cuentas hardcodeadas).
    - Verificación mediante función criptográfica bcrypt (auto-migración transparente de hashes heredados).
    - Protección contra enumeración de usuarios (mensaje neutro).
    - Sesión persistente firmada con HMAC-SHA256 en cookie HTTP-Only.
    """
    clean_user = username.strip().lower()
    clean_pwd = password.strip()

    user = db.query(User).filter(
        (User.username.ilike(clean_user)) | (User.email.ilike(clean_user))
    ).first()

    if not user or not verify_password(clean_pwd, user.password):
        try:
            prev_fails = int(request.cookies.get("caramel_login_fails", 0))
        except Exception:
            prev_fails = 0
        failed_attempts = prev_fails + 1

        template_resp = templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "current_user": None,
                "error": "Credenciales inválidas. Por favor verifica tu correo institucional (@unimar.edu.ve) y contraseña.",
                "failed_attempts": failed_attempts,
                "username_val": username,
                "support_email": SUPPORT_EMAIL,
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
        template_resp.set_cookie(
            key="caramel_login_fails",
            value=str(failed_attempts),
            max_age=3600,
            httponly=True,
            samesite="lax",
            secure=(request.url.scheme == "https"),
        )
        return template_resp

    # Auto-migración transparente a bcrypt factor 12 si la cuenta tenía un formato legado
    if not is_bcrypt_hash(user.password):
        try:
            user.password = hash_password(clean_pwd)
            db.commit()
        except Exception:
            db.rollback()

    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    _set_signed_session_cookie(redirect, request, user.id)
    redirect.delete_cookie(key="caramel_login_fails")
    return redirect

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    """Pantalla de Registro Exclusivo para Estudiantes UNIMAR."""
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"current_user": None, "error": None, "form_data": {}}
    )

@router.post("/register")
def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    carrera: str = Form(...),
    trimestre: int = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Registro exclusivo de Estudiantes bajo principio de menor privilegio (PoLP):
    - Validación obligatoria de dominio institucional (@unimar.edu.ve).
    - Cifrado de contraseña con bcrypt (factor de coste 12).
    - Asignación inmutable del rol Estudiante y título honorífico 'Casi Ingeniero'.
    - Activación inmediata (validado_por_ceo = 1) para la comunidad estudiantil.
    """
    clean_user = username.strip().lower()
    clean_email = email.strip().lower()
    form_data = {
        "full_name": full_name,
        "email": email,
        "carrera": carrera,
        "trimestre": trimestre,
        "username": username
    }

    # 1. Validación de correo institucional obligatorio (@unimar.edu.ve)
    email_valid, email_msg = validate_institutional_email(clean_email)
    if not email_valid:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"current_user": None, "error": email_msg, "form_data": form_data},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 2. Validación de confirmación de contraseña
    if confirm_password is not None and (not confirm_password.strip() or password != confirm_password):
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "error": "Las contraseñas no coinciden. Por favor confirma tu contraseña exactamente.",
                "form_data": form_data
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 3. Validación de fortaleza de contraseña
    is_valid, msg = validate_password_strength(password)
    if not is_valid:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"current_user": None, "error": msg, "form_data": form_data},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 4. Verificar unicidad de usuario y correo
    existing = db.query(User).filter(
        (User.username.ilike(clean_user)) | (User.email.ilike(clean_email))
    ).first()

    if existing:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "error": "El usuario o correo institucional ya se encuentra registrado.",
                "form_data": form_data
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Cifrado seguro
    pwd_hash = hash_password(password)

    new_user = User(
        username=clean_user,
        email=clean_email,
        password=pwd_hash,
        full_name=full_name.strip(),
        carrera=carrera.strip(),
        trimestre=trimestre,
        avatar_url=random.choice(DEFAULT_AVATARS),
        banner_url=DEFAULT_BANNER,
        id_rol=1,
        rol_nombre="Estudiante",
        titulo_honorifico="Casi Ingeniero",
        puntos_reputacion=50, # Puntos de bienvenida por registro
        validado_por_ceo=1
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "error": "El usuario o correo institucional ya se encuentra registrado.",
                "form_data": form_data
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    _set_signed_session_cookie(redirect, request, new_user.id)
    return redirect

@router.get("/docente/registro", response_class=HTMLResponse)
def docente_register_page(request: Request, db: Session = Depends(get_db)):
    """Portal exclusivo de acreditación y registro para el personal docente UNIMAR."""
    return templates.TemplateResponse(
        request=request,
        name="docente_register.html",
        context={"current_user": None, "error": None, "form_data": {}}
    )

@router.post("/docente/registro")
def docente_register_submit(
    request: Request,
    full_name: str = Form(...),
    titulo_honorifico: str = Form("Profesor"),
    cedula: str = Form(...),
    codigo_credencial: Optional[str] = Form("DOC-UNIMAR-2026"),
    email: str = Form(...),
    catedra_asignada: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Registro y Acreditación Docente con cuarentena de seguridad:
    - Validación obligatoria de correo institucional (@unimar.edu.ve).
    - Captura de Cédula de Identidad y Cátedra asignada.
    - Asignación de rol Docente de Cátedra (id_rol = 2).
    - Estado en cuarentena (validado_por_ceo = 0): La cuenta opera con perfil estándar
      de consulta hasta su homologación manual por el CEO / Decanato de Ingeniería.
    """
    clean_user = username.strip().lower()
    clean_email = email.strip().lower()
    form_data = {
        "full_name": full_name,
        "titulo_honorifico": titulo_honorifico,
        "cedula": cedula,
        "codigo_credencial": codigo_credencial,
        "email": email,
        "catedra_asignada": catedra_asignada,
        "username": username
    }

    # 1. Validación de correo institucional obligatorio (@unimar.edu.ve)
    email_valid, email_msg = validate_institutional_email(clean_email)
    if not email_valid:
        return templates.TemplateResponse(
            request=request,
            name="docente_register.html",
            context={"current_user": None, "error": email_msg, "form_data": form_data},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 2. Validación de confirmación de contraseña
    if confirm_password is not None and (not confirm_password.strip() or password != confirm_password):
        return templates.TemplateResponse(
            request=request,
            name="docente_register.html",
            context={
                "current_user": None,
                "error": "Las contraseñas no coinciden. Por favor confirma tu contraseña exactamente.",
                "form_data": form_data
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 3. Validación de fortaleza de contraseña
    is_valid, msg = validate_password_strength(password)
    if not is_valid:
        return templates.TemplateResponse(
            request=request,
            name="docente_register.html",
            context={"current_user": None, "error": msg, "form_data": form_data},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 4. Verificar unicidad de usuario y correo
    existing = db.query(User).filter(
        (User.username.ilike(clean_user)) | (User.email.ilike(clean_email))
    ).first()

    if existing:
        return templates.TemplateResponse(
            request=request,
            name="docente_register.html",
            context={
                "current_user": None,
                "error": "El usuario o correo institucional ya se encuentra registrado.",
                "form_data": form_data
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Cifrado seguro
    pwd_hash = hash_password(password)

    new_docente = User(
        username=clean_user,
        email=clean_email,
        password=pwd_hash,
        full_name=full_name.strip(),
        carrera="Ingeniería de Sistemas",
        trimestre=0, # Docente / Egresado
        avatar_url=random.choice(DEFAULT_AVATARS),
        banner_url=DEFAULT_BANNER,
        id_rol=2,
        rol_nombre="Docente de Cátedra",
        catedra_asignada=catedra_asignada.strip() if catedra_asignada else "Todas las Cátedras del Eje",
        titulo_honorifico=titulo_honorifico.strip() if titulo_honorifico else "Profesor",
        puntos_reputacion=100,
        validado_por_ceo=0 # CUARENTENA: Espera ratificación del CEO para validar recursos
    )
    db.add(new_docente)
    try:
        db.commit()
        db.refresh(new_docente)
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="docente_register.html",
            context={
                "current_user": None,
                "error": "El usuario o correo institucional ya se encuentra registrado.",
                "form_data": form_data
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # El docente inicia sesión de inmediato con perfil estándar de consulta
    redirect = RedirectResponse(url="/?welcome=docente_pending", status_code=status.HTTP_303_SEE_OTHER)
    _set_signed_session_cookie(redirect, request, new_docente.id)
    return redirect

@router.get("/logout")
def logout():
    """Cierra la sesión institucional y redirige al login."""
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(key="caramel_user_id")
    return redirect


def _ensure_reset_tokens_table():
    """Garantiza que existan las tablas y columnas de restablecimiento una sola vez por proceso."""
    global _RESET_SCHEMA_READY
    if _RESET_SCHEMA_READY:
        return
    try:
        Base.metadata.create_all(
            bind=engine,
            tables=[PasswordResetToken.__table__, PasswordResetRequest.__table__],
        )
    except Exception:
        pass
    # Migración segura de columnas nuevas si la tabla ya existía previamente
    for ddl in (
        "ALTER TABLE password_reset_tokens ADD COLUMN email_changed SMALLINT NOT NULL DEFAULT 0",
        "ALTER TABLE password_reset_tokens ADD COLUMN used_at TIMESTAMP",
    ):
        try:
            with engine.begin() as conn:
                conn.execute(text(ddl))
        except Exception:
            pass
    _RESET_SCHEMA_READY = True


@router.post("/api/support/password-reset-request")
async def create_password_reset_request(request: Request, db: Session = Depends(get_db)):
    """
    Registra un aviso interno para el CEO cuando un usuario pulsa 'Contacta al soporte'
    desde /login para restablecer su contraseña.
    """
    _ensure_reset_tokens_table()

    identifier = ""
    try:
        payload = await request.json()
        identifier = str(payload.get("identifier") or "").strip()[:150]
    except Exception:
        pass

    clean_id = identifier.lower()
    matched_user = None
    if clean_id:
        matched_user = db.query(User).filter(
            (User.username.ilike(clean_id)) | (User.email.ilike(clean_id))
        ).first()

    # Evitar duplicados si ya existe una solicitud pendiente idéntica en los últimos 5 minutos
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    existing_recent = db.query(PasswordResetRequest).filter(
        PasswordResetRequest.status == "pendiente",
        PasswordResetRequest.identifier == (identifier or "No especificado"),
        PasswordResetRequest.created_at >= five_min_ago,
    ).first()

    if not existing_recent:
        req = PasswordResetRequest(
            identifier=identifier or "No especificado",
            matched_user_id=matched_user.id if matched_user else None,
            status="pendiente",
        )
        db.add(req)
        db.commit()

    return JSONResponse({"success": True})


@router.post("/api/ceo/dismiss-reset-request/{req_id}")
def ceo_dismiss_reset_request(req_id: int, request: Request, db: Session = Depends(get_db)):
    """Permite al CEO descartar una solicitud de soporte ya revisada."""
    current_user = get_current_user(request, db)
    if not current_user or not current_user.is_ceo:
        return JSONResponse({"success": False, "error": "Solo CEO."}, status_code=403)

    _ensure_reset_tokens_table()
    req = db.query(PasswordResetRequest).filter(PasswordResetRequest.id == req_id).first()
    if req:
        req.status = "descartada"
        db.commit()
    return JSONResponse({"success": True})


def _hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


@router.post("/api/ceo/generate-reset-link")
async def ceo_generate_reset_link(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint exclusivo del CEO para emitir un enlace temporal (30 min, 1 solo uso)
    de restablecimiento de contraseña, con opción de desbloquear la edición del correo.
    """
    current_user = get_current_user(request, db)
    if not current_user or not current_user.is_ceo:
        return JSONResponse(
            {"success": False, "error": "Acceso restringido exclusivamente al CEO."},
            status_code=status.HTTP_403_FORBIDDEN,
        )

    _ensure_reset_tokens_table()

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "Solicitud inválida."}, status_code=400)

    target_user_id = payload.get("user_id")
    allow_email_edit = bool(payload.get("allow_email_edit", False))
    request_id = payload.get("request_id")

    if not target_user_id:
        return JSONResponse({"success": False, "error": "Selecciona un usuario válido."}, status_code=400)

    try:
        target_user_id_int = int(target_user_id)
    except (ValueError, TypeError):
        return JSONResponse({"success": False, "error": "Identificador de usuario inválido."}, status_code=400)

    target_user = db.query(User).filter(User.id == target_user_id_int).first()
    if not target_user:
        return JSONResponse({"success": False, "error": "Usuario no encontrado."}, status_code=404)

    # Invalida cualquier enlace anterior pendiente de este mismo usuario
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == target_user.id,
        PasswordResetToken.used == 0,
    ).update({"used": 1})

    # Marca como atendidas las solicitudes de soporte pendientes de este usuario (y el request_id exacto)
    if request_id is not None and str(request_id).strip() != "":
        try:
            db.query(PasswordResetRequest).filter(
                PasswordResetRequest.id == int(request_id)
            ).update({"status": "atendida"}, synchronize_session=False)
        except (ValueError, TypeError):
            pass

    db.query(PasswordResetRequest).filter(
        PasswordResetRequest.status == "pendiente",
        (
            (PasswordResetRequest.matched_user_id == target_user.id)
            | (PasswordResetRequest.identifier.ilike(target_user.email))
            | (PasswordResetRequest.identifier.ilike(target_user.username))
        ),
    ).update({"status": "atendida"}, synchronize_session=False)

    raw_token = secrets.token_urlsafe(32)
    token_record = PasswordResetToken(
        user_id=target_user.id,
        token_hash=_hash_reset_token(raw_token),
        allow_email_edit=1 if allow_email_edit else 0,
        used=0,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        created_by_id=current_user.id,
    )
    db.add(token_record)
    db.commit()

    base_url = str(request.base_url).rstrip("/")
    reset_url = f"{base_url}/reset-password/{raw_token}"

    return JSONResponse({
        "success": True,
        "reset_url": reset_url,
        "expires_minutes": 30,
        "allow_email_edit": allow_email_edit,
        "user_email": target_user.email,
        "user_name": target_user.full_name,
    })


@router.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_page(token: str, request: Request, db: Session = Depends(get_db)):
    """Vista protegida por token temporal para restablecer contraseña (y correo solo si el CEO lo habilitó)."""
    _ensure_reset_tokens_table()

    token_hash = _hash_reset_token(token)
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not record or record.used == 1 or record.expires_at < datetime.utcnow():
        reason = (
            "Este enlace ya fue utilizado anteriormente."
            if (record and record.used == 1)
            else "Este enlace no es válido o ha expirado (validez de 30 minutos). Solicita uno nuevo al equipo de soporte."
        )
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "current_user": None,
                "token_invalid": True,
                "invalid_reason": reason,
                "allow_email_edit": False,
                "target_user": None,
                "token": token,
                "error": None,
                "form_email": "",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    target_user = db.query(User).filter(User.id == record.user_id).first()
    if not target_user:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "current_user": None,
                "token_invalid": True,
                "invalid_reason": "La cuenta asociada a este enlace ya no existe.",
                "allow_email_edit": False,
                "target_user": None,
                "token": token,
                "error": None,
                "form_email": "",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={
            "current_user": None,
            "token_invalid": False,
            "invalid_reason": None,
            "allow_email_edit": bool(record.allow_email_edit),
            "target_user": target_user,
            "token": token,
            "error": None,
            "form_email": target_user.email,
        },
    )


@router.post("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_submit(
    token: str,
    request: Request,
    password: str = Form(...),
    confirm_password: str = Form(...),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Procesa el cambio de contraseña (y actualización de correo solo si el token fue autorizado por el CEO)."""
    _ensure_reset_tokens_table()

    token_hash = _hash_reset_token(token)
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not record or record.used == 1 or record.expires_at < datetime.utcnow():
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "current_user": None,
                "token_invalid": True,
                "invalid_reason": "Este enlace ya fue utilizado o ha expirado. Solicita uno nuevo a soporte.",
                "allow_email_edit": False,
                "target_user": None,
                "token": token,
                "error": None,
                "form_email": "",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    target_user = db.query(User).filter(User.id == record.user_id).first()
    if not target_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    allow_email_edit = bool(record.allow_email_edit)
    submitted_email = (email or target_user.email).strip().lower() if allow_email_edit else target_user.email

    def _render_error(msg: str):
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "current_user": None,
                "token_invalid": False,
                "invalid_reason": None,
                "allow_email_edit": allow_email_edit,
                "target_user": target_user,
                "token": token,
                "error": msg,
                "form_email": submitted_email,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 1. Validar contraseñas
    if password != confirm_password:
        return _render_error("Las contraseñas no coinciden. Verifica ambos campos.")

    pwd_ok, pwd_msg = validate_password_strength(password)
    if not pwd_ok:
        return _render_error(pwd_msg)

    # 2. Solo si el CEO desbloqueó la edición del correo en el token, validar y actualizar correo
    old_email = target_user.email
    did_change_email = False
    if allow_email_edit and submitted_email != old_email.lower():
        email_ok, email_msg = validate_institutional_email(submitted_email)
        if not email_ok:
            return _render_error(email_msg)

        duplicate_user = db.query(User).filter(
            User.email.ilike(submitted_email),
            User.id != target_user.id,
        ).first()
        if duplicate_user:
            return _render_error("Ese correo institucional ya pertenece a otra cuenta registrada.")

        target_user.email = submitted_email
        did_change_email = True

    # 3. Guardar nueva contraseña cifrada con bcrypt y quemar el token (un solo uso)
    new_hash = hash_password(password)
    target_user.password = new_hash
    record.used = 1
    record.used_at = datetime.utcnow()
    record.email_changed = 1 if did_change_email else 0

    # Sincronizar espejo en tabla 'usuarios' con savepoint seguro (evita abortar la transacción en PostgreSQL)
    try:
        with db.begin_nested():
            if did_change_email:
                db.execute(
                    text(
                        "UPDATE usuarios SET password_hash = :pwd, correo_institucional = :new_email "
                        "WHERE LOWER(correo_institucional) = :old_email"
                    ),
                    {"pwd": new_hash, "new_email": submitted_email, "old_email": old_email.lower()},
                )
            else:
                db.execute(
                    text(
                        "UPDATE usuarios SET password_hash = :pwd "
                        "WHERE LOWER(correo_institucional) = :old_email"
                    ),
                    {"pwd": new_hash, "old_email": old_email.lower()},
                )
    except Exception:
        pass

    db.commit()

    reset_flag = "email_and_password" if did_change_email else "password"
    redirect = RedirectResponse(url=f"/login?reset={reset_flag}", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(key="caramel_login_fails")
    return redirect
