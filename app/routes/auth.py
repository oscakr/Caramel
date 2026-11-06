from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Role
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
                return user
        except Exception:
            pass
    return None

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    """Pantalla 1 del prototipo Figma: Iniciar sesión institucional."""
    current_user = get_current_user(request, db)
    # Si ya tiene sesión activa y no está pidiendo salir, redirige al feed
    if current_user and not request.query_params.get("switch"):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"current_user": None, "error": None}
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

    if not user or not verify_password(clean_pwd, user.password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "current_user": None,
                "error": "Credenciales inválidas. Por favor verifica tu correo institucional (@unimar.edu.ve) y contraseña."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    # Cookie segura conforme a directivas OWASP
    redirect.set_cookie(
        key="caramel_user_id",
        value=str(user.id),
        max_age=604800, # 7 días
        httponly=True,
        samesite="lax"
    )
    return redirect

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    """Pantalla de Registro & Onboarding del prototipo Figma."""
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
    rol_nombre: str = Form("Estudiante"),
    carrera: str = Form(...),
    trimestre: int = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Registro formal de usuarios en las tablas USUARIOS y ROLES:
    - Validación obligatoria de dominio institucional (@unimar.edu.ve).
    - Cifrado de contraseña con bcrypt (factor de coste 12).
    - Asignación de rol jerárquico (Estudiante, Docente, Curador).
    - Puntos de reputación iniciales de bienvenida.
    """
    clean_user = username.strip().lower()
    clean_email = email.strip().lower()
    form_data = {
        "full_name": full_name,
        "email": email,
        "rol_nombre": rol_nombre,
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

    # 2. Validación de fortaleza de contraseña
    is_valid, msg = validate_password_strength(password)
    if not is_valid:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"current_user": None, "error": msg, "form_data": form_data},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 3. Verificar unicidad de usuario y correo
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

    # Determinar id_rol según catálogo
    id_rol = 1
    if "docente" in rol_nombre.lower():
        id_rol = 2
    elif "curador" in rol_nombre.lower() or "admin" in rol_nombre.lower():
        id_rol = 3

    # Cifrado seguro
    pwd_hash = hash_password(password)

    new_user = User(
        username=clean_user,
        email=clean_email,
        password=pwd_hash,
        full_name=full_name.strip(),
        carrera=carrera.strip(),
        trimestre=trimestre,
        avatar_url=f"https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        id_rol=id_rol,
        rol_nombre=rol_nombre,
        puntos_reputacion=50 # Puntos de bienvenida por registro
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

@router.get("/logout")
def logout():
    """Cierra la sesión institucional y redirige al login."""
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(key="caramel_user_id")
    return redirect

@router.get("/demo-switch/{user_id}")
def demo_switch(user_id: int, db: Session = Depends(get_db)):
    """Selector rápido de perfiles de prueba para la defensa de tesis."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key="caramel_user_id",
        value=str(user.id),
        max_age=604800,
        httponly=True,
        samesite="lax"
    )
    return redirect
