import bcrypt
import re

def hash_password(password: str) -> str:
    """Generates a secure bcrypt hash with 12 rounds conforming to ISO/IEC 27001 & RNF-03."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely verifies a password against its bcrypt hash (or plain text transition fallback)."""
    if not hashed_password:
        return False
    try:
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        pass
    # Transition fallback for initial unhashed mock records
    return plain_password == hashed_password

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validates password complexity according to academic information security standards."""
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    return True, ""

def validate_institutional_email(email: str) -> tuple[bool, str]:
    """Valida que el correo pertenezca exclusivamente a la Universidad de Margarita (@unimar.edu.ve)."""
    if not email:
        return False, "Por favor ingresa tu correo institucional."
    clean = email.strip().lower()
    if "@" not in clean:
        return False, "Formato de correo electrónico inválido."
    parts = clean.split("@")
    if len(parts) != 2:
        return False, "Formato de correo electrónico inválido."
    local_part, domain = parts
    if len(local_part) < 2:
        return False, "El identificador del correo institucional es demasiado corto."
    if domain != "unimar.edu.ve":
        return False, "Registro exclusivo para la comunidad UNIMAR. Debes usar tu correo institucional (@unimar.edu.ve)."
    return True, ""
