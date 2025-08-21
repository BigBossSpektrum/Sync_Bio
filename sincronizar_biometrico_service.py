# sincronizar_biometrico_service.py
# Versión sin GUI para ejecutar como servicio/tarea programada

import os
import json
import requests
import logging
import time
import sys
from zk import ZK
from datetime import datetime

# ————— Configuración de logging para servicio —————
import os
import sys

# Obtener la ruta absoluta del directorio del script
if getattr(sys, 'frozen', False):
    # Si está ejecutándose como EXE compilado
    script_dir = os.path.dirname(sys.executable)
else:
    # Si está ejecutándose como script Python
    script_dir = os.path.dirname(os.path.abspath(__file__))

# Configurar la ruta del archivo de log
log_file_path = os.path.join(script_dir, 'biometrico_sync_service.log')

# Configurar logging con rotación de archivos
from logging.handlers import RotatingFileHandler

# Crear logger personalizado
logger = logging.getLogger('BiometricoSyncService')
logger.setLevel(logging.INFO)

# Limpiar handlers existentes para evitar duplicados
logger.handlers.clear()

# Handler para archivo con rotación (máximo 5 archivos de 10MB cada uno)
file_handler = RotatingFileHandler(
    log_file_path,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.info("🚀 Servicio de sincronización biométrica iniciado")
logger.info(f"📁 Directorio de trabajo: {script_dir}")
logger.info(f"📄 Archivo de log: {log_file_path}")
logger.info(f"💻 Ejecutándose como: {'EXE compilado' if getattr(sys, 'frozen', False) else 'Script Python'}")

# ————— Configuración —————
CONFIG_FILE = os.path.join(script_dir, 'biometrico_config.json')
SERVER_URL = "http://186.31.35.24:8000/api/recibir-datos-biometrico/"
TOKEN_API = None

# Configuración por defecto
default_config = {
    'IP_BIOMETRICO': '192.168.1.88',
    'PUERTO_BIOMETRICO': 4370,
    'NOMBRE_ESTACION': 'Centenario',
    'SERVER_URL': SERVER_URL,
    'TOKEN_API': TOKEN_API,
    'ENABLED': True
}

def load_config():
    """Cargar configuración desde archivo"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"✅ Configuración cargada desde {CONFIG_FILE}")
            return config
        else:
            logger.warning(f"⚠️ Archivo de configuración no encontrado, usando configuración por defecto")
            save_config(default_config)
            return default_config
    except Exception as e:
        logger.error(f"❌ Error cargando configuración: {e}")
        return default_config

def save_config(config):
    """Guardar configuración en archivo"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Configuración guardada en {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"❌ Error guardando configuración: {e}")

def conectar_dispositivo(ip, puerto=4370, timeout=30):
    """Conectar al dispositivo biométrico"""
    logger.info(f"🔌 Intentando conectar al dispositivo en {ip}:{puerto} (timeout: {timeout}s)")
    
    # Probar diferentes configuraciones de conexión
    configuraciones = [
        {'force_udp': False, 'ommit_ping': False},
        {'force_udp': True, 'ommit_ping': False},
        {'force_udp': False, 'ommit_ping': True},
        {'force_udp': True, 'ommit_ping': True}
    ]
    
    for i, config in enumerate(configuraciones, 1):
        try:
            logger.info(f"🔄 Intento {i}/4 - UDP: {config['force_udp']}, Ping: {not config['ommit_ping']}")
            zk = ZK(ip, port=puerto, timeout=timeout, **config)
            conn = zk.connect()
            
            # Probar la conexión obteniendo información del dispositivo
            firmware_version = conn.get_firmware_version()
            logger.info(f"✅ Conexión exitosa! Firmware: {firmware_version}")
            
            # Intentar deshabilitar el dispositivo temporalmente
            try:
                conn.disable_device()
                logger.info("🔒 Dispositivo deshabilitado temporalmente para sincronización")
            except Exception as disable_error:
                logger.warning(f"⚠️ No se pudo deshabilitar el dispositivo: {disable_error}")
            
            return conn
            
        except Exception as e:
            logger.warning(f"❌ Intento {i} fallido: {e}")
            if i < len(configuraciones):
                logger.info("⏳ Probando siguiente configuración...")
                time.sleep(2)
            continue
    
    logger.error(f"❌ Todos los intentos de conexión fallaron para {ip}:{puerto}")
    return None

def obtener_usuarios(conn):
    """Obtener usuarios del dispositivo"""
    try:
        logger.info("👥 Obteniendo usuarios...")
        usuarios = conn.get_users()
        return {u.user_id: u.name for u in usuarios}
    except Exception as e:
        logger.error(f"❌ Error al obtener usuarios: {e}")
        return {}

def obtener_registros_crudos(conn, nombre_estacion):
    """Obtener registros de asistencia del dispositivo"""
    logger.info("📄 Obteniendo registros de asistencia...")
    try:
        # Verificar que la conexión siga activa
        try:
            device_name = conn.get_device_name()
            logger.info(f"📱 Dispositivo: {device_name}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo obtener nombre del dispositivo: {e}")
        
        # Obtener registros de asistencia
        logger.info("📥 Llamando a get_attendance()...")
        registros = conn.get_attendance()
        logger.info("✅ get_attendance() completado")
        
        if not registros:
            logger.warning("⚠️ No hay registros de asistencia en el dispositivo")
            return []

        logger.info(f"📥 Se encontraron {len(registros)} registros de asistencia")
        
        # Obtener información de usuarios para mapear nombres
        logger.info("👥 Obteniendo mapeo de usuarios...")
        user_map = obtener_usuarios(conn)
        logger.info(f"👥 Se mapearon {len(user_map)} usuarios")
        
        logger.info("🔄 Procesando registros...")
        data = []
        for i, r in enumerate(registros):
            try:
                # Verificar progreso cada 10 registros
                if i > 0 and i % 10 == 0:
                    logger.info(f"🔄 Procesados {i}/{len(registros)} registros...")
                
                registro_data = {
                    'user_id': r.user_id,
                    'nombre': user_map.get(r.user_id, f"Usuario_{r.user_id}"),
                    'timestamp': r.timestamp.isoformat() if r.timestamp else None,
                    'status': r.status,
                    'estacion': nombre_estacion,
                    'punch': getattr(r, 'punch', 0)
                }
                data.append(registro_data)
                
                # Mostrar algunos ejemplos en el log
                if i < 3:
                    logger.info(f"🧪 Registro {i+1}: Usuario {registro_data['user_id']} - {registro_data['nombre']} - {registro_data['timestamp']}")
                    
            except Exception as reg_error:
                logger.error(f"❌ Error procesando registro {i}: {reg_error}")
                continue
        
        logger.info(f"✅ Se procesaron {len(data)} registros correctamente")
        return data
        
    except Exception as e:
        logger.error(f"❌ Error al obtener registros: {e}")
        import traceback
        logger.error(f"📋 Detalles del error: {traceback.format_exc()}")
        return []

def enviar_datos(data, server_url, token=None):
    """Enviar datos al servidor"""
    logger.info(f"📤 Enviando {len(data)} registros a {server_url}...")
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    try:
        resp = requests.post(server_url, json=data, headers=headers, timeout=30)
        logger.info(f"📨 Código de respuesta: {resp.status_code}")
        if resp.status_code == 200:
            logger.info("✅ Datos enviados correctamente")
            return True
        else:
            logger.warning(f"❌ Error en la respuesta del servidor: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error al enviar datos: {e}")
        return False

def ejecutar_sincronizacion():
    """Ejecutar un ciclo de sincronización"""
    logger.info("🚀 === INICIANDO CICLO DE SINCRONIZACIÓN ===")
    
    # Cargar configuración
    config = load_config()
    
    if not config.get('ENABLED', True):
        logger.info("⏸️ Sincronización deshabilitada en configuración")
        return True
    
    if not config.get('IP_BIOMETRICO') or not config.get('NOMBRE_ESTACION'):
        logger.error("❌ Configuración incompleta (falta IP o nombre de estación)")
        logger.error(f"   IP: '{config.get('IP_BIOMETRICO')}'")
        logger.error(f"   Estación: '{config.get('NOMBRE_ESTACION')}'")
        return False

    ip = config['IP_BIOMETRICO']
    puerto = config.get('PUERTO_BIOMETRICO', 4370)
    estacion = config['NOMBRE_ESTACION']
    server_url = config.get('SERVER_URL', SERVER_URL)
    token = config.get('TOKEN_API')
    
    logger.info(f"🎯 Objetivo: {ip}:{puerto}")
    logger.info(f"🏢 Estación: {estacion}")
    
    # Verificar conectividad básica
    try:
        import socket
        logger.info("🔍 Verificando conectividad TCP...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, puerto))
        sock.close()
        
        if result == 0:
            logger.info("✅ Puerto TCP accesible")
        else:
            logger.warning(f"⚠️ Puerto TCP no responde (código: {result})")
    except Exception as net_error:
        logger.warning(f"⚠️ Error verificando conectividad: {net_error}")

    logger.info("🔌 Estableciendo conexión con el dispositivo...")
    conn = conectar_dispositivo(ip, puerto)
    if not conn:
        logger.error("❌ No se pudo establecer conexión con el dispositivo")
        return False

    try:
        # Obtener información del dispositivo
        try:
            logger.info("📊 Obteniendo información del dispositivo...")
            users_count = len(conn.get_users() or [])
            logger.info(f"👥 Usuarios registrados en el dispositivo: {users_count}")
        except Exception as info_error:
            logger.warning(f"⚠️ No se pudo obtener información del dispositivo: {info_error}")

        # Obtener registros
        logger.info("📄 Iniciando obtención de registros...")
        try:
            regs = obtener_registros_crudos(conn, estacion)
            logger.info(f"📥 Obtención de registros completada: {len(regs)} registros")
        except Exception as reg_error:
            logger.error(f"❌ Error durante obtención de registros: {reg_error}")
            regs = []
        
        if regs:
            logger.info(f"📤 Preparando envío de {len(regs)} registros al servidor...")
            try:
                success = enviar_datos(regs, server_url, token)
                if success:
                    logger.info("✅ Envío de datos completado exitosamente")
                    return True
                else:
                    logger.error("❌ Falló el envío de datos")
                    return False
            except Exception as send_error:
                logger.error(f"❌ Error enviando datos: {send_error}")
                return False
        else:
            logger.info("🟡 No hay datos para enviar en este ciclo")
            return True
            
    except Exception as cycle_error:
        logger.error(f"❌ Error durante el ciclo de sincronización: {cycle_error}")
        import traceback
        logger.error(f"📋 Detalles del error: {traceback.format_exc()}")
        return False
        
    finally:
        try:
            logger.info("🔌 Cerrando conexión con el dispositivo...")
            conn.enable_device()
            conn.disconnect()
            logger.info("✅ Dispositivo habilitado y desconectado correctamente")
        except Exception as e:
            logger.error(f"❌ Error al desconectar: {e}")
        
        logger.info("🏁 Ciclo de sincronización completado")

if __name__ == '__main__':
    try:
        logger.info(f"🐍 Python {sys.version}")
        logger.info(f"📍 Argumentos: {sys.argv}")
        
        # Ejecutar sincronización
        success = ejecutar_sincronizacion()
        
        if success:
            logger.info("✅ Sincronización ejecutada exitosamente")
            sys.exit(0)
        else:
            logger.error("❌ La sincronización falló")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚡ Ejecución interrumpida por el usuario (Ctrl+C)")
        sys.exit(2)
    except Exception as e:
        logger.exception(f"❌ Error inesperado: {e}")
        sys.exit(3)
    finally:
        try:
            logger.info("🏁 Servicio finalizado")
            
            # Limpiar handlers de logging
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
                
        except Exception as final_error:
            try:
                print(f"Error en limpieza final: {final_error}")
            except:
                pass
