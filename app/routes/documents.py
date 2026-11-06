import re
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Document, Review, Bookmark, UserInteraction
from .auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_youtube_embed_url(url: str | None) -> str | None:
    if not url:
        return None
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return f"https://www.youtube-nocookie.com/embed/{match.group(1)}"
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

@router.get("/upload-material", response_class=HTMLResponse)
def upload_material_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="upload_material.html",
        context={"current_user": current_user, "active_nav": "explore", "success": False}
    )

@router.post("/upload-material")
def upload_material_submit(
    request: Request,
    title: str = Form(...),
    authors: str = Form(...),
    materias: str = Form(...),
    trimestres: int = Form(...),
    material_type: str = Form("libro"),
    external_url: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    is_teacher = bool(current_user.id_rol and current_user.id_rol >= 2)
    initial_status = "aprobado" if is_teacher else "pendiente"

    cover = "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400"
    if material_type == "video":
        cover = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400"
    elif material_type == "guia":
        cover = "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=400"

    new_doc = Document(
        title=title.strip(),
        subtitle="Material propuesto por la comunidad",
        authors=authors.strip(),
        edition="Edición Digital",
        publisher="UNIMAR Digital",
        cover_url=cover,
        header_banner_url="https://images.unsplash.com/photo-1509228468518-180dd4864904?w=1000",
        carreras=current_user.carrera or "Ingeniería de Sistemas",
        trimestres=str(trimestres),
        materias=materias.strip(),
        tags=f"{title}, {materias}, {material_type}",
        description=description.strip(),
        pages=120 if material_type == "libro" else 15,
        year=2026,
        read_url=external_url.strip(),
        external_url=external_url.strip(),
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

    return templates.TemplateResponse(
        request=request,
        name="upload_material.html",
        context={"current_user": current_user, "active_nav": "explore", "success": True}
    )

@router.get("/validation-panel", response_class=HTMLResponse)
def validation_panel_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    pending_docs = db.query(Document).filter(Document.status == "pendiente").order_by(Document.id.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="validation_panel.html",
        context={"current_user": current_user, "active_nav": "explore", "pending_documents": pending_docs}
    )

@router.post("/document/{doc_id}/validate")
def validate_document(
    doc_id: int,
    request: Request,
    action: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user:
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
