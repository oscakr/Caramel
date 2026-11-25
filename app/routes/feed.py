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
from ..models import User, Document, CuratedList, Review, ReviewLike, Friendship, Bookmark, PasswordResetToken, PasswordResetRequest
from ..recommender import AcademicRecommender
from ..storage import UPLOAD_DIR, upload_bytes, delete_uploaded_url, extract_managed_rel_path
from ..time_utils import format_vet
from .auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["vet"] = format_vet

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
    recommendations = recommender.get_recommendations(current_user.id, limit=12)

    # 5. Pending materials (para este validador), teacher validations and CEO support requests count
    pending_validation_count = 0
    if current_user.can_validate:
        from .documents import get_pending_docs_for_validator
        pending_validation_count = len(get_pending_docs_for_validator(db, current_user.id))
        if current_user.is_ceo:
            pending_docentes_count = db.query(User).filter(User.id_rol >= 2, User.validado_por_ceo == 0).count()
            pending_validation_count += pending_docentes_count
            try:
                pending_reset_reqs = db.query(PasswordResetRequest).filter(PasswordResetRequest.status == "pendiente").count()
                pending_validation_count += pending_reset_reqs
            except Exception:
                db.rollback()

    # Check which reviews the user has liked ("Me Sirve")
    try:
        liked_review_ids = set(
            r[0] for r in db.query(ReviewLike.review_id).filter(
                ReviewLike.user_id == current_user.id
            ).all()
        )
    except Exception:
        db.rollback()
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

    query_builder = db.query(Document).filter(Document.status.in_(["aprobado", "en_revision"]))

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

    # Acceso estrictamente reservado para rango CEO (RBAC)
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
        if not target_user:
            return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)
        profile_user = target_user
        is_own_profile = (profile_user.id == current_user.id)

    # Catálogo de documentos aprobados disponibles para selección en Mi Showcase (solo si es el propio perfil)
    all_engineering_docs = []
    if is_own_profile:
        all_engineering_docs = db.query(Document).filter(
            Document.status.in_(["aprobado", "en_revision"]),
            (
                (Document.carreras.ilike("%Ingeniería%")) | 
                (Document.carreras.ilike("%Sistemas%")) | 
                (Document.carreras.ilike("%Computación%"))
            )
        ).all()
        if not all_engineering_docs:
            all_engineering_docs = db.query(Document).filter(Document.status.in_(["aprobado", "en_revision"])).all()

    # Procesar documentos asignados en Mi Showcase (hasta 4)
    showcase_docs = []
    if profile_user.showcase_ids:
        raw_ids = [int(x.strip()) for x in profile_user.showcase_ids.split(",") if x.strip().isdigit()]
        for doc_id in raw_ids[:4]:
            doc = db.query(Document).filter(Document.id == doc_id, Document.status.in_(["aprobado", "en_revision"])).first()
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

def _cleanup_old_profile_upload(old_url: str, db: Session, column_attr, exclude_user_id: int):
    """Elimina el archivo anterior (en Supabase Storage o /uploads/) al cambiar avatar o banner si ningún otro usuario lo usa."""
    rel = extract_managed_rel_path(old_url)
    if not rel or "/" in rel or "\\" in rel:
        return
    if not (rel.startswith("avatar_") or rel.startswith("banner_")):
        return
    still_used = db.query(User).filter(
        column_attr == old_url,
        User.id != exclude_user_id
    ).first()
    if not still_used:
        delete_uploaded_url(old_url)


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

    old_avatar_url = current_user.avatar_url
    safe_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', filename)
    unique_filename = f"avatar_{uuid.uuid4().hex[:10]}_{safe_name}"
    new_url = upload_bytes(unique_filename, contents, content_type=file.content_type)

    current_user.avatar_url = new_url
    db.commit()
    _cleanup_old_profile_upload(old_avatar_url, db, User.avatar_url, current_user.id)

    return {"success": True, "avatar_url": new_url, "message": "¡Foto de perfil actualizada exitosamente!"}

@router.post("/api/profile/set-avatar")
async def set_avatar_url(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})

    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"success": False, "error": "Solicitud JSON inválida."})
    avatar_url = (data.get("avatar_url") or "").strip()
    if not avatar_url:
        return JSONResponse(status_code=400, content={"success": False, "error": "La URL no puede estar vacía."})

    old_avatar_url = current_user.avatar_url
    current_user.avatar_url = avatar_url
    db.commit()
    if old_avatar_url != avatar_url:
        _cleanup_old_profile_upload(old_avatar_url, db, User.avatar_url, current_user.id)

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

    old_banner_url = current_user.banner_url
    safe_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', filename)
    unique_filename = f"banner_{uuid.uuid4().hex[:10]}_{safe_name}"
    new_url = upload_bytes(unique_filename, contents, content_type=file.content_type)

    current_user.banner_url = new_url
    db.commit()
    _cleanup_old_profile_upload(old_banner_url, db, User.banner_url, current_user.id)

    return {"success": True, "banner_url": new_url, "message": "¡Foto de banner actualizada exitosamente!"}

@router.post("/api/profile/set-banner")
async def set_banner_url(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})

    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"success": False, "error": "Solicitud JSON inválida."})
    banner_url = (data.get("banner_url") or "").strip()
    if not banner_url:
        return JSONResponse(status_code=400, content={"success": False, "error": "La URL del banner no puede estar vacía."})

    old_banner_url = current_user.banner_url
    current_user.banner_url = banner_url
    db.commit()
    if old_banner_url != banner_url:
        _cleanup_old_profile_upload(old_banner_url, db, User.banner_url, current_user.id)

    return {"success": True, "banner_url": banner_url, "message": "¡Banner de perfil actualizado exitosamente!"}

@router.post("/api/profile/set-banner-position")
async def set_banner_position(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})

    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"success": False, "error": "Solicitud JSON inválida."})
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

    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"success": False, "error": "Solicitud JSON inválida."})
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

@router.post("/api/profile/showcase")
@router.post("/api/profile/update-showcase")
async def update_showcase(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "error": "No autenticado"})

    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"success": False, "error": "Solicitud JSON inválida."})
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
    - Orden cronológico estricto (lo más reciente SIEMPRE en el tope).
    - Auto-archivo a los 15 días para avisos informativos + respeto a limpieza manual (`notifications_cleared_at`).
    - Las tareas pendientes activas (validaciones y soporte CEO) siempre se mantienen visibles hasta ser atendidas.
    """
    notifications = []
    now = datetime.utcnow()
    auto_expire_cutoff = now - timedelta(days=15)
    cleared_at = getattr(user, "notifications_cleared_at", None)
    info_cutoff = max(auto_expire_cutoff, cleared_at) if cleared_at else auto_expire_cutoff

    def _is_info_visible(event_dt: datetime | None) -> bool:
        if event_dt is None:
            # Registros históricos sin timestamp: se ocultan si el usuario ya limpió su bandeja
            return cleared_at is None
        return event_dt >= info_cutoff

    # 0. Avisos de seguridad al propio usuario cuando su contraseña (y/o correo) fue restablecida
    try:
        from .auth import _ensure_reset_tokens_table
        _ensure_reset_tokens_table()
        completed_resets = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == 1,
            PasswordResetToken.used_at.isnot(None),
        ).order_by(PasswordResetToken.used_at.desc()).limit(5).all()
        for tok in completed_resets:
            if not _is_info_visible(tok.used_at):
                continue
            when_str = format_vet(tok.used_at, "%d/%m/%Y %H:%M")
            if getattr(tok, "email_changed", 0) == 1:
                notifications.append({
                    "notif_id": f"reset_tok_{tok.id}_email",
                    "_sort_ts": tok.used_at,
                    "is_pending_task": False,
                    "type": "docente",
                    "badge_class": "bg-emerald-100 text-emerald-800 border border-emerald-300",
                    "border_class": "border-emerald-300",
                    "title": "Contraseña y correo institucional restablecidos",
                    "description": f"Tu contraseña y tu correo institucional ({user.email}) fueron actualizados correctamente. Si no reconoces este cambio, contacta de inmediato a soporte.",
                    "time": when_str,
                    "link": "/profile"
                })
            else:
                notifications.append({
                    "notif_id": f"reset_tok_{tok.id}_pwd",
                    "_sort_ts": tok.used_at,
                    "is_pending_task": False,
                    "type": "docente",
                    "badge_class": "bg-emerald-100 text-emerald-800 border border-emerald-300",
                    "border_class": "border-emerald-300",
                    "title": "Contraseña restablecida con éxito",
                    "description": "Tu contraseña de acceso a Caramel UNIMAR fue actualizada correctamente. Si no reconoces este cambio, contacta de inmediato a soporte.",
                    "time": when_str,
                    "link": "/profile"
                })
    except Exception:
        db.rollback()

    # 1. Validación de aportes del usuario y reseñas reales recibidas
    uploaded_docs = db.query(Document).filter(
        Document.uploaded_by_id == user.id
    ).order_by(Document.id.desc()).all()
    for doc in uploaded_docs:
        if doc.verified_by_id:
            ver_dt = getattr(doc, "verified_at", None)
            if _is_info_visible(ver_dt):
                verifier = doc.verified_by
                verifier_name = verifier.full_name if verifier else "Comisión Docente"
                # Fallback determinista para documentos validados antes de existir verified_at
                sort_ts = ver_dt if ver_dt else datetime(2000, 1, 1) + timedelta(seconds=doc.id)
                time_label = format_vet(ver_dt, "%d/%m %H:%M", fallback=("Aprobado" if doc.status == "aprobado" else "Revisado"))
                if doc.status == "aprobado":
                    notifications.append({
                        "notif_id": f"doc_ok_{doc.id}_{int(sort_ts.timestamp())}",
                        "_sort_ts": sort_ts,
                        "is_pending_task": False,
                        "type": "docente",
                        "badge_class": "bg-emerald-100 text-emerald-800 border border-emerald-300",
                        "border_class": "border-emerald-300",
                        "title": f"Aporte validado: '{doc.title}'",
                        "description": f"{verifier_name} aprobó y certificó tu recurso para el plan de estudios de {doc.materias}.",
                        "time": time_label,
                        "link": f"/document/{doc.id}"
                    })
                elif doc.status == "rechazado":
                    reason = doc.rejection_reason or "Tu recurso no fue aprobado en la revisión docente. Verifica las observaciones técnicas."
                    has_txt = bool(getattr(doc, "rejection_file_url", None))
                    txt_url = getattr(doc, "rejection_file_url", None)

                    notifications.append({
                        "notif_id": f"doc_rej_{doc.id}_{int(sort_ts.timestamp())}",
                        "_sort_ts": sort_ts,
                        "is_pending_task": False,
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
                        "time": time_label,
                        "link": "#"
                    })

        # 2. Reseñas reales sobre los aportes del usuario
        if doc.reviews:
            for rev in doc.reviews:
                if rev.user_id != user.id:
                    rev_dt = getattr(rev, "created_at", None)
                    if not _is_info_visible(rev_dt):
                        continue
                    sort_ts = rev_dt if rev_dt else datetime(2000, 1, 1) + timedelta(seconds=rev.id)
                    reviewer_name = rev.user.full_name if rev.user else "Estudiante"
                    review_snippet = (rev.content or "")[:85]
                    notifications.append({
                        "notif_id": f"rev_{rev.id}",
                        "_sort_ts": sort_ts,
                        "is_pending_task": False,
                        "type": "activity",
                        "badge_class": "bg-sky-100 text-sky-800 border border-sky-300",
                        "border_class": "border-sky-300",
                        "title": f"Nueva valoración en '{doc.title}'",
                        "description": f"{reviewer_name} calificó tu aporte con {rev.rating}★: \"{review_snippet}\"",
                        "time": format_vet(rev_dt, "%d/%m %H:%M"),
                        "link": f"/document/{doc.id}"
                    })

    # 3. Notificación de validaciones pendientes para Docentes y CEO (no expiran hasta atenderse)
    if getattr(user, "can_validate", False):
        from .documents import get_pending_docs_for_validator
        pending_docs = get_pending_docs_for_validator(db, user.id)
        pending_total = len(pending_docs)
        desempate_count = sum(1 for d in pending_docs if d.status == "en_revision" or getattr(d, "consensus_state", None) == "en_revision")
        latest_pending_ts = now - timedelta(seconds=1) if pending_docs else datetime(2000, 1, 1)
        if getattr(user, "is_ceo", False):
            pending_docentes = db.query(User).filter(User.id_rol >= 2, User.validado_por_ceo == 0).order_by(User.created_at.desc()).all()
            pending_total += len(pending_docentes)
            if pending_docentes and pending_docentes[0].created_at:
                latest_pending_ts = max(latest_pending_ts, pending_docentes[0].created_at)

        if pending_total > 0:
            latest_doc_id = pending_docs[0].id if pending_docs else 0
            title_pending = (
                f"{pending_total} pendientes en validación ({desempate_count} desempate{'s' if desempate_count != 1 else ''})"
                if desempate_count > 0
                else f"{pending_total} elementos pendientes en cola de validación"
            )
            notifications.append({
                "notif_id": f"pending_queue_{pending_total}_{desempate_count}_{latest_doc_id}",
                "_sort_ts": latest_pending_ts,
                "is_pending_task": True,
                "type": "docente",
                "badge_class": "bg-amber-100 text-amber-800 border border-amber-300",
                "border_class": "border-amber-300",
                "title": title_pending,
                "description": f"Tienes {pending_total} solicitudes académicas o materiales en espera de tu dictamen institucional.",
                "time": "Pendiente",
                "link": "/validation-panel"
            })

    # 4. Solicitudes de soporte de restablecimiento de acceso (exclusivo para el CEO, no expiran hasta atenderse)
    if getattr(user, "is_ceo", False):
        try:
            reset_reqs = db.query(PasswordResetRequest).filter(
                PasswordResetRequest.status == "pendiente"
            ).order_by(PasswordResetRequest.created_at.desc()).limit(10).all()
            for req in reset_reqs:
                if req.matched_user:
                    who = f"{req.matched_user.full_name} ({req.matched_user.email})"
                else:
                    who = req.identifier
                req_ts = req.created_at or now
                notifications.append({
                    "notif_id": f"reset_req_{req.id}",
                    "_sort_ts": req_ts,
                    "is_pending_task": True,
                    "type": "docente",
                    "badge_class": "bg-caramel-100 text-caramel-800 border border-caramel-300",
                    "border_class": "border-caramel-300",
                    "title": f"Solicitud de restablecimiento de contraseña — {who}",
                    "description": "Este usuario pulsó 'Contacta al soporte' desde el inicio de sesión. Entra para generarle su enlace de sustitución de contraseña.",
                    "time": format_vet(req.created_at, "%d/%m %H:%M"),
                    "link": "/validation-panel"
                })
        except Exception:
            db.rollback()

    # Ordenar estrictamente de la más reciente a la más antigua
    notifications.sort(key=lambda item: item.get("_sort_ts") or datetime(2000, 1, 1), reverse=True)
    return notifications


@router.post("/notifications/clear")
def clear_user_notifications(request: Request, db: Session = Depends(get_db)):
    """Limpia los avisos informativos ya leídos del usuario (las tareas pendientes siguen activas)."""
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    current_user.notifications_cleared_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(url="/notifications", status_code=status.HTTP_303_SEE_OTHER)

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
