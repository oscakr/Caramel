from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models import User, Document, CuratedList, Review, Friendship
from ..recommender import AcademicRecommender
from .auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

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

    # 5. Pending materials count for teachers/curators
    pending_validation_count = 0
    if current_user.id_rol and current_user.id_rol >= 2:
        pending_validation_count = db.query(Document).filter(Document.status == "pendiente").count()

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

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "current_user": current_user,
            "active_nav": "profile",
        }
    )

@router.get("/notifications", response_class=HTMLResponse)
def notifications_view(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="notifications.html",
        context={
            "current_user": current_user,
            "active_nav": "notifications",
        }
    )
