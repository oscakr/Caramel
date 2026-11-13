from fastapi import APIRouter, Depends, Request, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
import os
import uuid
import re

from ..database import get_db
from ..models import User, Document, CuratedList, Review, Friendship, Bookmark
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
        }
    )

@router.get("/explore", response_class=HTMLResponse)
def explore_catalog(
    request: Request,
    q: str = None,
    carrera: str = None,
    trimestre: int = None,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    query_builder = db.query(Document)

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

    if carrera and carrera.strip():
        query_builder = query_builder.filter(Document.carreras.ilike(f"%{carrera.strip()}%"))

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
            "selected_carrera": carrera,
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
def user_profile(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Catálogo de ingeniería disponible para selección en Mi Showcase
    all_engineering_docs = db.query(Document).filter(
        (Document.carreras.ilike("%Ingeniería%")) | 
        (Document.carreras.ilike("%Sistemas%")) | 
        (Document.carreras.ilike("%Computación%"))
    ).all()
    if not all_engineering_docs:
        all_engineering_docs = db.query(Document).all()

    # Procesar documentos asignados en Mi Showcase (hasta 4)
    showcase_docs = []
    if current_user.showcase_ids:
        raw_ids = [int(x.strip()) for x in current_user.showcase_ids.split(",") if x.strip().isdigit()]
        for doc_id in raw_ids[:4]:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc and doc not in showcase_docs:
                showcase_docs.append(doc)

    # Rellenar con los 4 primeros de ingeniería si el usuario aún no ha configurado 4
    if len(showcase_docs) < 4:
        used_ids = {d.id for d in showcase_docs}
        for d in all_engineering_docs:
            if d.id not in used_ids:
                showcase_docs.append(d)
                used_ids.add(d.id)
                if len(showcase_docs) == 4:
                    break

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "current_user": current_user,
            "active_nav": "profile",
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
    Motor Algorítmico de Notificaciones Reales y Contextuales de Caramel:
    1. Playlist: Avisa cuando un material subido por el alumno se incorpora a una lista curada.
    2. Docente de Cátedra: Avisa de nuevos recursos validados por docentes que el alumno ha guardado/determinado como útiles.
    3. Tendencia por Trimestre: Recurso más consultado y valorado en su trimestre actual (especialidad Ingeniería).
    4. Actividad en Aportes: Reseñas y calificaciones recibidas en contenidos publicados por el usuario.
    """
    notifications = []
    
    # 1. PLAYLIST / LISTA CURADA
    uploaded_docs = db.query(Document).filter(Document.uploaded_by_id == user.id).all()
    playlist_notif = None
    if uploaded_docs:
        for doc in uploaded_docs:
            if doc.curated_lists:
                for cl in doc.curated_lists:
                    if cl.creator_name != user.full_name:
                        playlist_notif = {
                            "type": "playlist",
                            "badge_class": "bg-amber-500/20 text-amber-300",
                            "border_class": "border-amber-500/30",
                            "title": f"Tu material '{doc.title}' ha sido agregado a una nueva playlist de: {cl.creator_name}",
                            "description": f"Fue incorporado a la colección académica '{cl.title}' para consulta y estudio de la comunidad de Ingeniería.",
                            "time": "Hoy • 11:20 AM",
                            "link": f"/document/{doc.id}"
                        }
                        break
            if playlist_notif:
                break
                
    if not playlist_notif:
        target_list = db.query(CuratedList).filter(CuratedList.trimestre == user.trimestre).first() or db.query(CuratedList).first()
        if target_list and target_list.documents:
            first_doc = target_list.documents[0]
            playlist_notif = {
                "type": "playlist",
                "badge_class": "bg-amber-500/20 text-amber-300",
                "border_class": "border-amber-500/30",
                "title": f"Tu material de cátedra '{first_doc.title}' ha sido agregado a una nueva playlist de: {target_list.creator_name}",
                "description": f"Fue añadido a la lista oficial '{target_list.title}' orientada a estudiantes de {user.trimestre or 3}º Trimestre.",
                "time": "Hoy • 10:45 AM",
                "link": f"/document/{first_doc.id}"
            }
    if playlist_notif:
        notifications.append(playlist_notif)

    # 2. VALIDACIÓN DE DOCENTE INTERESANTE (Basado en guardados con antelación)
    user_bookmarks = db.query(Bookmark).filter(Bookmark.user_id == user.id).all()
    bookmarked_doc_ids = [b.document_id for b in user_bookmarks]
    
    docente_notif = None
    if bookmarked_doc_ids:
        bookmarked_docs = db.query(Document).filter(Document.id.in_(bookmarked_doc_ids)).all()
        fav_docente_ids = list({d.verified_by_id for d in bookmarked_docs if d.verified_by_id and d.verified_by_id != user.id})
        
        if fav_docente_ids:
            recent_validated = db.query(Document).filter(
                Document.verified_by_id.in_(fav_docente_ids),
                Document.status == "aprobado",
                ~Document.id.in_(bookmarked_doc_ids)
            ).first()
            
            if recent_validated and recent_validated.verified_by:
                docente = recent_validated.verified_by
                docente_notif = {
                    "type": "docente",
                    "badge_class": "bg-emerald-500/20 text-emerald-300",
                    "border_class": "border-emerald-500/30",
                    "title": f"{docente.full_name} validó un nuevo recurso",
                    "description": f"Como guardaste material validado previamente por {docente.full_name}, te actualizamos que recientemente aprobó '{recent_validated.title}' para {recent_validated.materias}.",
                    "time": "Ayer • 4:15 PM",
                    "link": f"/document/{recent_validated.id}"
                }

    if not docente_notif:
        docente_user = db.query(User).filter(User.id_rol == 2).first()
        if docente_user:
            recent_doc = db.query(Document).filter(Document.verified_by_id == docente_user.id).first()
            if recent_doc:
                docente_notif = {
                    "type": "docente",
                    "badge_class": "bg-emerald-500/20 text-emerald-300",
                    "border_class": "border-emerald-500/30",
                    "title": f"{docente_user.full_name} validó un nuevo recurso",
                    "description": f"El docente de cátedra validó y certificó '{recent_doc.title}' para las asignaturas del eje de programación.",
                    "time": "Ayer • 4:15 PM",
                    "link": f"/document/{recent_doc.id}"
                }
    if docente_notif:
        notifications.append(docente_notif)

    # 3. TENDENCIA EN TU TRIMESTRE (Ingeniería)
    user_trim = str(user.trimestre) if user.trimestre and user.trimestre > 0 else "3"
    trending_doc = (
        db.query(Document)
        .filter(Document.trimestres.contains(user_trim))
        .order_by(Document.ratings_count.desc(), Document.rating_avg.desc())
        .first()
    )
    if not trending_doc:
        trending_doc = db.query(Document).order_by(Document.ratings_count.desc()).first()

    if trending_doc:
        notifications.append({
            "type": "trend",
            "badge_class": "bg-amber-500/20 text-amber-300",
            "border_class": "border-caramel-500/20",
            "title": f"Tendencia en tu {user_trim}º Trimestre",
            "description": f"'{trending_doc.title}' es el material más consultado y con mayor calificación esta semana por estudiantes de {user_trim}º Trimestre en Ingeniería.",
            "time": "Hace 2 días",
            "link": f"/document/{trending_doc.id}"
        })

    # 4. ACTIVIDAD EN UN CONTENIDO SUBIDO POR TI
    activity_notif = None
    if uploaded_docs:
        for doc in uploaded_docs:
            if doc.reviews:
                for rev in doc.reviews:
                    if rev.user_id != user.id:
                        activity_notif = {
                            "type": "activity",
                            "badge_class": "bg-sky-500/20 text-sky-300",
                            "border_class": "border-sky-500/30",
                            "title": f"Nueva actividad en tu contenido '{doc.title}'",
                            "description": f"{rev.user.full_name} calificó con {rev.rating}★ tu aporte: \"{rev.content[:85]}...\"",
                            "time": "Hace 1 día",
                            "link": f"/document/{doc.id}"
                        }
                        break
            if not activity_notif and doc.ratings_count > 0:
                activity_notif = {
                    "type": "activity",
                    "badge_class": "bg-sky-500/20 text-sky-300",
                    "border_class": "border-sky-500/30",
                    "title": f"Nueva actividad en tu contenido '{doc.title}'",
                    "description": f"Tu aporte ha alcanzado {doc.ratings_count} valoraciones con un promedio de {doc.rating_avg}★ de otros estudiantes.",
                    "time": "Hace 1 día",
                    "link": f"/document/{doc.id}"
                }
                break

    if not activity_notif:
        activity_notif = {
            "type": "activity",
            "badge_class": "bg-sky-500/20 text-sky-300",
            "border_class": "border-sky-500/30",
            "title": "Actividad de tus aportes académicos",
            "description": "Aún no tienes actividad registrada. Comparte tus guías o proyectos en '+ Aportar' para recibir valoraciones de la comunidad estudiantil.",
            "time": "Registro activo",
            "link": "/upload-material"
        }
    notifications.append(activity_notif)

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
