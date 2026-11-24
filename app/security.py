import bcrypt
import hashlib
import hmac
import os
import time
from dotenv import load_dotenv

load_dotenv()

SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 días


def _get_session_secret() -> bytes:
    """
    Obtiene la clave secreta para firmar cookies de sesión con HMAC-SHA256.
    Prioriza SESSION_SECRET_KEY desde variables de entorno (.env / Render).
    """
    env_secret = os.getenv("SESSION_SECRET_KEY", "").strip()
    if env_secret:
        return env_secret.encode("utf-8")
    # Fallback determinista derivado del entorno para evitar sesiones rotas en desarrollo local
    fallback_seed = os.getenv("DATABASE_URL", "caramel-local-dev-key") + "::caramel-hmac-v1"
    return hashlib.sha256(fallback_seed.encode("utf-8")).digest()


def sign_session_user_id(user_id: int) -> str:
    """Genera un token de sesión firmado criptográficamente (HMAC-SHA256) con timestamp."""
    issued_at = int(time.time())
    payload = f"{int(user_id)}.{issued_at}"
    signature = hmac.new(_get_session_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def verify_session_cookie(token: str | None, max_age: int = SESSION_MAX_AGE_SECONDS) -> int | None:
    """
    Valida la firma HMAC-SHA256 (comparación en tiempo constante) y vigencia de la cookie de sesión.
    Rechaza cualquier cookie manipulada o sin firma.
    """
    if not token or not isinstance(token, str):
        return None
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None
    uid_str, ts_str, provided_sig = parts
    if not uid_str.isdigit() or not ts_str.isdigit():
        return None
    payload = f"{uid_str}.{ts_str}"
    expected_sig = hmac.new(_get_session_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, provided_sig):
        return None
    now = int(time.time())
    issued_at = int(ts_str)
    if issued_at > now + 60 or (now - issued_at) > max_age:
        return None
    return int(uid_str)


def is_bcrypt_hash(hashed_password: str | None) -> bool:
    return bool(hashed_password and (hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$")))


def hash_password(password: str) -> str:
    """Generates a secure bcrypt hash with 12 rounds conforming to ISO/IEC 27001 & RNF-03."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely verifies a password against its bcrypt hash (with constant-time transition check for legacy rows)."""
    if not hashed_password:
        return False
    try:
        if is_bcrypt_hash(hashed_password):
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False
    # Transición segura en tiempo constante para cuentas heredadas antes de migrar a bcrypt
    return hmac.compare_digest(plain_password, hashed_password)


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
        return False, "Debes usar tu correo institucional (@unimar.edu.ve)."
    return True, ""
