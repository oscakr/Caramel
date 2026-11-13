import os
import re
import uuid
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Document, Review, Bookmark, UserInteraction, Catedra
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

    youtube_embed_url = get_youtube_embed_url(doc.external_url)

    return templates.TemplateResponse(
        request=request,
        name="document_detail.html",
        context={
            "current_user": current_user,
            "document": doc,
            "is_bookmarked": is_bookmarked,
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

    # Add review
    new_review = Review(
        user_id=current_user.id,
        document_id=doc.id,
        rating=rating,
        content=content.strip(),
        likes_count=1
    )
    db.add(new_review)

    # Add interaction
    db.add(UserInteraction(
        user_id=current_user.id,
        document_id=doc.id,
        interaction_type="rate",
        weight=float(rating) / 2.0
    ))

    db.commit()

    # Recalculate document rating average and 5-star histogram
    doc.update_rating_stats()
    db.commit()

    return RedirectResponse(url=f"/document/{doc.id}", status_code=status.HTTP_303_SEE_OTHER)

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

    existing = db.query(Document).filter(
        (Document.external_url.like(f"%{yt_id}%")) | 
        (Document.read_url.like(f"%{yt_id}%"))
    ).first()

    if existing:
        return {
            "valid": True,
            "duplicate": True,
            "message": "¡El video que intentas aprobar ya fue validado anteriormente, más atento Casi Ingeniero!"
        }

    return {"valid": True, "duplicate": False}

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

    # El título del material es automáticamente el nombre de la cátedra
    title_clean = materias_clean
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

        # Validación estricta de duplicados
        existing = db.query(Document).filter(
            (Document.external_url.like(f"%{yt_id}%")) | 
            (Document.read_url.like(f"%{yt_id}%"))
        ).first()

        if existing:
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

    is_teacher = bool(current_user.can_validate)
    initial_status = "aprobado" if is_teacher else "pendiente"

    new_doc = Document(
        title=title_clean,
        subtitle=f"Aporte para {materias_clean}",
        authors=authors_clean,
        edition="Edición Digital",
        publisher="UNIMAR Digital",
        cover_url=cover,
        header_banner_url="https://images.unsplash.com/photo-1509228468518-180dd4864904?w=1000",
        carreras=current_user.carrera or "Ingeniería de Sistemas",
        trimestres=str(trimestres),
        materias=materias_clean,
        tags=f"{title_clean}, {materias_clean}, {material_type}",
        description=desc_clean,
        pages=20 if material_type == "pdf" else 1,
        year=2026,
        read_url=read_link,
        external_url=saved_url,
        material_type=material_type,
        status=initial_status,
        uploaded_by_id=current_user.id,
        verified_by_id=current_user.id if is_teacher else None,
        rating_avg=5.0,
        ratings_count=1,
        star_5_count=1
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
    if current_user.is_ceo:
        pending_docentes = db.query(User).filter(User.id_rol >= 2, User.validado_por_ceo == 0).order_by(User.id.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="validation_panel.html",
        context={
            "current_user": current_user,
            "active_nav": "explore",
            "pending_documents": pending_docs,
            "pending_docentes": pending_docentes
        }
    )

@router.post("/document/{doc_id}/validate")
def validate_document(
    doc_id: int,
    request: Request,
    action: str = Form(...),
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
        elif action == "rechazar":
            doc.status = "rechazado"
        db.commit()

    return RedirectResponse(url="/validation-panel", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/admin/user/{target_id}/approve-docente")
def approve_docente(target_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or not current_user.is_ceo:
        raise HTTPException(status_code=403, detail="Exclusivo para autorización por el CEO")

    target = db.query(User).filter(User.id == target_id).first()
    if target:
        target.validado_por_ceo = 1
        db.commit()

    return RedirectResponse(url="/validation-panel", status_code=status.HTTP_303_SEE_OTHER)

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

    return RedirectResponse(url="/validation-panel", status_code=status.HTTP_303_SEE_OTHER)
