from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Document, Review, Bookmark, UserInteraction
from .auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/document/{doc_id}", response_class=HTMLResponse)
def document_detail(doc_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
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

    return templates.TemplateResponse(
        request=request,
        name="document_detail.html",
        context={
            "current_user": current_user,
            "document": doc,
            "is_bookmarked": is_bookmarked,
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
