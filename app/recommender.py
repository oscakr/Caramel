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

from .models import User, Document, Review, ReviewLike, Friendship, Bookmark, UserInteraction

# Mapeo oficial del Pensum Vigente UNIMAR (Eje de Programación y Desarrollo de Sistemas)
CATEDRA_TRIMESTRE_MAP = {
    "técnicas de programación": 3,
    "tecnicas de programacion": 3,
    "programación i": 4,
    "programacion i": 4,
    "programación ii": 5,
    "programacion ii": 5,
    "estructura de datos": 5,
    "programación iii": 6,
    "programacion iii": 6,
    "sistemas i": 6,
    "base de datos i": 6,
    "programación iv": 7,
    "programacion iv": 7,
    "sistemas ii": 7,
    "base de datos ii": 7,
    "sistemas iii": 8,
    "sistemas operativos": 9,
    "sistemas de información gerencial": 9,
    "sistemas de informacion gerencial": 9,
    "metodología de desarrollo de software": 10,
    "metodologia de desarrollo de software": 10,
}

PENSUM_CATEDRAS_POR_TRIMESTRE = {
    1: ["Técnicas de Programación", "Programación I", "Estructura de Datos", "Programación II"],
    2: ["Técnicas de Programación", "Programación I", "Estructura de Datos", "Programación II"],
    3: ["Técnicas de Programación", "Programación I", "Estructura de Datos", "Programación II"],
    4: ["Programación I", "Técnicas de Programación", "Programación II", "Estructura de Datos"],
    5: ["Estructura de Datos", "Programación II", "Programación I", "Base de Datos I"],
    6: ["Programación III", "Sistemas I", "Base de Datos I", "Estructura de Datos", "Programación II"],
    7: ["Programación IV", "Sistemas II", "Base de Datos II", "Base de Datos I", "Sistemas I"],
    8: ["Sistemas III", "Base de Datos II", "Sistemas II", "Programación IV", "Sistemas Operativos"],
    9: ["Sistemas Operativos", "Sistemas de Información Gerencial", "Sistemas III", "Metodología de Desarrollo de Software"],
    10: ["Metodología de Desarrollo de Software", "Sistemas de Información Gerencial", "Sistemas Operativos", "Sistemas III"],
    11: ["Metodología de Desarrollo de Software", "Sistemas de Información Gerencial", "Sistemas Operativos", "Sistemas III"],
    12: ["Metodología de Desarrollo de Software", "Sistemas de Información Gerencial", "Base de Datos II", "Sistemas III"],
}

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
            text = f"{doc.title or ''} {doc.subtitle or ''} {doc.authors or ''} {doc.carreras or ''} {doc.materias or ''} {doc.tags or ''} {doc.description or ''}"
            corpus.append(text.lower())
        return corpus

    def _get_user_interest_text(self, user: User, documents_by_id: Dict[int, Document]) -> str:
        """Constructs a composite profile text reflecting user's academic level and interactions."""
        profile_tokens = [(user.carrera or "").lower(), f"trimestre {user.trimestre or 3}"]

        # Materias sugeridas según el trimestre real del pensum UNIMAR
        sugeridas = PENSUM_CATEDRAS_POR_TRIMESTRE.get(user.trimestre or 3, [])
        for mat in sugeridas:
            profile_tokens.append(mat.lower())

        if getattr(user, "catedra_asignada", None):
            profile_tokens.append((user.catedra_asignada or "").lower())

        # Showcase documents (4 Materiales Favoritos del usuario)
        if getattr(user, "showcase_ids", None):
            raw_ids = [int(x.strip()) for x in user.showcase_ids.split(",") if x.strip().isdigit()]
            for sid in raw_ids:
                if sid in documents_by_id:
                    doc = documents_by_id[sid]
                    profile_tokens.extend([doc.title or "", doc.materias or "", doc.tags or ""])

        # Positively rated documents (4 or 5 stars)
        for rev in user.reviews:
            if (rev.rating or 0) >= 4 and rev.document_id in documents_by_id:
                doc = documents_by_id[rev.document_id]
                profile_tokens.extend([doc.title or "", doc.materias or "", doc.tags or ""])

        # Bookmarks
        for bm in user.bookmarks:
            if bm.document_id in documents_by_id:
                doc = documents_by_id[bm.document_id]
                profile_tokens.extend([doc.title or "", doc.materias or "", doc.tags or ""])

        # Explicit interactions
        for inter in user.interactions:
            if inter.document_id in documents_by_id and inter.interaction_type in ('read', 'save'):
                doc = documents_by_id[inter.document_id]
                profile_tokens.extend([doc.materias or "", doc.tags or ""])

        return " ".join(t for t in profile_tokens if t)

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

        all_documents = self.db.query(Document).filter(Document.status == "aprobado").all()
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
            doc_carreras = [c.strip().lower() for c in (doc.carreras or "").split(",") if c.strip()]
            user_carrera = (user.carrera or "").strip().lower()

            if user_carrera and any(user_carrera in c or c in user_carrera for c in doc_carreras):
                acad_score += 0.55  # Carrera afín

            # Trimestre & Pensum UNIMAR proximity score
            doc_trimestres = [int(t.strip()) for t in str(doc.trimestres or "").split(",") if t.strip().isdigit()]
            doc_materia_clean = (doc.materias or "").strip().lower()
            if doc_materia_clean in CATEDRA_TRIMESTRE_MAP:
                official_tri = CATEDRA_TRIMESTRE_MAP[doc_materia_clean]
                if official_tri not in doc_trimestres:
                    doc_trimestres.append(official_tri)

            user_sugeridas = [m.lower() for m in PENSUM_CATEDRAS_POR_TRIMESTRE.get(user.trimestre or 3, [])]
            user_cat_asignada = (getattr(user, "catedra_asignada", "") or "").strip().lower()

            if user.trimestre in doc_trimestres or (user_cat_asignada and user_cat_asignada in doc_materia_clean):
                acad_score += 0.45  # Coincide con su trimestre actual o cátedra asignada
            elif user_sugeridas and doc_materia_clean == user_sugeridas[0]:
                acad_score += 0.45  # Materia prioritaria de su trimestre en el pensum UNIMAR
            elif any(abs((user.trimestre or 0) - t) == 1 for t in doc_trimestres) or doc_materia_clean in user_sugeridas:
                acad_score += 0.30  # Trimestre contiguo (+/- 1) o materia del bloque sugerido
            acad_score = min(1.0, acad_score)

            # B. Social / Peer Score (0.0 to 1.0)
            social_score = 0.0
            friends_who_read = []
            friends_high_rating_count = 0

            for rev in doc.reviews:
                if rev.user_id in friend_ids:
                    friends_who_read.append(rev.user)
                    if (rev.rating or 0) >= 4:
                        friends_high_rating_count += 1

            if friends_who_read:
                social_score = min(1.0, 0.4 + (friends_high_rating_count * 0.2))
            else:
                # Cohort proxy: peers from same career and trimester
                cohort_reviews = [
                    r for r in doc.reviews
                    if r.user and (r.user.carrera or "").lower() == user_carrera and r.user.trimestre == user.trimestre
                ]
                if cohort_reviews:
                    social_score = min(0.7, 0.2 + len(cohort_reviews) * 0.15)

            # C. Content Similarity Score (0.0 to 1.0)
            content_score = float(content_similarities[idx])

            # D. Bayesian Quality Score (0.0 to 1.0 normalized)
            v = float(doc.ratings_count or 0)
            r = float(doc.rating_avg or 0.0)
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
                reasons.append(f"Recomendado por {friends_high_rating_count} de tus amigos con 5 estrellas")
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
        """Returns documents trending in the user's current academic trimester and UNIMAR pensum block."""
        docs = self.db.query(Document).filter(Document.status == "aprobado").all()
        target = str(user.trimestre or 3)
        sugeridas = [m.lower() for m in PENSUM_CATEDRAS_POR_TRIMESTRE.get(user.trimestre or 3, [])]
        matched = []
        for d in docs:
            t_list = [t.strip() for t in str(d.trimestres or "").split(",") if t.strip()]
            d_mat = (d.materias or "").strip().lower()
            if d_mat in CATEDRA_TRIMESTRE_MAP:
                t_list.append(str(CATEDRA_TRIMESTRE_MAP[d_mat]))
            if target in t_list or d_mat in sugeridas:
                matched.append(d)

        # Fallback to all approved documents if none match the exact trimester yet
        if not matched:
            matched = list(docs)

        # Sort by exact trimester match first, then ratings_count and rating_avg
        matched.sort(
            key=lambda d: (
                1 if target in [t.strip() for t in str(d.trimestres or "").split(",") if t.strip()] else 0,
                (d.ratings_count or 0) * (d.rating_avg or 0.0)
            ),
            reverse=True
        )
        return matched[:limit]
