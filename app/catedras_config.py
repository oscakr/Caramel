"""
Configuración centralizada de Cátedras Oficiales y Banners Académicos UNIMAR.
Eje curricular de Ingeniería de Sistemas.
"""
import os
import random

# Los 4 banners oficiales aleatorios para la cabecera de los materiales (probabilidad 1 en 4)
DOCUMENT_BANNERS: list[str] = [
    "/static/img/document_banners/banner_1.webp",
    "/static/img/document_banners/banner_2.jpg",
    "/static/img/document_banners/banner_3.jpg",
    "/static/img/document_banners/banner_4.jpg",
]


def get_random_document_banner(doc_id: int | None = None) -> str:
    """
    Devuelve aleatoriamente uno de los 4 banners oficiales de materiales (probabilidad 1 en 4).
    Si se indica doc_id (materiales existentes sin banner guardado), usa una semilla estable por ID
    para conservar la distribución 1/4 sin cambiar al recargar la página.
    """
    if doc_id is not None:
        rng = random.Random(f"caramel-doc-banner-{doc_id}")
        return rng.choice(DOCUMENT_BANNERS)
    return random.choice(DOCUMENT_BANNERS)

# Mapeo de Cátedra -> Ruta o URL de Imagen Oficial de Banner
# Cuando el usuario proporcione una imagen para una cátedra, se coloca en app/static/img/catedras/ y se vincula aquí.
CATEDRA_BANNERS: dict[str, str | None] = {
    "Técnicas de Programación": None,
    "Programación I": None,
    "Programación II": None,
    "Estructura de Datos": None,
    "Programación III": None,
    "Sistemas I": None,
    "Base de Datos I": None,
    "Programación IV": None,
    "Sistemas II": None,
    "Base de Datos II": None,
    "Sistemas III": None,
    "Sistemas Operativos": None,
    "Sistemas de Información Gerencial": None,
    "Metodología de Desarrollo de Software": None,
}

# Lista canónica ordenada de las 14 cátedras oficiales del eje
OFFICIAL_CATEDRAS_LIST = list(CATEDRA_BANNERS.keys())

def get_catedra_banner(materia_or_title: str | None) -> str | None:
    """
    Retorna la URL de la imagen de banner oficial para la cátedra especificada.
    Si aún no tiene imagen asignada, retorna None (dejando el banner vacío sin imágenes no relacionadas).
    """
    if not materia_or_title:
        return None

    clean = materia_or_title.strip()

    # Coincidencia exacta
    if clean in CATEDRA_BANNERS and CATEDRA_BANNERS[clean]:
        return CATEDRA_BANNERS[clean].strip()

    # Coincidencia insensible a mayúsculas o subcadena
    clean_lower = clean.lower()
    for cat_name, banner_url in CATEDRA_BANNERS.items():
        if banner_url and (cat_name.lower() in clean_lower or clean_lower in cat_name.lower()):
            return banner_url.strip()

    return None
