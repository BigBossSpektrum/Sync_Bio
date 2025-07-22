import os
import json
import requests
import logging
from datetime import datetime
from zk import ZK
from dotenv import load_dotenv

# Importación de utilitarios, registros y cálculos
from utils import interpretar_estado, detectar_turno
from registros import procesar_registros
from calculos import determinar_tipo_registro, calcular_horas_usuario

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('biometrico_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("🚀 Iniciando script de sincronización biométrica")

DEFAULT_PORT = 4370
SERVER_URL = "http://186.31.35.24:8000/api/recibir-datos-biometrico/"


def conectar_dispositivo(ip, puerto=DEFAULT_PORT, timeout=10):
    logger.info(f"🔌 Intentando conectar al dispositivo biométrico en {ip}:{puerto}")
    zk = ZK(ip, port=puerto, timeout=timeout, force_udp=False, ommit_ping=False)
    try:
        logger.info("🔄 Estableciendo conexión...")
        conn = zk.connect()
        conn.disable_device()
        logger.info(f"✅ Conectado exitosamente al biométrico en {ip}:{puerto}")
        return conn
    except Exception as e:
        logger.error(f"❌ Error al conectar al dispositivo {ip}:{puerto} - {str(e)}")
        return None


def obtener_registros(conn, estacion):
    logger.info(f"📄 Obteniendo registros de asistencia de la estación: {estacion}")
    try:
        registros_biometrico = conn.get_attendance()
        logger.info(f"📥 Total registros leídos: {len(registros_biometrico)}")

        if not registros_biometrico:
            logger.warning("⚠️ No se encontraron registros en el dispositivo")
            return []

        usuarios_biometrico = {user.user_id: user.name for user in conn.get_users()}
        registros = []
        for i, record in enumerate(registros_biometrico):
            nombre = usuarios_biometrico.get(record.user_id, "Desconocido")
            registro = {
                'user_id': record.user_id,
                'nombre': nombre,
                'timestamp': record.timestamp.isoformat(),
                'estado': interpretar_estado(record.status)
            }
            registros.append(registro)

            if i < 3:
                logger.debug(f"Registro procesado: {registro}")

        logger.info(f"✅ Procesados {len(registros)} registros correctamente")
        return registros

    except Exception as e:
        logger.error(f"❌ Error al obtener registros: {str(e)}")
        return []


def enviar_al_servidor(data, token=None):
    logger.info(f"🚀 Preparando envío de {len(data)} registros al servidor")
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'

    try:
        logger.info("📤 Enviando datos al servidor...")
        response = requests.post(SERVER_URL, json=data, headers=headers, timeout=10)
        logger.info(f"📊 Respuesta del servidor: Status {response.status_code}")

        if response.status_code == 200:
            logger.info("✅ Datos enviados correctamente al servidor")
        else:
            logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"❌ Error al enviar datos al servidor: {str(e)}")


def main():
    logger.info("🔧 Iniciando función principal")
    ip_biometrico = os.getenv('IP_BIOMETRICO')
    puerto_biometrico = os.getenv('PUERTO_BIOMETRICO', DEFAULT_PORT)
    nombre_estacion = os.getenv('NOMBRE_ESTACION')
    token_api = os.getenv('TOKEN_API')

    if not ip_biometrico or not nombre_estacion:
        logger.error("❌ Configuración faltante en .env")
        return

    conn = conectar_dispositivo(ip_biometrico, int(puerto_biometrico))
    if not conn:
        logger.error("❌ No se pudo establecer conexión con el dispositivo biométrico")
        return

    registros = obtener_registros(conn, nombre_estacion)

    if registros:
        logger.info(f"🔄 Procesando registros para jornada y cálculo de horas...")
        procesados = procesar_registros(registros)

        logger.info("📊 Cálculo de horas por usuario:")
        for user_id in set(r['user_id'] for r in procesados):
            resumen = calcular_horas_usuario(user_id, procesados)
            logger.info(f"Usuario {user_id}: {json.dumps(resumen, indent=2, ensure_ascii=False)}")

        enviar_al_servidor(procesados, token=token_api)
    else:
        logger.warning("⚠️ No se encontraron registros para procesar ni enviar")

    try:
        conn.enable_device()
        conn.disconnect()
        logger.info("✅ Dispositivo habilitado y desconectado correctamente")
    except Exception as e:
        logger.error(f"❌ Error al cerrar conexión: {str(e)}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⚡ Proceso interrumpido por el usuario")
    except Exception as e:
        logger.critical(f"❌ Error crítico en el programa principal: {str(e)}")
    finally:
        logger.info("🏁 Finalizando script de sincronización biométrica")
