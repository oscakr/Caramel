from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import engine, Base
from .seed_data import seed_database
from .routes import auth, feed, documents, api_recommender

# Initialize DB tables and seed data
Base.metadata.create_all(bind=engine)
seed_database()

app = FastAPI(
    title="Caramel - Plataforma de Recomendación de Documentos Académicos",
    description="Motor de recomendación híbrido para estudiantes universitarios con interfaz idéntica al prototipo de Figma.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
app.include_router(auth.router)
app.include_router(feed.router)
app.include_router(documents.router)
app.include_router(api_recommender.router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
