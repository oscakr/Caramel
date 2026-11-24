from datetime import datetime
import random
import uuid
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Table, BigInteger, SmallInteger, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .database import Base

DEFAULT_AVATARS = [
    "/static/img/avatares/Flavio.jpg",
    "/static/img/avatares/Daniela.jpg",
    "/static/img/avatares/Franklin.jpg",
    "/static/img/avatares/Jhonny.jpg",
    "/static/img/avatares/Oswuald.jpg",
    "/static/img/avatares/Yemnel.jpg",
]
DEFAULT_BANNER = "/static/img/bannerdefault.jpg"

# ==============================================================================
# MODELO ENTIDAD-RELACIÓN OFICIAL DE LA TESIS (CUADRO Nº 23 - DICCIONARIO DE DATOS)
# PostgreSQL 15 en 3FN para Supabase
# ==============================================================================

class Role(Base):
    """Tabla ROLES: Catálogo de roles según estándar ISO 21001 y políticas UNIMAR."""
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True, autoincrement=True)
    nombre_rol = Column(String(50), unique=True, nullable=False) # 'Estudiante', 'Docente de Cátedra', 'Curador/Administrador'
    permisos = Column(Text, nullable=False, default="{}")

class Usuario(Base):
    """Tabla USUARIOS: Comunidad estudiantil y docente registrada con @unimar.edu.ve."""
    __tablename__ = "usuarios"

    id_usuario = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre_completo = Column(String(150), nullable=False)
    correo_institucional = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False) # Hash bcrypt factor 12
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    carrera = Column(String(100), nullable=False, default="Ingeniería de Sistemas")
    trimestre = Column(Integer, nullable=False, default=3)
    avatar_url = Column(String(255), default=lambda: random.choice(DEFAULT_AVATARS))
    puntos_reputacion = Column(Integer, default=0)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    titulo_honorifico = Column(String(50), default="Casi Ingeniero")
    showcase_ids = Column(String(255), default="")
    validado_por_ceo = Column(SmallInteger, default=1)
    banner_url = Column(String(300), default=DEFAULT_BANNER)
    banner_position = Column(String(50), default="50% 50%")
    catedra_asignada = Column(String(100), default="Todas las Cátedras del Eje")
    last_trimestre_change = Column(DateTime, nullable=True)

    rol = relationship("Role", foreign_keys=[id_rol], lazy="joined")
    proyectos = relationship("Proyecto", back_populates="autor", foreign_keys="Proyecto.id_autor")
    revisiones = relationship("RevisionPares", back_populates="revisor")
    valoraciones = relationship("Valoracion", back_populates="usuario")

    # Propiedades de compatibilidad de acceso para la interfaz Caramel:
    @property
    def id(self):
        return str(self.id_usuario)

    @property
    def username(self):
        if self.is_ceo:
            return "P3"
        return self.correo_institucional.split("@")[0]

    @property
    def email(self):
        return self.correo_institucional

    @property
    def password(self):
        return self.password_hash

    @property
    def full_name(self):
        return self.nombre_completo

    @property
    def rol_nombre(self):
        return self.rol.nombre_rol if self.rol else "Estudiante"

    @property
    def saludo_titulo(self):
        if self.titulo_honorifico:
            return self.titulo_honorifico
        if self.id_rol == 2:
            if "ing" in (self.nombre_completo or "").lower():
                return "Ingeniero"
            return "Profesor"
        elif self.id_rol == 3:
            if "dra" in (self.nombre_completo or "").lower() or "dr" in (self.nombre_completo or "").lower():
                return "Doctora"
            return "Profesor"
        return "Casi Ingeniero"

    @property
    def is_ceo(self) -> bool:
        return (
            self.correo_institucional == "oalvarez.7305@unimar.edu.ve"
            or (self.rol and self.rol.nombre_rol == "CEO")
            or self.rol_nombre == "CEO"
        )

    @property
    def cargo_abreviado(self) -> str:
        """Abreviación oficial del cargo para el badge del header institucional."""
        if self.is_ceo:
            return "CEO"
        is_docente = (self.id_rol == 2) or ("docente" in (self.rol_nombre or "").lower()) or ("profesor" in (self.rol_nombre or "").lower())
        if is_docente:
            th = (self.titulo_honorifico or "").strip().lower()
            if "ing" in th:
                return "Ing."
            elif "dra" in th:
                return "Dra."
            elif "dr" in th:
                return "Dr."
            elif "mag" in th or "msc" in th or "master" in th:
                return "MSc."
            elif "lic" in th:
                return "Lic."
            elif "prof" in th:
                return "Prof."
            fn = (self.full_name or "").lower()
            if "ing" in fn:
                return "Ing."
            elif "dra" in fn:
                return "Dra."
            elif "dr" in fn:
                return "Dr."
            elif "msc" in fn:
                return "MSc."
            elif "lic" in fn:
                return "Lic."
            return "Prof."
        return "Est."

class Catedra(Base):
    """Tabla CATEDRAS: Unidades curriculares del plan de estudio de UNIMAR."""
    __tablename__ = "catedras"

    id_catedra = Column(Integer, primary_key=True, autoincrement=True)
    codigo_materia = Column(String(20), unique=True, nullable=False) # Ej. SIS-101
    nombre_catedra = Column(String(100), nullable=False) # Ej. Algoritmos y Programación I
    trimestre = Column(Integer, nullable=False) # 1 al 12

    proyectos = relationship("Proyecto", back_populates="catedra")

class Proyecto(Base):
    """Tabla PROYECTOS: Proyectos de software y materiales académicos bajo estándar Dublin Core."""
    __tablename__ = "proyectos"

    id_proyecto = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    titulo = Column(String(200), nullable=False, index=True) # Dublin Core: Title
    descripcion = Column(Text, nullable=False)               # Dublin Core: Description
    id_autor = Column(String(36), ForeignKey("usuarios.id_usuario"), nullable=False)
    id_catedra = Column(Integer, ForeignKey("catedras.id_catedra"), nullable=False)
    lenguaje_principal = Column(String(50), nullable=False) # Python, Java, C++, JS, SQL
    tipo_material = Column(String(50), default="proyecto")   # 'proyecto', 'libro', 'video', 'guia'
    enlace_externo = Column(String(350), nullable=True)
    cover_url = Column(String(300), default="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400")
    estado_curaduria = Column(String(30), default="Pendiente") # 'Pendiente', 'Aprobado', 'Destacado', 'Rechazado'
    motivo_rechazo = Column(Text, nullable=True)
    archivo_dictamen_url = Column(String(300), nullable=True)
    id_validador = Column(String(36), ForeignKey("usuarios.id_usuario"), nullable=True)
    fecha_publicacion = Column(DateTime, default=datetime.utcnow)

    autor = relationship("Usuario", foreign_keys=[id_autor], lazy="joined", back_populates="proyectos")
    validador = relationship("Usuario", foreign_keys=[id_validador], lazy="joined")
    catedra = relationship("Catedra", foreign_keys=[id_catedra], lazy="joined", back_populates="proyectos")
    archivos = relationship("ArchivoCodigo", back_populates="proyecto", cascade="all, delete-orphan")
    revisiones = relationship("RevisionPares", back_populates="proyecto", cascade="all, delete-orphan")
    valoraciones = relationship("Valoracion", back_populates="proyecto", cascade="all, delete-orphan")

class ArchivoCodigo(Base):
    """Tabla ARCHIVOS_CODIGO: Ficheros de código fuente y scripts individuales o zip."""
    __tablename__ = "archivos_codigo"

    id_archivo = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_proyecto = Column(String(36), ForeignKey("proyectos.id_proyecto"), nullable=False)
    nombre_archivo = Column(String(120), nullable=False)
    extension = Column(String(10), nullable=False) # .py, .java, .cpp, .js, .sql, .zip
    contenido_codigo = Column(Text, nullable=True)
    tamanio_bytes = Column(BigInteger, nullable=False)
    ruta_almacenamiento = Column(String(255), nullable=False)

    proyecto = relationship("Proyecto", back_populates="archivos")

class RevisionPares(Base):
    """Tabla REVISIONES_PARES: Evaluaciones técnicas y comentarios de calidad de código."""
    __tablename__ = "revisiones_pares"

    id_revision = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_proyecto = Column(String(36), ForeignKey("proyectos.id_proyecto"), nullable=False)
    id_revisor = Column(String(36), ForeignKey("usuarios.id_usuario"), nullable=False)
    comentario_tecnico = Column(Text, nullable=False)
    calificacion_criterio = Column(Integer, nullable=True) # 1 a 5
    linea_referencia = Column(Integer, nullable=True)
    fecha_revision = Column(DateTime, default=datetime.utcnow)

    proyecto = relationship("Proyecto", back_populates="revisiones")
    revisor = relationship("Usuario", foreign_keys=[id_revisor], lazy="joined", back_populates="revisiones")

class Valoracion(Base):
    """Tabla VALORACIONES: Votos comunitarios de utilidad (+1 / -1) para el capital intelectual."""
    __tablename__ = "valoraciones"

    id_valoracion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_proyecto = Column(String(36), ForeignKey("proyectos.id_proyecto"), nullable=False)
    id_usuario = Column(String(36), ForeignKey("usuarios.id_usuario"), nullable=False)
    tipo_voto = Column(SmallInteger, nullable=False) # +1 o -1
    fecha_voto = Column(DateTime, default=datetime.utcnow)

    proyecto = relationship("Proyecto", back_populates="valoraciones")
    usuario = relationship("Usuario", foreign_keys=[id_usuario], lazy="joined", back_populates="valoraciones")


# ==============================================================================
# MODELOS DE COMPATIBILIDAD CON VISTAS NATIVAS DE CARAMEL
# ==============================================================================

curated_list_documents = Table(
    "curated_list_documents",
    Base.metadata,
    Column("curated_list_id", Integer, ForeignKey("curated_lists.id"), primary_key=True),
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    carrera = Column(String(100), nullable=False, default="Ingeniería de Sistemas")
    trimestre = Column(Integer, nullable=False, default=3)
    avatar_url = Column(String(255), default=lambda: random.choice(DEFAULT_AVATARS))
    created_at = Column(DateTime, default=datetime.utcnow)

    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=True)
    rol_nombre = Column(String(50), default="Estudiante")
    puntos_reputacion = Column(Integer, default=0)
    titulo_honorifico = Column(String(50), default="Casi Ingeniero")
    showcase_ids = Column(String(255), default="")
    validado_por_ceo = Column(SmallInteger, default=1)
    banner_url = Column(String(300), default=DEFAULT_BANNER)
    banner_position = Column(String(50), default="50% 50%")
    catedra_asignada = Column(String(100), default="Todas las Cátedras del Eje")
    last_trimestre_change = Column(DateTime, nullable=True) # 1 = Validado por CEO, 0 = Pendiente de validación
    notifications_cleared_at = Column(DateTime, nullable=True)

    rol = relationship("Role", foreign_keys=[id_rol], lazy="joined")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship("UserInteraction", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")

    @property
    def can_validate(self) -> bool:
        """Determina si el usuario tiene privilegios activos para validar recursos (CEO o docente aprobado)."""
        if self.is_ceo:
            return True
        if self.id_rol and self.id_rol >= 2:
            return bool(self.validado_por_ceo)
        return False

    @property
    def is_docente_pending_validation(self) -> bool:
        """Indica si el usuario se registró como docente o curador pero aún espera la validación del CEO."""
        if self.is_ceo:
            return False
        if self.id_rol and self.id_rol >= 2:
            return not bool(self.validado_por_ceo)
        return False

    @property
    def saludo_titulo(self):
        if self.titulo_honorifico:
            return self.titulo_honorifico
        if self.id_rol == 2:
            if "ing" in (self.full_name or "").lower():
                return "Ingeniero"
            return "Profesor"
        elif self.id_rol == 3:
            if "dra" in (self.full_name or "").lower() or "dr" in (self.full_name or "").lower():
                return "Doctora"
            return "Profesor"
        return "Casi Ingeniero"

    @property
    def nombre_completo(self):
        return self.full_name

    @property
    def is_ceo(self) -> bool:
        return (
            self.email == "oalvarez.7305@unimar.edu.ve"
            or (self.username or "").lower() in ("oalvarez.7305", "p3")
            or self.rol_nombre == "CEO"
            or (self.rol and self.rol.nombre_rol == "CEO")
        )

    @property
    def cargo_abreviado(self) -> str:
        """Abreviación oficial del cargo para el badge del header institucional."""
        if self.is_ceo:
            return "CEO"
        is_docente = (self.id_rol == 2) or ("docente" in (self.rol_nombre or "").lower()) or ("profesor" in (self.rol_nombre or "").lower())
        if is_docente:
            th = (self.titulo_honorifico or "").strip().lower()
            if "ing" in th:
                return "Ing."
            elif "dra" in th:
                return "Dra."
            elif "dr" in th:
                return "Dr."
            elif "mag" in th or "msc" in th or "master" in th:
                return "MSc."
            elif "lic" in th:
                return "Lic."
            elif "prof" in th:
                return "Prof."
            fn = (self.full_name or "").lower()
            if "ing" in fn:
                return "Ing."
            elif "dra" in fn:
                return "Dra."
            elif "dr" in fn:
                return "Dr."
            elif "msc" in fn:
                return "MSc."
            elif "lic" in fn:
                return "Lic."
            return "Prof."
        return "Est."

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
    carreras = Column(String(250), nullable=False)
    trimestres = Column(String(100), nullable=False)
    materias = Column(String(250), nullable=False)
    tags = Column(String(350), nullable=False)
    description = Column(Text, nullable=False)
    pages = Column(Integer, default=650)
    year = Column(Integer, default=2021)
    read_url = Column(String(300), default="#")
    
    rating_avg = Column(Float, default=0.0)
    ratings_count = Column(Integer, default=0)
    star_5_count = Column(Integer, default=0)
    star_4_count = Column(Integer, default=0)
    star_3_count = Column(Integer, default=0)
    star_2_count = Column(Integer, default=0)
    star_1_count = Column(Integer, default=0)

    status = Column(String(30), default="pendiente")
    consensus_state = Column(String(30), default="pendiente")  # pendiente | aprobado_provisional | en_revision | aprobado_definitivo | rechazado
    rejection_reason = Column(Text, nullable=True)
    rejection_file_url = Column(String(350), nullable=True)
    material_type = Column(String(50), default="pdf")
    external_url = Column(String(350), nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id], lazy="joined")
    verified_by = relationship("User", foreign_keys=[verified_by_id], lazy="joined")
    reviews = relationship("Review", back_populates="document", cascade="all, delete-orphan", order_by="desc(Review.created_at)")
    curated_lists = relationship("CuratedList", secondary=curated_list_documents, back_populates="documents")
    interactions = relationship("UserInteraction", back_populates="document", cascade="all, delete-orphan")

    @property
    def verifier_name(self) -> str:
        if self.verified_by:
            return self.verified_by.full_name
        return "Docente Validador"

    @property
    def verifier_role(self) -> str:
        if self.verified_by:
            return self.verified_by.rol_nombre or "Docente de Cátedra"
        return "Docente de Cátedra"

    @property
    def effective_banner_url(self) -> str:
        if self.header_banner_url and "photo-1509228468518-180dd4864904" not in self.header_banner_url:
            return self.header_banner_url
        from .catedras_config import get_catedra_banner, get_random_document_banner
        return get_catedra_banner(self.materias or self.title) or get_random_document_banner(self.id)

    @staticmethod
    def _ordinal_trimestre(num: int) -> str:
        ordinals = {
            1: "1er",
            2: "2do",
            3: "3er",
            4: "4to",
            5: "5to",
            6: "6to",
            7: "7mo",
            8: "8vo",
            9: "9no",
            10: "10mo",
            11: "11vo",
            12: "12vo",
        }
        return ordinals.get(num, f"{num}º")

    def _format_trimestres(self, suffix: str) -> str:
        raw = str(self.trimestres or "").strip()
        if not raw:
            return suffix
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        formatted = []
        for p in parts:
            try:
                formatted.append(self._ordinal_trimestre(int(p)))
            except ValueError:
                formatted.append(p)
        if not formatted:
            return suffix
        if len(formatted) == 1:
            return f"{formatted[0]} {suffix}"
        if len(formatted) == 2:
            return f"{formatted[0]} y {formatted[1]} {suffix}"
        return f"{', '.join(formatted[:-1])} y {formatted[-1]} {suffix}"

    @property
    def trimestre_badge_label(self) -> str:
        return self._format_trimestres("Trimestre")

    @property
    def trimestre_short_label(self) -> str:
        return self._format_trimestres("Tri")

    def update_rating_stats(self):
        """Recalculate average rating and histogram from actual reviews."""
        if not self.reviews:
            self.star_1_count = 0
            self.star_2_count = 0
            self.star_3_count = 0
            self.star_4_count = 0
            self.star_5_count = 0
            self.ratings_count = 0
            self.rating_avg = 0.0
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
    rating = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    document = relationship("Document", back_populates="reviews")
    likes = relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan")

class ReviewLike(Base):
    """Tabla REVIEW_LIKES: Registro de 'Me Sirve' / votos de utilidad en reseñas (1 por usuario)."""
    __tablename__ = "review_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    review = relationship("Review", back_populates="likes")

class CuratedList(Base):
    __tablename__ = "curated_lists"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(String(250), nullable=True)
    creator_name = Column(String(100), default="Caramel Académico")
    creator_avatar = Column(String(250), default="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150")
    carrera = Column(String(100), nullable=True)
    trimestre = Column(Integer, nullable=True)
    badge_color = Column(String(50), default="caramel")
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
    interaction_type = Column(String(50), nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    document = relationship("Document", back_populates="interactions")


class PasswordResetToken(Base):
    """Tabla PASSWORD_RESET_TOKENS: Enlaces temporales de un solo uso emitidos por el CEO."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    allow_email_edit = Column(SmallInteger, default=0, nullable=False)  # 0 = bloqueado, 1 = desbloqueado por CEO
    used = Column(SmallInteger, default=0, nullable=False)              # 0 = activo, 1 = consumido
    email_changed = Column(SmallInteger, default=0, nullable=False)     # 1 = se cambió también el correo
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])


class PasswordResetRequest(Base):
    """Tabla PASSWORD_RESET_REQUESTS: Avisos al CEO cuando un usuario solicita soporte desde el login."""
    __tablename__ = "password_reset_requests"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(150), nullable=False, default="")
    matched_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="pendiente")  # 'pendiente', 'atendida', 'descartada'
    created_at = Column(DateTime, default=datetime.utcnow)

    matched_user = relationship("User", foreign_keys=[matched_user_id])


class DocumentValidation(Base):
    """Tabla DOCUMENT_VALIDATIONS: Dictámenes individuales de docentes para consenso 2-de-3 y control de concurrencia."""
    __tablename__ = "document_validations"
    __table_args__ = (
        UniqueConstraint("document_id", "validator_id", name="uq_doc_validator"),
    )

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    validator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    decision = Column(String(20), nullable=False)  # 'aprobar' | 'rechazar'
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document")
    validator = relationship("User", lazy="joined")
