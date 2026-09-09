from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import User, Document
from ..recommender import AcademicRecommender

router = APIRouter(prefix="/api", tags=["API"])

@router.get("/recommendations")
def get_recommendations_api(
    user_id: int = Query(1, description="ID del usuario universitario"),
    limit: int = Query(5, description="Número de recomendaciones a retornar"),
    db: Session = Depends(get_db)
):
    """
    Endpoint del motor de recomendación híbrido de Caramel.
    Calcula en tiempo real los puntajes curriculares, colaborativos y de contenido.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "Usuario no encontrado"}

    recommender = AcademicRecommender(db)
    raw_recs = recommender.get_recommendations(user_id, limit=limit)

    results = []
    for r in raw_recs:
        doc = r["document"]
        results.append({
            "document_id": doc.id,
            "title": doc.title,
            "authors": doc.authors,
            "cover_url": doc.cover_url,
            "carreras": doc.carreras,
            "trimestres": doc.trimestres,
            "materias": doc.materias,
            "composite_score": r["score"],
            "academic_context_score": r["academic_score"],
            "social_peer_score": r["social_score"],
            "content_tfidf_score": r["content_score"],
            "bayesian_quality_score": r["quality_score"],
            "explainability_reason": r["reason"],
            "rating_avg": doc.rating_avg,
            "ratings_count": doc.ratings_count
        })

    return {
        "user": {
            "id": user.id,
            "name": user.full_name,
            "carrera": user.carrera,
            "trimestre": user.trimestre
        },
        "algorithm": "Hybrid Collaborative & Curricular Content-Based TF-IDF",
        "total_results": len(results),
        "recommendations": results
    }

@router.get("/documents")
def get_documents_api(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "authors": d.authors,
            "rating": d.rating_avg,
            "carreras": d.carreras,
            "trimestres": d.trimestres
        }
        for d in docs
    ]
