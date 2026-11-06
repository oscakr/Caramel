from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from .database import Base

curated_list_documents = Table(
    "curated_list_documents",
    Base.metadata,
    Column("curated_list_id", Integer, ForeignKey("curated_lists.id"), primary_key=True),
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
)

class Role(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True, autoincrement=True)
    nombre_rol = Column(String(50), unique=True, nullable=False) # 'Estudiante', 'Docente de Cátedra', 'Curador/Administrador'
    permisos = Column(Text, nullable=False, default="{}")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    carrera = Column(String(100), nullable=False, default="Ingeniería de Sistemas")
    trimestre = Column(Integer, nullable=False, default=3)
    avatar_url = Column(String(255), default="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Roles y reputación comunitaria según norma institucional ISO / Tesis
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=True)
    rol_nombre = Column(String(50), default="Estudiante")
    puntos_reputacion = Column(Integer, default=0)

    rol = relationship("Role", foreign_keys=[id_rol], lazy="joined")

    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship("UserInteraction", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False, index=True)
    subtitle = Column(String(150), nullable=True)
    edition = Column(String(50), nullable=True)
    authors = Column(String(200), nullable=False)
    publisher = Column(String(100), nullable=True)
    cover_url = Column(String(300), nullable=False)
    header_banner_url = Column(String(300), nullable=True)
    carreras = Column(String(250), nullable=False)  # Comma-separated: "Ingeniería de Sistemas,Computación,Civil"
    trimestres = Column(String(100), nullable=False) # Comma-separated: "2,3,4"
    materias = Column(String(250), nullable=False)  # Comma-separated: "Cálculo II,Matemáticas II"
    tags = Column(String(350), nullable=False)      # Keywords for TF-IDF
    description = Column(Text, nullable=False)
    pages = Column(Integer, default=650)
    year = Column(Integer, default=2021)
    read_url = Column(String(300), default="#")
    
    # Rating stats (mirroring Figma's 4.6 and 5-tier histogram)
    rating_avg = Column(Float, default=4.5)
    ratings_count = Column(Integer, default=1)
    star_5_count = Column(Integer, default=10)
    star_4_count = Column(Integer, default=6)
    star_3_count = Column(Integer, default=2)
    star_2_count = Column(Integer, default=1)
    star_1_count = Column(Integer, default=0)

    reviews = relationship("Review", back_populates="document", cascade="all, delete-orphan", order_by="desc(Review.created_at)")
    curated_lists = relationship("CuratedList", secondary=curated_list_documents, back_populates="documents")
    interactions = relationship("UserInteraction", back_populates="document", cascade="all, delete-orphan")

    def update_rating_stats(self):
        """Recalculate average rating and histogram from actual reviews."""
        if not self.reviews:
            return
        c1 = sum(1 for r in self.reviews if r.rating == 1)
        c2 = sum(1 for r in self.reviews if r.rating == 2)
        c3 = sum(1 for r in self.reviews if r.rating == 3)
        c4 = sum(1 for r in self.reviews if r.rating == 4)
        c5 = sum(1 for r in self.reviews if r.rating == 5)
        total = len(self.reviews)
        avg = sum(r.rating for r in self.reviews) / total if total > 0 else 0.0

        self.star_1_count = c1
        self.star_2_count = c2
        self.star_3_count = c3
        self.star_4_count = c4
        self.star_5_count = c5
        self.ratings_count = total
        self.rating_avg = round(avg, 1)

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    rating = Column(Integer, nullable=False) # 1 to 5
    content = Column(Text, nullable=False)
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    document = relationship("Document", back_populates="reviews")

class CuratedList(Base):
    __tablename__ = "curated_lists"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(String(250), nullable=True)
    creator_name = Column(String(100), default="Caramel Académico")
    creator_avatar = Column(String(250), default="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150")
    carrera = Column(String(100), nullable=True)
    trimestre = Column(Integer, nullable=True)
    badge_color = Column(String(50), default="caramel") # styling theme
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", secondary=curated_list_documents, back_populates="curated_lists")

class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookmarks")
    document = relationship("Document")

class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    interaction_type = Column(String(50), nullable=False) # 'view', 'read', 'save', 'rate'
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    document = relationship("Document", back_populates="interactions")
