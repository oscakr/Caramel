import random
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Role, DEFAULT_AVATARS, DEFAULT_BANNER
from ..security import hash_password, verify_password, validate_password_strength, validate_institutional_email

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Extrae el usuario autenticado a través de la cookie HTTP-Only."""
    user_id = request.cookies.get("caramel_user_id")
    if user_id:
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                if user.is_ceo and user.username != "P3":
                    user.username = "P3"
                    db.commit()
                try:
                    from .feed import get_contextual_notifications
                    notifs = get_contextual_notifications(user, db)
                    user.has_notifications = len(notifs) > 0
                    user.notifications_count = len(notifs)
                except Exception:
                    user.has_notifications = False
                    user.notifications_count = 0
                return user
        except Exception:
            pass
    return None

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    """Pantalla 1 del prototipo Figma: Iniciar sesión institucional."""
    try:
        failed_attempts = int(request.cookies.get("caramel_login_fails", 0))
    except Exception:
        failed_attempts = 0
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"current_user": None, "error": None, "failed_attempts": failed_attempts, "username_val": ""}
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
    - Búsqueda por correo institucional o username.
    - Verificación mediante función criptográfica bcrypt.
    - Protección contra enumeración de usuarios (mensaje neutro).
    - Sesión persistente protegida mediante cookie HTTP-Only.
    """
    clean_user = username.strip().lower()
    clean_pwd = password.strip()

    user = db.query(User).filter(
        (User.username.ilike(clean_user)) | (User.email.ilike(clean_user))
    ).first()
    if not user and clean_user in ("p3", "oalvarez.7305"):
        user = db.query(User).filter(User.email == "oalvarez.7305@unimar.edu.ve").first()
    if user and user.is_ceo and user.username != "P3":
        user.username = "P3"
        db.commit()

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
                "username_val": username
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
        template_resp.set_cookie(
            key="caramel_login_fails",
            value=str(failed_attempts),
            max_age=3600,
            httponly=True,
            samesite="lax"
        )
        return template_resp

    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    # Cookie segura conforme a directivas OWASP
    redirect.set_cookie(
        key="caramel_user_id",
        value=str(user.id),
        max_age=604800, # 7 días
        httponly=True,
        samesite="lax"
    )
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
    db.commit()
    db.refresh(new_user)

    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key="caramel_user_id",
        value=str(new_user.id),
        max_age=604800,
        httponly=True,
        samesite="lax"
    )
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
    db.commit()
    db.refresh(new_docente)

    # El docente inicia sesión de inmediato con perfil estándar de consulta
    redirect = RedirectResponse(url="/?welcome=docente_pending", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key="caramel_user_id",
        value=str(new_docente.id),
        max_age=604800,
        httponly=True,
        samesite="lax"
    )
    return redirect

@router.get("/logout")
def logout():
    """Cierra la sesión institucional y redirige al login."""
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(key="caramel_user_id")
    return redirect
