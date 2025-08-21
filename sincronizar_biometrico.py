import os
import json
import requests
from zk import ZK
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
print("🚀 Iniciando script de sincronización biométrica")

DEFAULT_PORT = 4370
SERVER_URL = "http://186.31.35.24:8000/api/recibir-datos-biometrico/"

def conectar_dispositivo(ip, puerto=DEFAULT_PORT, timeout=10):
    print(f"🔌 Conectando al dispositivo en {ip}:{puerto}")
    zk = ZK(ip, port=puerto, timeout=timeout, force_udp=False, ommit_ping=False)
    try:
        conn = zk.connect()
        conn.disable_device()
        print("✅ Dispositivo conectado y deshabilitado temporalmente")
        return conn
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def obtener_usuarios(conn):
    try:
        print("👥 Obteniendo usuarios...")
        usuarios = conn.get_users()
        return {u.user_id: u.name for u in usuarios}
    except Exception as e:
        print(f"❌ Error al obtener usuarios: {e}")
        return {}

def obtener_registros_crudos(conn, nombre_estacion):
    print("📄 Obteniendo registros...")
    try:
        registros = conn.get_attendance()
        if not registros:
            print("⚠️ No hay registros nuevos")
            return []

        print(f"📥 Registros obtenidos: {len(registros)}")
        user_map = obtener_usuarios(conn)
        data = []

        for i, r in enumerate(registros):
            data.append({
                'user_id': r.user_id,
                'nombre': user_map.get(r.user_id, "Desconocido"),
                'timestamp': r.timestamp.isoformat(),
                'status': r.status,
                'estacion': nombre_estacion
            })
            if i < 3:
                print(f"🧪 Ejemplo: {data[-1]}")

        return data
    except Exception as e:
        print(f"❌ Error al obtener registros: {e}")
        return []

def enviar_datos(data, token=None):
    print(f"📤 Enviando {len(data)} registros...")
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'

    try:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        resp = requests.post(SERVER_URL, json=data, headers=headers, timeout=10)
        print(f"📨 Código de respuesta: {resp.status_code}")
        print(f"📨 Contenido: {resp.text}")
        if resp.status_code == 200:
            print("✅ Datos enviados correctamente")
        else:
            print("❌ Error en la respuesta del servidor")
    except Exception as e:
        print(f"❌ Error al enviar datos: {e}")

def main():
    ip = os.getenv('IP_BIOMETRICO')
    puerto = int(os.getenv('PUERTO_BIOMETRICO', DEFAULT_PORT))
    nombre_estacion = os.getenv('NOMBRE_ESTACION')
    token_api = os.getenv('TOKEN_API')

    if not ip or not nombre_estacion:
        print("❌ Variables de entorno incompletas")
        return

    conn = conectar_dispositivo(ip, puerto)
    if not conn:
        return

    try:
        registros = obtener_registros_crudos(conn, nombre_estacion)
        if registros:
            enviar_datos(registros, token_api)
        else:
            print("🟡 Sin datos para enviar")
    finally:
        try:
            conn.enable_device()
            conn.disconnect()
            print("🔌 Dispositivo habilitado y desconectado")
        except Exception as e:
            print(f"❌ Error al desconectar: {e}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("⚡ Ejecución interrumpida por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    finally:
        print("🏁 Script finalizado")
