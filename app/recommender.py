"""
Academic Document Recommendation Engine for Caramel.
Implements a Hybrid Filtering Architecture:
1. Curricular / Academic Contextual Filtering (Career + Trimester match)
2. Social / Collaborative Peer Filtering (Friends & Cohort interactions)
3. Content-Based Filtering with TF-IDF Vector Space & Cosine Similarity
4. Bayesian Quality Smoothing
5. Transparent Reason Generation (Explainable AI)
"""

from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from .models import User, Document, Review, Friendship, Bookmark, UserInteraction

SPANISH_STOP_WORDS = [
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para",
    "con", "no", "una", "su", "al", "lo", "como", "mas", "pero", "sus", "le", "ya", "o", "este",
    "si", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre", "tambien", "me", "hasta",
    "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos", "uno", "les", "ni", "contra",
    "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mi", "antes", "algunos", "que", "unos", "yo",
    "otro", "otras", "otra", "el", "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual",
    "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros", "mi", "mis", "tu", "te", "ti", "tu", "tus"
]

class AcademicRecommender:
    def __init__(self, db: Session):
        self.db = db
        self.vectorizer = TfidfVectorizer(
            stop_words=SPANISH_STOP_WORDS,
            ngram_range=(1, 2),
            max_features=2500
        )

    def _build_document_corpus(self, documents: List[Document]) -> List[str]:
        """Creates rich textual representations for content-based matching."""
        corpus = []
        for doc in documents:
            text = f"{doc.title} {doc.subtitle or ''} {doc.authors} {doc.carreras} {doc.materias} {doc.tags} {doc.description}"
            corpus.append(text.lower())
        return corpus

    def _get_user_interest_text(self, user: User, documents_by_id: Dict[int, Document]) -> str:
        """Constructs a composite profile text reflecting user's academic level and interactions."""
        profile_tokens = [user.carrera.lower(), f"trimestre {user.trimestre}"]

        # Positively rated documents (4 or 5 stars)
        for rev in user.reviews:
            if rev.rating >= 4 and rev.document_id in documents_by_id:
                doc = documents_by_id[rev.document_id]
                profile_tokens.extend([doc.title, doc.materias, doc.tags])

        # Bookmarks
        for bm in user.bookmarks:
            if bm.document_id in documents_by_id:
                doc = documents_by_id[bm.document_id]
                profile_tokens.extend([doc.title, doc.materias, doc.tags])

        # Explicit interactions
        for inter in user.interactions:
            if inter.document_id in documents_by_id and inter.interaction_type in ('read', 'save'):
                doc = documents_by_id[inter.document_id]
                profile_tokens.extend([doc.materias, doc.tags])

        return " ".join(profile_tokens)

    def _get_friend_ids(self, user_id: int) -> List[int]:
        friendships = self.db.query(Friendship).filter(
            (Friendship.user_id == user_id) | (Friendship.friend_id == user_id)
        ).all()
        friends = set()
        for f in friendships:
            if f.user_id == user_id:
                friends.add(f.friend_id)
            else:
                friends.add(f.user_id)
        return list(friends)

    def get_recommendations(
        self,
        user_id: int,
        limit: int = 10,
        exclude_interacted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Calculates hybrid recommendation scores for the user.
        Returns sorted list of dicts with document object, scores, and explanation.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        all_documents = self.db.query(Document).all()
        if not all_documents:
            return []

        docs_by_id = {doc.id: doc for doc in all_documents}
        friend_ids = self._get_friend_ids(user_id)

        # 1. Content-based Vector Space
        corpus = self._build_document_corpus(all_documents)
        try:
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            user_text = self._get_user_interest_text(user, docs_by_id)
            user_vec = self.vectorizer.transform([user_text])
            content_similarities = cosine_similarity(user_vec, tfidf_matrix).flatten()
        except Exception:
            # Fallback if corpus vocabulary is very sparse
            content_similarities = np.zeros(len(all_documents))

        # 2. Bayesian Quality Score Calculation
        # WR = (v / (v + m)) * R + (m / (v + m)) * C
        all_ratings = [doc.rating_avg for doc in all_documents if doc.ratings_count > 0]
        global_avg_c = np.mean(all_ratings) if all_ratings else 4.0
        m = 3.0  # minimum reviews threshold for Bayesian confidence

        # 3. Compute Composite Scores
        scored_items = []
        user_reviewed_doc_ids = {r.document_id for r in user.reviews}

        for idx, doc in enumerate(all_documents):
            if exclude_interacted and doc.id in user_reviewed_doc_ids:
                continue

            # A. Academic Contextual Score (0.0 to 1.0)
            acad_score = 0.0
            doc_carreras = [c.strip().lower() for c in doc.carreras.split(",")]
            user_carrera = user.carrera.strip().lower()

            if any(user_carrera in c or c in user_carrera for c in doc_carreras):
                acad_score += 0.55  # Carrera afín

            # Trimestre proximity score
            doc_trimestres = [int(t.strip()) for t in doc.trimestres.split(",") if t.strip().isdigit()]
            if user.trimestre in doc_trimestres:
                acad_score += 0.45  # Coincide con su trimestre actual
            elif any(abs(user.trimestre - t) == 1 for t in doc_trimestres):
                acad_score += 0.25  # Trimestre contiguo (+/- 1)
            acad_score = min(1.0, acad_score)

            # B. Social / Peer Score (0.0 to 1.0)
            social_score = 0.0
            friends_who_read = []
            friends_high_rating_count = 0

            for rev in doc.reviews:
                if rev.user_id in friend_ids:
                    friends_who_read.append(rev.user)
                    if rev.rating >= 4:
                        friends_high_rating_count += 1

            if friends_who_read:
                social_score = min(1.0, 0.4 + (friends_high_rating_count * 0.2))
            else:
                # Cohort proxy: peers from same career and trimester
                cohort_reviews = [
                    r for r in doc.reviews
                    if r.user and r.user.carrera.lower() == user_carrera and r.user.trimestre == user.trimestre
                ]
                if cohort_reviews:
                    social_score = min(0.7, 0.2 + len(cohort_reviews) * 0.15)

            # C. Content Similarity Score (0.0 to 1.0)
            content_score = float(content_similarities[idx])

            # D. Bayesian Quality Score (0.0 to 1.0 normalized)
            v = float(doc.ratings_count)
            r = float(doc.rating_avg)
            bayesian_score = ((v / (v + m)) * r + (m / (v + m)) * global_avg_c) / 5.0

            # --- Hybrid Combination ---
            # Weights: Academic: 0.35, Social: 0.25, Content: 0.25, Quality: 0.15
            composite_score = (
                0.35 * acad_score +
                0.25 * social_score +
                0.25 * content_score +
                0.15 * bayesian_score
            )

            # --- Generate Explanation Reason ---
            reasons = []
            if user.trimestre in doc_trimestres and any(user_carrera in c for c in doc_carreras):
                reasons.append(f"Clave para tu {user.trimestre}º Trimestre de {user.carrera}")
            elif friends_high_rating_count > 0:
                reasons.append(f"Recomendado por {friends_high_rating_count} de tus amigos con 5★")
            elif content_score > 0.45:
                reasons.append(f"{int(content_score * 100)}% de afinidad con tus lecturas de estudio")
            elif doc.rating_avg >= 4.7:
                reasons.append("Material de alta calificación en la facultad")
            else:
                reasons.append("Popular entre estudiantes de tu carrera")

            scored_items.append({
                "document": doc,
                "score": round(composite_score * 100, 1),
                "academic_score": round(acad_score * 100, 1),
                "social_score": round(social_score * 100, 1),
                "content_score": round(content_score * 100, 1),
                "quality_score": round(bayesian_score * 100, 1),
                "reason": reasons[0],
                "friends_who_read": friends_who_read[:3]
            })

        # Sort descending by composite score
        scored_items.sort(key=lambda x: x["score"], reverse=True)
        return scored_items[:limit]

    def get_popular_in_trimester(self, user: User, limit: int = 6) -> List[Document]:
        """Returns documents trending in the user's current academic trimester."""
        docs = self.db.query(Document).all()
        target = str(user.trimestre)
        matched = []
        for d in docs:
            t_list = [t.strip() for t in d.trimestres.split(",")]
            if target in t_list:
                matched.append(d)

        # Sort by ratings_count and rating_avg
        matched.sort(key=lambda d: (d.ratings_count * d.rating_avg), reverse=True)
        return matched[:limit]
