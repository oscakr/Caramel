"""
Initial database seeder for Caramel.
Creates system roles and official accounts without fake documents or preview mockups.
"""

from sqlalchemy.orm import Session
from .models import User, Role
from .database import SessionLocal, engine, Base
from .security import hash_password

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 0. Create Roles if not present
    if not db.query(Role).first():
        db.add_all([
            Role(id_rol=1, nombre_rol="Estudiante", permisos='{"can_read": true, "can_review": true, "can_upload": true}'),
            Role(id_rol=2, nombre_rol="Docente de Cátedra", permisos='{"can_read": true, "can_review": true, "can_upload": true, "can_validate": true}'),
            Role(id_rol=3, nombre_rol="Curador/Administrador", permisos='{"can_read": true, "can_review": true, "can_upload": true, "can_validate": true, "can_admin": true}'),
            Role(id_rol=4, nombre_rol="CEO", permisos='{"can_read": true, "can_review": true, "can_upload": true, "can_validate": true, "can_admin": true, "is_ceo": true}')
        ])
        db.commit()

    # Check if already seeded with users
    if db.query(User).first():
        db.close()
        return

    print("Initializing official institutional users...")

    # 1. Create Official CEO User (Oscar)
    default_pwd = hash_password("password123")
    users_data = [
        {
            "username": "P3",
            "email": "oalvarez.7305@unimar.edu.ve",
            "password": default_pwd,
            "full_name": "Oscar Alvarez",
            "carrera": "Ingeniería de Sistemas",
            "trimestre": 3,
            "id_rol": 4,
            "rol_nombre": "CEO",
            "puntos_reputacion": 100,
            "avatar_url": "/static/img/caramel_logo.png",
            "showcase_ids": ""
        }
    ]

    for u_data in users_data:
        user = User(**u_data)
        db.add(user)
    db.commit()

    db.close()
    print("Database initialization completed cleanly without mockups.")

if __name__ == "__main__":
    seed_database()
