import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Carga variables de entorno desde el archivo .env si existe
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./caramel.db")

# Muchos proveedores de nube (Supabase, Neon, Render, Railway) proveen la URI con 'postgres://'
# SQLAlchemy 1.4+ requiere 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configuración del motor según dialecto
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # Configuración de grado de producción para PostgreSQL / Nube:
    # - pool_pre_ping: verifica la vida de la conexión antes de usarla (evita cortes SSL o desconexiones de nube)
    # - pool_recycle: recicla conexiones periódicamente
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
