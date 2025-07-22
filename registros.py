from utils import detectar_turno
from calculos import determinar_tipo_registro
from datetime import datetime

def procesar_registros(registros):
    registros_por_usuario = {}

    for registro in registros:
        user_id = registro['user_id']
        registros_usuario = registros_por_usuario.get(user_id, [])

        # Determinar tipo (Entrada/Salida)
        tipo = determinar_tipo_registro(registro, registros_usuario)
        registro['tipo'] = tipo

        # Detectar turno
        hora = datetime.fromisoformat(registro['timestamp']).hour
        registro['turno'] = detectar_turno(hora)

        registros_usuario.append(registro)
        registros_por_usuario[user_id] = registros_usuario

    return [registro for registros_usuario in registros_por_usuario.values() for registro in registros_usuario]

def formatear_registros_para_envio(registros, estacion):
    """
    Prepara los registros para enviarlos al backend en el formato que el template espera.
    """
    datos_formateados = []
    registros_por_usuario = {}

    # Agrupar registros por usuario
    for r in registros:
        registros_por_usuario.setdefault(r['user_id'], []).append(r)

    for user_id, registros_usuario in registros_por_usuario.items():
        registros_usuario.sort(key=lambda r: r['timestamp'])
        entrada = None

        for reg in registros_usuario:
            timestamp = datetime.fromisoformat(reg['timestamp'])

            if reg.get('tipo') == 'Entrada':
                entrada = timestamp
                nombre = reg.get('nombre', 'N/A')
            elif reg.get('tipo') == 'Salida' and entrada:
                salida = timestamp
                nombre = reg.get('nombre', 'N/A')
                duracion = (salida - entrada).total_seconds() / 3600

                datos_formateados.append({
                    'usuario_id': user_id,
                    'nombre': nombre,
                    'cedula': None,  # La cédula la asigna el backend
                    'estacion': estacion,
                    'entrada': entrada.isoformat(),
                    'salida': salida.isoformat(),
                    'horas_trabajadas': round(duracion, 2),
                    'en_turno': False
                })
                entrada = None

        # Si quedó entrada sin salida
        if entrada:
            datos_formateados.append({
                'usuario_id': user_id,
                'nombre': nombre,
                'cedula': None,  # La cédula la asigna el backend
                'estacion': estacion,
                'entrada': entrada.isoformat(),
                'salida': None,
                'horas_trabajadas': None,
                'en_turno': True
            })

    return datos_formateados