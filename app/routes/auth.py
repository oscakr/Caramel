from fastapi import APIRouter, Depends, Request, Response, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extracts logged in user from cookie, falling back to Oscar (id=1) for testing."""
    user_id = request.cookies.get("caramel_user_id")
    if user_id:
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                return user
        except Exception:
            pass
    # Default to first user (Oscar)
    user = db.query(User).first()
    return user

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"current_user": current_user, "error": None}
    )

@router.post("/login")
def login_submit(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        (User.username == username.strip()) | (User.email == username.strip())
    ).first()

    if not user or user.password != password.strip():
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "current_user": None,
                "error": "Credenciales inválidas. Puedes usar usuario 'oscar' y contraseña 'password123' o seleccionar un perfil de prueba."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(key="caramel_user_id", value=str(user.id), httponly=True)
    return redirect

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"current_user": current_user, "error": None}
    )

@router.post("/register")
def register_submit(
    request: Request,
    email: str = Form(...),
    carrera: str = Form(...),
    trimestre: int = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if username or email exists
    existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "error": "El nombre de usuario o correo ya está registrado."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    new_user = User(
        username=username.strip(),
        email=email.strip(),
        password=password.strip(),
        full_name=username.capitalize(),
        carrera=carrera.strip(),
        trimestre=trimestre,
        avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(key="caramel_user_id", value=str(new_user.id), httponly=True)
    return redirect

@router.get("/demo-switch/{user_id}")
def demo_switch_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    """Fast switcher to demonstrate how the recommender personalizes for each student profile."""
    user = db.query(User).filter(User.id == user_id).first()
    target_url = request.headers.get("referer", "/")
    redirect = RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    if user:
        redirect.set_cookie(key="caramel_user_id", value=str(user.id), httponly=True)
    return redirect

@router.get("/logout")
def logout():
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(key="caramel_user_id")
    return redirect
