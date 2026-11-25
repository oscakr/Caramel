from datetime import datetime, timedelta, timezone
from typing import Optional

# Hora oficial de Venezuela (VET = UTC-4, sin horario de verano)
VET_TZ = timezone(timedelta(hours=-4))


def to_vet(dt: Optional[datetime]) -> Optional[datetime]:
    """Convierte un datetime UTC (naive o aware) a hora local de Venezuela (UTC-4)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(VET_TZ)


def now_vet() -> datetime:
    """Retorna la fecha y hora actual en hora oficial de Venezuela (UTC-4)."""
    return datetime.now(VET_TZ)


def format_vet(
    dt: Optional[datetime],
    fmt: str = "%d/%m %H:%M",
    fallback: str = "Reciente",
) -> str:
    """Formatea un datetime UTC en hora local de Venezuela (UTC-4)."""
    local_dt = to_vet(dt)
    return local_dt.strftime(fmt) if local_dt else fallback
