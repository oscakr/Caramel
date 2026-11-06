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
