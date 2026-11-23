import os
import re
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db, engine, Base
from ..models import User, Document, Review, ReviewLike, Bookmark, UserInteraction, Catedra
from ..catedras_config import get_catedra_banner
from .auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB

def extract_youtube_id(url: str | None) -> str | None:
    if not url:
        return None
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?(?:.*&)?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_embed_url(url: str | None) -> str | None:
    yt_id = extract_youtube_id(url)
    if yt_id:
        return f"https://www.youtube-nocookie.com/embed/{yt_id}"
    return None

@router.get("/document/{doc_id}", response_class=HTMLResponse)
def document_detail(doc_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento académico no encontrado")

    # Record view interaction to enrich content-based recommendation model
    db.add(UserInteraction(
        user_id=current_user.id,
        document_id=doc.id,
        interaction_type="view",
        weight=0.5
    ))
    db.commit()

    # Check if bookmarked
    is_bookmarked = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.document_id == doc.id
    ).first() is not None

    # Check which reviews the current user has liked ("Me Sirve")
    try:
        Base.metadata.create_all(bind=engine, tables=[ReviewLike.__table__])
        liked_review_ids = set(
            r[0] for r in db.query(ReviewLike.review_id).filter(
                ReviewLike.user_id == current_user.id
            ).all()
        )
    except Exception:
        liked_review_ids = set()

    youtube_embed_url = get_youtube_embed_url(doc.external_url)

    return templates.TemplateResponse(
        request=request,
        name="document_detail.html",
        context={
            "current_user": current_user,
            "document": doc,
            "banner_url": doc.effective_banner_url,
            "is_bookmarked": is_bookmarked,
            "liked_review_ids": liked_review_ids,
            "youtube_embed_url": youtube_embed_url,
            "active_nav": "feed"
        }
    )

@router.post("/document/{doc_id}/review")
def add_review(
    doc_id: int,
    request: Request,
    rating: int = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    rating = max(1, min(5, rating))

    # Actualizar reseña existente o crear una nueva para evitar votos duplicados del mismo usuario
    existing_review = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.document_id == doc.id
    ).first()

    if existing_review:
        existing_review.rating = rating
        existing_review.content = content.strip()
    else:
        new_review = Review(
            user_id=current_user.id,
            document_id=doc.id,
            rating=rating,
            content=content.strip(),
            likes_count=0
        )
        db.add(new_review)

    # Actualizar o registrar la interacción en el historial del recomendador
    existing_inter = db.query(UserInteraction).filter(
        UserInteraction.user_id == current_user.id,
        UserInteraction.document_id == doc.id,
        UserInteraction.interaction_type == "rate"
    ).first()

    if existing_inter:
        existing_inter.weight = float(rating) / 2.0
    else:
        db.add(UserInteraction(
            user_id=current_user.id,
            document_id=doc.id,
            interaction_type="rate",
            weight=float(rating) / 2.0
        ))

    db.commit()

    # Recalcular promedio exacto y desglose de estrellas en el documento
    doc.update_rating_stats()
    db.commit()

    return RedirectResponse(url=f"/document/{doc.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/review/{review_id}/like")
def toggle_review_like(review_id: int, request: Request, db: Session = Depends(get_db)):
    """Toggle Me Sirve: 1 like por usuario. Clic = agrega like; segundo clic = remueve like."""
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        Base.metadata.create_all(bind=engine, tables=[ReviewLike.__table__])
    except Exception:
        pass

    rev = db.query(Review).filter(Review.id == review_id).first()
    if not rev:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    existing_like = db.query(ReviewLike).filter(
        ReviewLike.review_id == review_id,
        ReviewLike.user_id == current_user.id
    ).first()

    if existing_like:
        # Toggle OFF: Segundo clic remueve el like
        db.delete(existing_like)
        db.commit()
    else:
        # Toggle ON: Primer clic agrega el like
        new_like = ReviewLike(user_id=current_user.id, review_id=review_id)
        db.add(new_like)
        db.commit()

    # Sincronizar conteo exacto de likes
    rev.likes_count = db.query(ReviewLike).filter(ReviewLike.review_id == review_id).count()
    db.commit()

    target_url = request.headers.get("referer") or f"/document/{rev.document_id}"
    return RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)

@router.post("/document/{doc_id}/bookmark")
def toggle_bookmark(doc_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    existing = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.document_id == doc_id
    ).first()

    if existing:
        db.delete(existing)
    else:
        db.add(Bookmark(user_id=current_user.id, document_id=doc_id))
        db.add(UserInteraction(
            user_id=current_user.id,
            document_id=doc_id,
            interaction_type="save",
            weight=2.0
        ))

    db.commit()
    target_url = request.headers.get("referer", f"/document/{doc_id}")
    return RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)

@router.post("/api/check-youtube-duplicate")
async def check_youtube_duplicate(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        url = body.get("url", "").strip()
    except Exception:
        url = ""

    yt_id = extract_youtube_id(url)
    if not yt_id:
        return {"valid": False, "duplicate": False, "message": "Enlace no válido"}

    matching_docs = db.query(Document).filter(
        (Document.external_url.like(f"%{yt_id}%")) | 
        (Document.read_url.like(f"%{yt_id}%"))
    ).all()

    already_approved = any(d.status == "aprobado" for d in matching_docs)
    rejected_count = sum(1 for d in matching_docs if d.status == "rechazado")

    if already_approved or rejected_count >= 3:
        return {
            "valid": True,
            "duplicate": True,
            "rejected_count": rejected_count,
            "message": "¡El video que intentas aprobar ya fue validado anteriormente, más atento Casi Ingeniero!"
        }

    return {"valid": True, "duplicate": False, "rejected_count": rejected_count}

@router.get("/upload-material", response_class=HTMLResponse)
def upload_material_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    catedras = db.query(Catedra).order_by(Catedra.trimestre, Catedra.nombre_catedra).all()

    return templates.TemplateResponse(
        request=request,
        name="upload_material.html",
        context={"current_user": current_user, "active_nav": "explore", "catedras": catedras, "success": False}
    )

@router.post("/upload-material")
async def upload_material_submit(
    request: Request,
    title: str = Form(None),
    authors: str = Form(None),
    materias: str = Form(None),
    trimestres: int = Form(1),
    material_type: str = Form("pdf"),
    external_url: str = Form(None),
    description: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    is_ajax = "application/json" in request.headers.get("accept", "") or request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not current_user:
        if is_ajax:
            return JSONResponse(status_code=401, content={"success": False, "error": "Sesión expirada o no autenticada"})
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    materias_clean = (materias or "").strip()
    if not materias_clean:
        materias_clean = "Programación IV"

    # Procesamiento inteligente y distintivo del título del material
    raw_title = (title or "").strip()
    if raw_title and raw_title.lower() != materias_clean.lower():
        title_clean = raw_title
    else:
        # Si no se suministró título específico o solo se envió el nombre de la cátedra
        if file and file.filename:
            raw_base = os.path.splitext(file.filename)[0].replace("_", " ").replace("-", " ").strip()
            title_clean = raw_base.title() if raw_base else f"Material de Estudio: {materias_clean}"
        elif material_type == "video":
            title_clean = f"Clase Audiovisual: {materias_clean}"
        else:
            title_clean = f"Aporte Académico: {materias_clean}"

    # Control de duplicados en títulos para la misma materia
    existing_same = db.query(Document).filter(
        Document.materias == materias_clean,
        Document.title.ilike(title_clean)
    ).first()
    if existing_same:
        count_same = db.query(Document).filter(
            Document.materias == materias_clean,
            Document.title.ilike(f"{title_clean}%")
        ).count()
        title_clean = f"{title_clean} (Aporte #{count_same + 1})"

    # El aportador se toma directamente de la sesión del usuario autenticado
    authors_clean = getattr(current_user, 'full_name', None) or getattr(current_user, 'nombre_completo', None) or current_user.username or current_user.email or "Estudiante UNIMAR"
    desc_clean = (description or "").strip() or f"Material académico propuesto para la cátedra {materias_clean}. Pendiente de revisión docente para asignación temática en el plan de evaluación."

    cover = "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400"
    read_link = "#"
    saved_url = external_url.strip() if external_url else "#"

    # Procesamiento por tipo de material
    if material_type == "video":
        yt_id = extract_youtube_id(external_url)
        if not yt_id:
            msg = "Por favor proporciona un enlace válido de YouTube."
            if is_ajax:
                return JSONResponse(status_code=400, content={"success": False, "error": msg})
            raise HTTPException(status_code=400, detail=msg)

        # Validación de duplicados: solo bloquea si ya está aprobado en la plataforma o si ya fue rechazado 3 veces
        matching_docs = db.query(Document).filter(
            (Document.external_url.like(f"%{yt_id}%")) | 
            (Document.read_url.like(f"%{yt_id}%"))
        ).all()

        already_approved = any(d.status == "aprobado" for d in matching_docs)
        rejected_count = sum(1 for d in matching_docs if d.status == "rechazado")

        if already_approved or rejected_count >= 3:
            duplicate_msg = "¡El video que intentas aprobar ya fue validado anteriormente, más atento Casi Ingeniero!"
            if is_ajax:
                return JSONResponse(status_code=400, content={"success": False, "error": duplicate_msg})
            catedras = db.query(Catedra).order_by(Catedra.trimestre, Catedra.nombre_catedra).all()
            return templates.TemplateResponse(
                request=request,
                name="upload_material.html",
                context={"current_user": current_user, "active_nav": "explore", "catedras": catedras, "error": duplicate_msg}
            )

        cover = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
        read_link = external_url.strip()
        saved_url = external_url.strip()
        if not title_clean:
            title_clean = f"Clase Audiovisual: {materias_clean}"

    elif material_type in ("pdf", "zip", "guia", "libro"):
        if file and file.filename:
            # Validar extensión
            ext = os.path.splitext(file.filename)[1].lower()
            if material_type == "pdf" and ext != ".pdf":
                err = "El archivo debe tener formato .pdf"
                if is_ajax:
                    return JSONResponse(status_code=400, content={"success": False, "error": err})
                raise HTTPException(status_code=400, detail=err)
            elif material_type == "zip" and ext != ".zip":
                err = "El archivo debe ser un paquete comprimido .zip"
                if is_ajax:
                    return JSONResponse(status_code=400, content={"success": False, "error": err})
                raise HTTPException(status_code=400, detail=err)

            contents = await file.read()
            if len(contents) > MAX_FILE_SIZE:
                err = f"El archivo supera el límite máximo de 30 MB (tamaño actual: {round(len(contents) / (1024*1024), 2)} MB)."
                if is_ajax:
                    return JSONResponse(status_code=400, content={"success": False, "error": err})
                raise HTTPException(status_code=400, detail=err)

            safe_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', file.filename)
            unique_filename = f"{uuid.uuid4().hex[:10]}_{safe_name}"
            target_path = os.path.join(UPLOAD_DIR, unique_filename)
            with open(target_path, "wb") as f_out:
                f_out.write(contents)

            read_link = f"/uploads/{unique_filename}"
            saved_url = read_link

            if not title_clean:
                title_clean = os.path.splitext(file.filename)[0].replace("_", " ").title()

            if material_type == "pdf":
                cover = "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400"
            else:
                cover = "https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=400"
        else:
            if external_url and external_url.strip():
                saved_url = external_url.strip()
                read_link = external_url.strip()
            if not title_clean:
                title_clean = f"Aporte Académico: {materias_clean}"
            cover = "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=400"

    # Todo contenido que se suba entra en estado 'pendiente' para ser revisado en el Panel de Validación
    initial_status = "pendiente"

    new_doc = Document(
        title=title_clean,
        subtitle=f"Aporte para {materias_clean}",
        authors=authors_clean,
        edition="Edición Digital",
        publisher="UNIMAR Digital",
        cover_url=cover,
        header_banner_url=get_catedra_banner(materias_clean),
        carreras=current_user.carrera or "Ingeniería de Sistemas",
        trimestres=str(trimestres),
        materias=materias_clean,
        tags=f"{title_clean}, {materias_clean}, {material_type}",
        description=desc_clean,
        pages=20 if material_type == "pdf" else 0,
        year=2026,
        read_url=read_link,
        external_url=saved_url,
        material_type=material_type,
        status=initial_status,
        uploaded_by_id=current_user.id,
        verified_by_id=None,
        rating_avg=0.0,
        ratings_count=0,
        star_5_count=0
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    if is_ajax:
        return JSONResponse(content={
            "success": True,
            "doc_id": new_doc.id,
            "message": "Material enviado exitosamente a revisión docente"
        })

    catedras = db.query(Catedra).order_by(Catedra.trimestre, Catedra.nombre_catedra).all()
    return templates.TemplateResponse(
        request=request,
        name="upload_material.html",
        context={"current_user": current_user, "active_nav": "explore", "catedras": catedras, "success": True}
    )

@router.get("/validation-panel", response_class=HTMLResponse)
def validation_panel_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if not current_user.can_validate:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    pending_docs = db.query(Document).filter(Document.status == "pendiente").order_by(Document.id.desc()).all()

    # Docentes y curadores pendientes de comprobación institucional por el CEO
    pending_docentes = []
    all_users = []
    if current_user.is_ceo:
        pending_docentes = db.query(User).filter(User.id_rol >= 2, User.validado_por_ceo == 0).order_by(User.id.desc()).all()
        all_users = db.query(User).order_by(User.full_name.asc()).all()

    return templates.TemplateResponse(
        request=request,
        name="validation_panel.html",
        context={
            "current_user": current_user,
            "active_nav": "explore",
            "pending_documents": pending_docs,
            "pending_docentes": pending_docentes,
            "all_users": all_users
        }
    )

@router.post("/document/{doc_id}/validate")
def validate_document(
    doc_id: int,
    request: Request,
    action: str = Form(...),
    title: str = Form(None),
    rejection_reason: str = Form(None),
    is_custom_reason: str = Form("false"),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user or not current_user.can_validate:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        if action == "aprobar":
            doc.status = "aprobado"
            doc.verified_by_id = current_user.id
            assigned_title = (title or "").strip()
            if assigned_title:
                doc.title = assigned_title
            doc.rejection_reason = None
            doc.rejection_file_url = None
        elif action == "rechazar":
            doc.status = "rechazado"
            doc.verified_by_id = current_user.id
            
            clean_reason = (rejection_reason or "").strip()
            reason_option_1 = "El contenido que indicaste no tiene mucha relacion con la catedra que seleccionaste"
            reason_option_2 = "Ya existe un contenido muy similar a este en la plataforma"
            
            # Determinar si es un motivo personalizado ("Otro motivo") o una de las opciones predefinidas
            is_custom = (is_custom_reason or "").lower() == "true" or (
                clean_reason
                and clean_reason != reason_option_1
                and clean_reason != reason_option_2
                and "relacion con la catedra" not in clean_reason.lower()
                and "similar a este" not in clean_reason.lower()
            )
            
            if is_custom and clean_reason:
                # Carpeta de almacenamiento para archivos de retroalimentación .txt
                rechazos_dir = os.path.join(UPLOAD_DIR, "motivos_rechazo")
                os.makedirs(rechazos_dir, exist_ok=True)
                
                txt_filename = f"motivo_rechazo_doc_{doc.id}_{uuid.uuid4().hex[:8]}.txt"
                txt_filepath = os.path.join(rechazos_dir, txt_filename)
                
                evaluator_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'nombre_completo', None) or current_user.username or "Docente Evaluador"
                evaluator_role = getattr(current_user, 'rol_nombre', None) or "Docente de Cátedra"
                evaluator_cargo = getattr(current_user, 'cargo_abreviado', None) or "Prof."
                student_name = doc.uploaded_by.full_name if doc.uploaded_by else doc.authors
                now_str = datetime.now().strftime("%d/%m/%Y a las %I:%M %p")
                
                txt_content = (
                    "======================================================================\n"
                    "UNIVERSIDAD DE MARGARITA (UNIMAR) - VICERRECTORADO ACADÉMICO\n"
                    "DECANATO DE INGENIERÍA Y AFINES - PLATAFORMA CARAMEL\n"
                    "DICTAMEN DE REVISIÓN Y VALIDACIÓN DE MATERIAL ACADÉMICO\n"
                    "======================================================================\n\n"
                    f"FECHA DE REVISIÓN: {now_str}\n"
                    f"ESTADO: NO ADMITIDO / RECHAZADO\n\n"
                    "----------------------------------------------------------------------\n"
                    "DATOS DEL RECURSO EVALUADO:\n"
                    "----------------------------------------------------------------------\n"
                    f"• Título del recurso: {doc.title}\n"
                    f"• Cátedra asignada:   {doc.materias}\n"
                    f"• Nivel curricular:   Trimestre {doc.trimestres}\n"
                    f"• Tipo de contenido:  {doc.material_type.upper()}\n"
                    f"• Estudiante autor:   {student_name}\n\n"
                    "----------------------------------------------------------------------\n"
                    "DOCENTE / CURADOR EVALUADOR:\n"
                    "----------------------------------------------------------------------\n"
                    f"• Evaluado por:       {evaluator_cargo} {evaluator_name}\n"
                    f"• Rol institucional:  {evaluator_role}\n"
                    f"• Correo oficial:     {current_user.email}\n\n"
                    "======================================================================\n"
                    "MOTIVO DETALLADO Y OBSERVACIONES TÉCNICAS DEL RECHAZO:\n"
                    "======================================================================\n\n"
                    f"{clean_reason}\n\n"
                    "----------------------------------------------------------------------\n"
                    "ORIENTACIÓN ACADÉMICA PARA EL ALUMNO:\n"
                    "----------------------------------------------------------------------\n"
                    "Estimado estudiante, en la Universidad de Margarita velamos por la\n"
                    "pertinencia y excelencia de los contenidos compartidos en Caramel.\n"
                    "Te invitamos a tomar en cuenta las observaciones emitidas por el\n"
                    "docente, ajustar tu recurso educativo y volver a postularlo a través\n"
                    "de la sección 'Aportar Material'.\n\n"
                    "======================================================================\n"
                    "Caramel UNIMAR - Repositorio y Motor de Recomendación Curricular\n"
                    "======================================================================\n"
                )
                
                with open(txt_filepath, "w", encoding="utf-8") as f_txt:
                    f_txt.write(txt_content)
                
                doc.rejection_reason = clean_reason
                doc.rejection_file_url = f"/uploads/motivos_rechazo/{txt_filename}"
            else:
                # Opciones predefinidas directas (1 paso)
                doc.rejection_reason = clean_reason or reason_option_1
                doc.rejection_file_url = None
                
        db.commit()

    return RedirectResponse(url=f"/validation-panel?status={action}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/admin/user/{target_id}/approve-docente")
def approve_docente(target_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or not current_user.is_ceo:
        raise HTTPException(status_code=403, detail="Exclusivo para autorización por el CEO")

    target = db.query(User).filter(User.id == target_id).first()
    if target:
        target.validado_por_ceo = 1
        db.commit()

    return RedirectResponse(url="/validation-panel?status=docente_aprobado", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/admin/user/{target_id}/reject-docente")
def reject_docente(target_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or not current_user.is_ceo:
        raise HTTPException(status_code=403, detail="Exclusivo para autorización por el CEO")

    target = db.query(User).filter(User.id == target_id).first()
    if target:
        target.id_rol = 1
        target.rol_nombre = "Estudiante"
        target.titulo_honorifico = "Casi Ingeniero"
        target.validado_por_ceo = 1
        db.commit()

    return RedirectResponse(url="/validation-panel?status=docente_rechazado", status_code=status.HTTP_303_SEE_OTHER)