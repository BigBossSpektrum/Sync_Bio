STATUS_MAP = {
    0: "Entrada",
    1: "Salida",
    2: "Break Out",
    3: "Break In",
    4: "Overtime",
    15: "Desconocido",
}

TURNOS = {
    'diurno': {'inicio': 6, 'fin': 22},
    'nocturno': {'inicio': 22, 'fin': 6},
}

def interpretar_estado(codigo):
    return STATUS_MAP.get(codigo, f"Desconocido ({codigo})")

def detectar_turno(hora):
    if TURNOS['nocturno']['inicio'] <= hora or hora < TURNOS['nocturno']['fin']:
        return 'nocturno'
    return 'diurno'
