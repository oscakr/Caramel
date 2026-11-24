import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Carga variables de entorno desde el archivo .env si existe
load_dotenv()

# Permite alternar entre SQLite local y Supabase sin modificar .env:
#   CARAMEL_DB_MODE=local  -> fuerza sqlite:///./caramel.db
#   CARAMEL_DB_MODE=online -> usa DATABASE_URL de .env (Supabase PostgreSQL)
CARAMEL_DB_MODE = os.getenv("CARAMEL_DB_MODE", "").strip().lower()
if CARAMEL_DB_MODE == "local":
    DATABASE_URL = "sqlite:///./caramel.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./caramel.db")

# Normalizar prefijo para usar el driver psycopg2 instalado en el venv
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

IS_LOCAL_DB = DATABASE_URL.startswith("sqlite")

# Configuración del motor según dialecto
if IS_LOCAL_DB:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print("[Caramel DB] Modo activo: LOCAL (SQLite -> caramel.db)")
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
    print("[Caramel DB] Modo activo: ONLINE (PostgreSQL / Supabase Cloud)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
