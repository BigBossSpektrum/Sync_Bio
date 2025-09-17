#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizador Biométrico - Servicio en Segundo Plano
====================================================
Este script funciona como un servicio que se ejecuta continuamente en segundo plano,
sincronizando datos del dispositivo biométrico con el servidor.

Características:
- Ejecución continua en segundo plano
- Sincronización automática cada N minutos
- Logging detallado
- Manejo de errores robusto
- Compatible con inicio automático de Windows
"""

import os
import sys
import json
import requests
import time
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import signal
import threading

# Variables globales
running = True
sync_thread = None

def setup_logging():
    """Configura el sistema de logging"""
    # Obtener directorio del script
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_file = os.path.join(app_dir, 'sync_service.log')
    
    # Configurar logging con rotación
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

def load_config():
    """Cargar configuración desde archivo JSON"""
    config_path = "../config/biometrico_config.json"
    default_config = {
        "SERVER_URL": "http://186.31.35.24:8000/api/recibir-datos-biometrico/",
        "TOKEN_API": None,
        "IP_BIOMETRICO": "192.168.1.88",
        "PUERTO_BIOMETRICO": 4370,
        "NOMBRE_ESTACION": "Centenario",
        "INTERVALO_MINUTOS": 5,
        "AUTO_START": False,
        "MINIMIZE_TO_TRAY": True
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Actualizar con valores por defecto si faltan
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            logging.warning(f"Archivo de configuración no encontrado: {config_path}")
            return default_config
    except Exception as e:
        logging.error(f"Error cargando configuración: {e}")
        return default_config

def sync_biometric_data(config):
    """Sincronizar datos del biométrico"""
    try:
        logging.info("🔄 Iniciando sincronización de datos biométricos...")
        
        # Validar configuración
        if not config.get("IP_BIOMETRICO"):
            raise Exception("IP del biométrico no configurada")
        
        if not config.get("SERVER_URL"):
            raise Exception("URL del servidor no configurada")
        
        # Importar módulos necesarios
        try:
            from zk import ZK
        except ImportError:
            logging.warning("Módulo 'zk' no disponible, usando simulación")
            return simulate_sync(config)
        
        # Conectar al dispositivo biométrico
        ip = config["IP_BIOMETRICO"]
        puerto = config["PUERTO_BIOMETRICO"]
        
        logging.info(f"📡 Conectando a biométrico {ip}:{puerto}...")
        
        zk = ZK(ip, port=puerto, timeout=5, password=0, force_udp=False, ommit_ping=False)
        conn = None
        
        try:
            conn = zk.connect()
            logging.info("✅ Conexión establecida con el biométrico")
            
            # Obtener registros de asistencia
            attendance = conn.get_attendance()
            logging.info(f"📊 Se obtuvieron {len(attendance)} registros")
            
            if len(attendance) == 0:
                logging.info("ℹ️ No hay registros nuevos para sincronizar")
                return True
            
            # Obtener usuarios para mapear nombres
            try:
                users = conn.get_users()
                user_dict = {user.uid: user.name for user in users}
                logging.info(f"👥 Se obtuvieron {len(users)} usuarios")
            except Exception as e:
                logging.warning(f"No se pudieron obtener usuarios: {e}")
                user_dict = {}
            
            # Procesar registros de asistencia
            datos_sync = []
            for record in attendance:
                try:
                    user_name = user_dict.get(record.uid, f"Usuario_{record.uid}")
                    
                    datos_sync.append({
                        "uid": record.uid,
                        "nombre": user_name,
                        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "dispositivo": config.get("NOMBRE_ESTACION", "Desconocido"),
                        "punch": record.punch,
                        "fecha": record.timestamp.strftime("%Y-%m-%d"),
                        "hora": record.timestamp.strftime("%H:%M:%S")
                    })
                except Exception as e:
                    logging.error(f"Error procesando registro {record}: {e}")
                    continue
            
            if not datos_sync:
                logging.warning("⚠️ No se pudieron procesar los registros")
                return False
            
            # Enviar datos al servidor
            success = send_data_to_server(datos_sync, config)
            if success:
                logging.info(f"✅ {len(datos_sync)} registros sincronizados exitosamente")
                return True
            else:
                logging.error("❌ Error enviando datos al servidor")
                return False
                
        finally:
            if conn:
                conn.disconnect()
                logging.info("🔌 Desconectado del biométrico")
                
    except Exception as e:
        logging.error(f"❌ Error en sincronización: {e}")
        return False

def simulate_sync(config):
    """Simular sincronización para pruebas"""
    logging.info("🎭 Ejecutando simulación de sincronización...")
    
    # Datos de prueba
    datos_sync = [{
        "uid": "test_001",
        "nombre": "Usuario Prueba",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dispositivo": config.get("NOMBRE_ESTACION", "Simulado"),
        "punch": 1,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S")
    }]
    
    # Enviar datos simulados
    success = send_data_to_server(datos_sync, config)
    if success:
        logging.info("✅ Simulación completada exitosamente")
        return True
    else:
        logging.error("❌ Error en simulación")
        return False

def send_data_to_server(datos, config):
    """Enviar datos al servidor"""
    try:
        server_url = config["SERVER_URL"]
        token = config.get("TOKEN_API")
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SincronizadorBiometrico/1.0"
        }
        
        if token:
            headers["Authorization"] = f"Token {token}"
        
        logging.info(f"📤 Enviando {len(datos)} registros al servidor...")
        
        response = requests.post(
            server_url,
            json=datos,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            logging.info("✅ Datos enviados exitosamente al servidor")
            return True
        else:
            logging.error(f"❌ Error del servidor: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error de conexión al servidor: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Error enviando datos: {e}")
        return False

def sync_loop(config):
    """Bucle principal de sincronización"""
    global running
    
    intervalo = config.get("INTERVALO_MINUTOS", 5) * 60  # Convertir a segundos
    logging.info(f"🔄 Iniciando bucle de sincronización (cada {config.get('INTERVALO_MINUTOS', 5)} minutos)")
    
    while running:
        try:
            # Ejecutar sincronización
            sync_biometric_data(config)
            
            # Esperar el intervalo especificado
            for _ in range(intervalo):
                if not running:
                    break
                time.sleep(1)
                
        except KeyboardInterrupt:
            logging.info("⚡ Interrupción del usuario detectada")
            break
        except Exception as e:
            logging.error(f"❌ Error en bucle de sincronización: {e}")
            time.sleep(60)  # Esperar 1 minuto antes de reintentar

def signal_handler(signum, frame):
    """Manejar señales del sistema"""
    global running
    logging.info(f"🛑 Señal {signum} recibida, cerrando aplicación...")
    running = False

def main():
    """Función principal"""
    global running, sync_thread
    
    # Configurar logging
    logger = setup_logging()
    logging.info("🚀 Iniciando Sincronizador Biométrico - Servicio en Segundo Plano")
    
    # Verificar argumentos
    if len(sys.argv) > 1 and sys.argv[1] == "--startup":
        logging.info("🔧 Iniciado desde startup de Windows")
    
    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Cargar configuración
        config = load_config()
        logging.info("⚙️ Configuración cargada correctamente")
        
        # Mostrar configuración (sin token)
        logging.info(f"📡 IP Biométrico: {config['IP_BIOMETRICO']}:{config['PUERTO_BIOMETRICO']}")
        logging.info(f"🏢 Estación: {config['NOMBRE_ESTACION']}")
        logging.info(f"⏱️ Intervalo: {config['INTERVALO_MINUTOS']} minutos")
        logging.info(f"🌐 Servidor: {config['SERVER_URL']}")
        
        # Iniciar hilo de sincronización
        sync_thread = threading.Thread(target=sync_loop, args=(config,))
        sync_thread.daemon = True
        sync_thread.start()
        
        logging.info("✅ Servicio iniciado correctamente")
        
        # Mantener el programa ejecutándose
        while running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("⚡ Interrupción del usuario")
    except Exception as e:
        logging.error(f"❌ Error crítico: {e}")
    finally:
        running = False
        if sync_thread and sync_thread.is_alive():
            sync_thread.join(timeout=5)
        logging.info("🏁 Servicio finalizado")

if __name__ == "__main__":
    main()
