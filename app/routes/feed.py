from fastapi import APIRouter, Depends, Request, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
import os
import uuid
import re
from datetime import datetime, timedelta

from ..database import get_db, engine, Base
from ..models import User, Document, CuratedList, Review, ReviewLike, Friendship, Bookmark
from ..recommender import AcademicRecommender
from .auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_class=HTMLResponse)
def home_feed(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    recommender = AcademicRecommender(db)

    # 1. Populares en este trimestre
    popular_in_trimester = recommender.get_popular_in_trimester(current_user, limit=8)

    # 2. Listas que podrían servirte
    curated_lists = db.query(CuratedList).all()

    # 3. Reviews recientes de tus amigos
    friendships = db.query(Friendship).filter(
        (Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id)
    ).all()
    friend_ids = set()
    for f in friendships:
        friend_ids.add(f.friend_id if f.user_id == current_user.id else f.user_id)

    friends_reviews = db.query(Review).filter(
        Review.user_id.in_(list(friend_ids))
    ).order_by(Review.created_at.desc()).limit(10).all()

    # Fallback to general recent reviews if user has no friend reviews yet
    if not friends_reviews:
        friends_reviews = db.query(Review).order_by(Review.created_at.desc()).limit(10).all()

    # 4. Hybrid Recommendations with Explainability
    recommendations = recommender.get_recommendations(current_user.id, limit=5)

    # 5. Pending materials and teacher validations count
    pending_validation_count = 0
    if current_user.can_validate:
        pending_validation_count = db.query(Document).filter(Document.status == "pendiente").count()
        if current_user.is_ceo:
            pending_docentes_count = db.query(User).filter(User.id_rol >= 2, User.validado_por_ceo == 0).count()
            pending_validation_count += pending_docentes_count

    # Check which reviews the user has liked ("Me Sirve")
    try:
        Base.metadata.create_all(bind=engine, tables=[ReviewLike.__table__])
        liked_review_ids = set(
            r[0] for r in db.query(ReviewLike.review_id).filter(
                ReviewLike.user_id == current_user.id
            ).all()
        )
    except Exception:
        liked_review_ids = set()

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "current_user": current_user,
            "active_nav": "feed",
            "popular_in_trimester": popular_in_trimester,
            "curated_lists": curated_lists,
            "friends_reviews": friends_reviews,
            "recommendations": recommendations,
            "pending_validation_count": pending_validation_count,
            "liked_review_ids": liked_review_ids,
        }
    )

@router.get("/explore", response_class=HTMLResponse)
def explore_catalog(
    request: Request,
    q: str = None,
    catedra: str = None,
    materia: str = None,
    trimestre: int = None,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    official_catedras = [
        "Técnicas de Programación",
        "Programación I",
        "Programación II",
        "Estructura de Datos",
        "Programación III",
        "Sistemas I",
        "Base de Datos I",
        "Programación IV",
        "Sistemas II",
        "Base de Datos II",
        "Sistemas III",
        "Sistemas Operativos",
        "Sistemas de Información Gerencial",
        "Metodología de Desarrollo de Software"
    ]

    query_builder = db.query(Document).filter(Document.status == "aprobado")

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query_builder = query_builder.filter(
            or_(
                Document.title.ilike(search_term),
                Document.authors.ilike(search_term),
                Document.materias.ilike(search_term),
                Document.tags.ilike(search_term),
                Document.description.ilike(search_term)
            )
        )

    selected_catedra = (catedra or materia or "").strip()
    if selected_catedra:
        search_cat = f"%{selected_catedra}%"
        query_builder = query_builder.filter(
            or_(
                Document.materias.ilike(search_cat),
                Document.title.ilike(search_cat)
            )
        )

    if trimestre:
        query_builder = query_builder.filter(Document.trimestres.ilike(f"%{trimestre}%"))

    documents = query_builder.order_by(Document.rating_avg.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="explore.html",
        context={
            "current_user": current_user,
            "active_nav": "explore",
            "documents": documents,
            "query": q,
            "selected_catedra": selected_catedra,
            "catedras": official_catedras,
            "selected_trimestre": trimestre
        }
    )

@router.get("/recommender-lab", response_class=HTMLResponse)
def recommender_lab(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Acceso estrictamente reservado para rango CEO (Oscar Alvarez)
    if not getattr(current_user, "is_ceo", False):
        return RedirectResponse(url="/?error=unauthorized_ceo", status_code=status.HTTP_303_SEE_OTHER)

    recommender = AcademicRecommender(db)
    recommendations = recommender.get_recommendations(current_user.id, limit=10)

    return templates.TemplateResponse(
        request=request,
        name="recommender_lab.html",
        context={
            "current_user": current_user,
            "active_nav": "lab",
            "recommendations": recommendations,
        }
    )

@router.get("/profile", response_class=HTMLResponse)
@router.get("/profile/{user_id}", response_class=HTMLResponse)
def user_profile(request: Request, user_id: str = None, db: Session = Depends(get_db)):
    """Visualización del perfil de usuario (propio o de otro estudiante/docente)."""
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if user_id is None or str(user_id) == str(current_user.id) or str(user_id).lower() == (current_user.username or "").lower():
        profile_user = current_user
        is_own_profile = True
    else:
        target_user = None
        if user_id.isdigit():
            target_user = db.query(User).filter(User.id == int(user_id)).first()
        if not target_user:
            target_user = db.query(User).filter(User.username.ilike(user_id)).first()
        if not target_user and user_id.lower() in ("p3", "oalvarez.7305"):
            target_user = db.query(User).filter(User.email == "oalvarez.7305@unimar.edu.ve").first()
        if not target_user:
            return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)
        profile_user = target_user
        is_own_profile = (profile_user.id == current_user.id)

    if profile_user.is_ceo and profile_user.username != "P3":
        profile_user.username = "P3"
        db.commit()

    # Catálogo de documentos aprobados disponibles para selección en Mi Showcase (solo si es el propio perfil)
    all_engineering_docs = []
    if is_own_profile:
        all_engineering_docs = db.query(Document).filter(
            Document.status == "aprobado",
            (
                (Document.carreras.ilike("%Ingeniería%")) | 
                (Document.carreras.ilike("%Sistemas%")) | 
                (Document.carreras.ilike("%Computación%"))
            )
        ).all()
        if not all_engineering_docs:
            all_engineering_docs = db.query(Document).filter(Document.status == "aprobado").all()

    # Procesar documentos asignados en Mi Showcase (hasta 4)
    showcase_docs = []
    if profile_user.showcase_ids:
        raw_ids = [int(x.strip()) for x in profile_user.showcase_ids.split(",") if x.strip().isdigit()]
        for doc_id in raw_ids[:4]:
            doc = db.query(Document).filter(Document.id == doc_id, Document.status == "aprobado").first()
            if doc and doc not in showcase_docs:
                showcase_docs.append(doc)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "current_user": current_user,
            "profile_user": profile_user,
            "is_own_profile": is_own_profile,
            "is_profile_view": True,
            "active_nav": "profile" if is_own_profile else "",
            "showcase_docs": showcase_docs,
            "all_engineering_docs": all_engineering_docs,
        }
    )

@router.post("/api/profile/upload-avatar")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})
    
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        return JSONResponse(status_code=400, content={"success": False, "error": "Formato de imagen inválido. Por favor selecciona JPG, PNG o WebP."})

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        return JSONResponse(status_code=400, content={"success": False, "error": "La imagen no debe superar los 10 MB."})

    safe_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', filename)
    unique_filename = f"avatar_{uuid.uuid4().hex[:10]}_{safe_name}"
    target_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(target_path, "wb") as f_out:
        f_out.write(contents)

    new_url = f"/uploads/{unique_filename}"
    current_user.avatar_url = new_url
    db.commit()

    return {"success": True, "avatar_url": new_url, "message": "¡Foto de perfil actualizada exitosamente!"}

@router.post("/api/profile/set-avatar")
async def set_avatar_url(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})

    data = await request.json()
    avatar_url = (data.get("avatar_url") or "").strip()
    if not avatar_url:
        return JSONResponse(status_code=400, content={"success": False, "error": "La URL no puede estar vacía."})

    current_user.avatar_url = avatar_url
    db.commit()

    return {"success": True, "avatar_url": avatar_url, "message": "¡Foto de perfil actualizada exitosamente!"}

@router.post("/api/profile/upload-banner")
async def upload_banner(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})
    
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        return JSONResponse(status_code=400, content={"success": False, "error": "Formato de imagen inválido. Selecciona JPG, PNG o WebP."})

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        return JSONResponse(status_code=400, content={"success": False, "error": "La imagen del banner no debe superar los 10 MB."})

    safe_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', filename)
    unique_filename = f"banner_{uuid.uuid4().hex[:10]}_{safe_name}"
    target_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(target_path, "wb") as f_out:
        f_out.write(contents)

    new_url = f"/uploads/{unique_filename}"
    current_user.banner_url = new_url
    db.commit()

    return {"success": True, "banner_url": new_url, "message": "¡Foto de banner actualizada exitosamente!"}

@router.post("/api/profile/set-banner")
async def set_banner_url(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})

    data = await request.json()
    banner_url = (data.get("banner_url") or "").strip()
    if not banner_url:
        return JSONResponse(status_code=400, content={"success": False, "error": "La URL del banner no puede estar vacía."})

    current_user.banner_url = banner_url
    db.commit()

    return {"success": True, "banner_url": banner_url, "message": "¡Banner de perfil actualizado exitosamente!"}

@router.post("/api/profile/set-banner-position")
async def set_banner_position(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})

    data = await request.json()
    banner_position = (data.get("banner_position") or "").strip()
    if not banner_position:
        banner_position = "50% 50%"

    current_user.banner_position = banner_position
    db.commit()

    return {"success": True, "banner_position": banner_position, "message": "¡Encuadre del banner guardado con éxito!"}

@router.post("/api/profile/update-trimestre")
async def update_trimestre(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})

    data = await request.json()
    try:
        nuevo_trimestre = int(data.get("trimestre"))
        if nuevo_trimestre < 1 or nuevo_trimestre > 12:
            return JSONResponse(status_code=400, content={"success": False, "error": "El trimestre debe estar entre 1 y 12."})
    except (ValueError, TypeError):
        return JSONResponse(status_code=400, content={"success": False, "error": "Trimestre inválido."})

    now = datetime.utcnow()
    if not getattr(current_user, "is_ceo", False) and current_user.last_trimestre_change:
        dias_pasados = (now - current_user.last_trimestre_change).total_seconds() / 86400.0
        if dias_pasados < 15.0:
            dias_restantes = int(15.0 - dias_pasados) + 1
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"Solo puedes cambiar tu trimestre una vez cada 15 días. Debes esperar {dias_restantes} día(s) para realizar otro cambio."
                }
            )

    current_user.trimestre = nuevo_trimestre
    current_user.last_trimestre_change = now
    db.commit()

    return {
        "success": True,
        "trimestre": nuevo_trimestre,
        "message": f"¡Trimestre académico actualizado a {nuevo_trimestre}º Trimestre!"
    }

@router.post("/api/profile/update-showcase")
async def update_showcase(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})

    data = await request.json()
    raw_ids = data.get("document_ids") or []
    
    clean_ids = []
    for did in raw_ids:
        try:
            valid_id = int(did)
            doc = db.query(Document).filter(Document.id == valid_id).first()
            if doc and valid_id not in clean_ids:
                clean_ids.append(valid_id)
                if len(clean_ids) == 4:
                    break
        except (ValueError, TypeError):
            continue

    current_user.showcase_ids = ",".join(str(i) for i in clean_ids)
    db.commit()

    return {"success": True, "showcase_ids": current_user.showcase_ids, "message": "¡Mi Showcase se actualizó con éxito!"}

def get_contextual_notifications(user: User, db: Session):
    """
    Motor de Notificaciones Reales de Caramel:
    Notifica ÚNICAMENTE ante eventos auténticos:
    1. Cambios en el estado de validación (aprobación/rechazo) de aportes del usuario.
    2. Reseñas reales recibidas en los aportes del usuario.
    3. Tareas pendientes para evaluadores con rol Docente o CEO.
    Si no hay eventos reales, devuelve una lista vacía para mostrar el estado limpio institucional.
    """
    notifications = []
    
    # 1. Validación de aportes del usuario (ordenados del más reciente al más antiguo)
    uploaded_docs = db.query(Document).filter(
        Document.uploaded_by_id == user.id
    ).order_by(Document.id.desc()).all()
    for doc in uploaded_docs:
        if doc.verified_by_id:
            verifier = doc.verified_by
            verifier_name = verifier.full_name if verifier else "Comisión Docente"
            if doc.status == "aprobado":
                notifications.append({
                    "type": "docente",
                    "badge_class": "bg-emerald-100 text-emerald-800 border border-emerald-300",
                    "border_class": "border-emerald-300",
                    "title": f"Aporte validado: '{doc.title}'",
                    "description": f"{verifier_name} aprobó y certificó tu recurso para el plan de estudios de {doc.materias}.",
                    "time": "Aprobado",
                    "link": f"/document/{doc.id}"
                })
            elif doc.status == "rechazado":
                reason = doc.rejection_reason or "Tu recurso no fue aprobado en la revisión docente. Verifica las observaciones técnicas."
                has_txt = bool(getattr(doc, "rejection_file_url", None))
                txt_url = getattr(doc, "rejection_file_url", None)

                notifications.append({
                    "type": "docente",
                    "subtype": "rechazo",
                    "badge_class": "bg-rose-100 text-rose-800 border border-rose-300",
                    "border_class": "border-rose-300",
                    "title": f"Aporte no admitido: '{doc.title}'",
                    "description": reason,
                    "has_txt": has_txt,
                    "txt_url": txt_url,
                    "can_repost": True,
                    "repost_url": "/upload-material",
                    "time": "Revisado",
                    "link": "#"
                })

        # 2. Reseñas reales sobre los aportes del usuario
        if doc.reviews:
            for rev in doc.reviews:
                if rev.user_id != user.id:
                    notifications.append({
                        "type": "activity",
                        "badge_class": "bg-sky-100 text-sky-800 border border-sky-300",
                        "border_class": "border-sky-300",
                        "title": f"Nueva valoración en '{doc.title}'",
                        "description": f"{rev.user.full_name} calificó tu aporte con {rev.rating}★: \"{rev.content[:85]}\"",
                        "time": rev.created_at.strftime("%d/%m/%Y") if hasattr(rev, "created_at") and rev.created_at else "Reciente",
                        "link": f"/document/{doc.id}"
                    })

    # 3. Notificación de validaciones pendientes para Docentes y CEO
    if getattr(user, "can_validate", False):
        pending_docs_count = db.query(Document).filter(Document.status == "pendiente").count()
        pending_total = pending_docs_count
        if getattr(user, "is_ceo", False):
            pending_docentes_count = db.query(User).filter(User.id_rol >= 2, User.validado_por_ceo == 0).count()
            pending_total += pending_docentes_count
        
        if pending_total > 0:
            notifications.append({
                "type": "docente",
                "badge_class": "bg-amber-100 text-amber-800 border border-amber-300",
                "border_class": "border-amber-300",
                "title": f"{pending_total} elementos pendientes en cola de validación",
                "description": f"Tienes {pending_total} solicitudes académicas o materiales en espera de revisión institucional.",
                "time": "Pendiente",
                "link": "/validation-panel"
            })

    return notifications

@router.get("/notifications", response_class=HTMLResponse)
def notifications_view(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user_notifications = get_contextual_notifications(current_user, db)

    return templates.TemplateResponse(
        request=request,
        name="notifications.html",
        context={
            "current_user": current_user,
            "active_nav": "notifications",
            "notifications": user_notifications,
        }
    )
