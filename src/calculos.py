from datetime import datetime

def calcular_horas_usuario(user_id, registros):
    registros_usuario = [r for r in registros if r['user_id'] == user_id]
    registros_usuario.sort(key=lambda x: x['timestamp'])

    entrada = None
    total_horas = 0
    detalle = []

    for reg in registros_usuario:
        timestamp = datetime.fromisoformat(reg['timestamp'])

        if reg.get('tipo') == 'Entrada':
            entrada = timestamp
        elif reg.get('tipo') == 'Salida' and entrada:
            salida = timestamp
            duracion = (salida - entrada).total_seconds() / 3600
            detalle.append({
                'entrada': entrada.isoformat(),
                'salida': salida.isoformat(),
                'horas': round(duracion, 2)
            })
            total_horas += duracion
            entrada = None  # reset

    return {
        'usuario_id': str(user_id),
        'total_horas': round(total_horas, 2),
        'detalle': detalle
    }

def determinar_tipo_registro(registro, registros_usuario):
    """
    Determina si el registro actual es una entrada o una salida
    basándose en el último tipo de registro previo.
    """
    registros_anteriores = [r for r in registros_usuario if r['timestamp'] < registro['timestamp']]
    registros_anteriores.sort(key=lambda r: r['timestamp'], reverse=True)

    if not registros_anteriores:
        return 'Entrada'  # No hay registros previos

    ultimo_tipo = registros_anteriores[0]['tipo']
    return 'Salida' if ultimo_tipo == 'Entrada' else 'Entrada'