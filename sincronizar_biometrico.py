import os
import json
import requests
import logging
from zk import ZK
from dotenv import load_dotenv
from datetime import datetime

# Configuración de logging
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
logger.info("🚀 Iniciando script de sincronización biométrica sin procesamiento")

DEFAULT_PORT = 4370
SERVER_URL = "http://186.31.35.24:8000/api/recibir-datos-biometrico/"

def conectar_dispositivo(ip, puerto=DEFAULT_PORT, timeout=10):
    logger.info(f"🔌 Intentando conectar al dispositivo biométrico en {ip}:{puerto}")
    zk = ZK(ip, port=puerto, timeout=timeout, force_udp=False, ommit_ping=False)
    try:
        conn = zk.connect()
        conn.disable_device()
        logger.info("✅ Conectado y dispositivo deshabilitado temporalmente")
        return conn
    except Exception as e:
        logger.error(f"❌ Error al conectar: {str(e)}")
        return None

def obtener_usuarios(conn):
    try:
        logger.info("👥 Obteniendo lista de usuarios del dispositivo...")
        usuarios = conn.get_users()
        user_map = {u.user_id: u.name for u in usuarios}
        logger.info(f"✅ Usuarios obtenidos: {len(user_map)}")
        return user_map
    except Exception as e:
        logger.error(f"❌ Error al obtener usuarios: {str(e)}")
        return {}

def obtener_registros_crudos(conn, nombre_estacion):
    logger.info("📄 Obteniendo registros RAW del dispositivo...")

    try:
        registros_biometrico = conn.get_attendance()
        logger.info(f"📥 Registros obtenidos: {len(registros_biometrico)}")

        if not registros_biometrico:
            logger.warning("⚠️ No hay registros en el dispositivo")
            return []

        user_map = obtener_usuarios(conn)

        data = []
        for i, record in enumerate(registros_biometrico):
            user_id = record.user_id
            registro = {
                'user_id': user_id,
                'nombre': user_map.get(user_id, "Desconocido"),  # 🧠 Nombre incluido
                'timestamp': record.timestamp.isoformat(),
                'status': record.status,
                'estacion': nombre_estacion
            }
            data.append(registro)

            if i < 3:
                logger.debug(f"Ejemplo registro: {registro}")

        return data

    except Exception as e:
        logger.error(f"❌ Error al obtener registros: {str(e)}")
        return []

def enviar_datos(data, token=None):
    logger.info(f"📤 Enviando {len(data)} registros al servidor")
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'

    print("\n📦 Datos que se enviarán al servidor:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    try:
        response = requests.post(SERVER_URL, json=data, headers=headers, timeout=10)

        print(f"\n📨 Respuesta del servidor: {response.status_code}")
        print("📨 Contenido de respuesta:")
        print(response.text)

        if response.status_code == 200:
            logger.info("✅ Envío exitoso")
        else:
            logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")

    except Exception as e:
        logger.error(f"❌ Error al enviar datos: {str(e)}")
        print(f"❌ Excepción al enviar datos: {str(e)}")

def main():
    ip = os.getenv('IP_BIOMETRICO')
    puerto = int(os.getenv('PUERTO_BIOMETRICO', DEFAULT_PORT))
    nombre_estacion = os.getenv('NOMBRE_ESTACION')
    token_api = os.getenv('TOKEN_API')

    if not ip or not nombre_estacion:
        logger.error("❌ Faltan variables de entorno: IP_BIOMETRICO o NOMBRE_ESTACION")
        return

    conn = conectar_dispositivo(ip, puerto)
    if not conn:
        return

    registros = obtener_registros_crudos(conn, nombre_estacion)
    if registros:
        enviar_datos(registros, token_api)
    else:
        logger.info("🟡 No hay datos para enviar")

    try:
        conn.enable_device()
        conn.disconnect()
        logger.info("🔌 Dispositivo habilitado y desconectado correctamente")
    except Exception as e:
        logger.error(f"❌ Error al cerrar conexión: {str(e)}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⚡ Proceso interrumpido por el usuario")
    except Exception as e:
        logger.critical(f"❌ Error crítico: {str(e)}")
    finally:
        logger.info("🏁 Finalizando script")
