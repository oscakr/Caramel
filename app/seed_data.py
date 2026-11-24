"""
Initial database seeder for Caramel.
Creates system RBAC roles and optionally bootstraps an initial administrator account
strictly from environment variables (zero hardcoded credentials in source code).
"""

import os
from .models import User, Role
from .database import SessionLocal, engine, Base
from .security import hash_password


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 0. Create official RBAC Roles if not present
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
            return

        # Optional initial CEO bootstrap strictly via environment variables (CWE-798 compliant)
        admin_email = os.getenv("CARAMEL_ADMIN_EMAIL", "").strip().lower()
        admin_password = os.getenv("CARAMEL_ADMIN_PASSWORD", "").strip()
        admin_username = os.getenv("CARAMEL_ADMIN_USERNAME", "admin").strip()
        admin_full_name = os.getenv("CARAMEL_ADMIN_FULL_NAME", "Administrador Caramel").strip()

        if admin_email and admin_password:
            print("Bootstrapping initial administrator account from environment variables...")
            ceo_user = User(
                username=admin_username,
                email=admin_email,
                password=hash_password(admin_password),
                full_name=admin_full_name,
                carrera="Ingeniería de Sistemas",
                trimestre=3,
                id_rol=4,
                rol_nombre="CEO",
                puntos_reputacion=100,
                avatar_url="/static/img/caramel_logo.png",
                showcase_ids="",
                validado_por_ceo=1,
            )
            db.add(ceo_user)
            db.commit()
        print("Database initialization completed cleanly without hardcoded credentials.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
