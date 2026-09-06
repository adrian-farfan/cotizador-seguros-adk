CATALOGO = [
    {
        "nombre": "Seguro Vida Básico",
        "tipo": "vida",
        "edad_min": 18,
        "edad_max": 65,
        "requiere_auto": False,
        "condiciones_excluidas": [],
    },
    {
        "nombre": "Seguro Vehicular Full",
        "tipo": "auto",
        "edad_min": 18,
        "edad_max": 70,
        "requiere_auto": True,
        "condiciones_excluidas": [],
    },
    {
        "nombre": "Seguro Salud Senior",
        "tipo": "salud",
        "edad_min": 60,
        "edad_max": 99,
        "requiere_auto": False,
        "condiciones_excluidas": [],
    },
    {
        "nombre": "Seguro Salud Joven",
        "tipo": "salud",
        "edad_min": 18,
        "edad_max": 59,
        "requiere_auto": False,
        "condiciones_excluidas": [],
    },
    {
        "nombre": "Seguro Vida Plus",
        "tipo": "vida",
        "edad_min": 18,
        "edad_max": 80,
        "requiere_auto": False,
        "condiciones_excluidas": ["diabetes"],
    },
]


def consultar_catalogo(edad: int, tiene_auto: bool, condiciones: list[str]) -> list[dict]:
    """Devuelve los productos de seguro que aplican a la situación de una persona.

    Args:
        edad: edad de la persona en años.
        tiene_auto: True si la persona posee un vehículo propio.
        condiciones: condiciones de salud que tiene la persona, ej. ["diabetes"].
            Lista vacía si no tiene ninguna.

    Returns:
        Los productos del catálogo cuyo rango de edad incluye a la persona,
        que no requieren auto si la persona no tiene uno, y que no excluyen
        ninguna de sus condiciones de salud.
    """
    resultados = []
    for producto in CATALOGO:
        if not (producto["edad_min"] <= edad <= producto["edad_max"]):
            continue
        if producto["requiere_auto"] and not tiene_auto:
            continue
        if any(c in producto["condiciones_excluidas"] for c in condiciones):
            continue
        resultados.append(producto)
    return resultados
