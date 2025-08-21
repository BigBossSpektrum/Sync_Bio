# sincronizador_biometrico_mejorado.py

import os
import json
import requests
import logging
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from zk import ZK
from datetime import datetime
import socket
import subprocess
import pystray
from PIL import Image, ImageDraw
import sys

# ————— Configuración de logging mejorada —————
def setup_logging():
    """Configura el sistema de logging con rotación de archivos"""
    from logging.handlers import RotatingFileHandler
    
    # Obtener directorio del ejecutable o script
    if getattr(sys, 'frozen', False):
        # Si es un ejecutable compilado
        app_dir = os.path.dirname(sys.executable)
    else:
        # Si es un script de Python
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Intentar crear directorio de logs dentro del directorio de la aplicación
    log_dir = os.path.join(app_dir, "logs")
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = os.path.join(log_dir, 'biometrico_sync.log')
    except (OSError, PermissionError):
        # Si no se puede crear en logs/, usar directorio de la aplicación
        log_file_path = os.path.join(app_dir, 'biometrico_sync.log')
        print(f"⚠️ No se pudo crear directorio logs, usando: {log_file_path}")
    
    # Configurar el logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para archivo con rotación
    try:
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        print(f"✅ Logging configurado correctamente: {log_file_path}")
    except Exception as e:
        print(f"❌ Error configurando file logging: {e}")
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

# Inicializar logging
logger = setup_logging()
logging.info("INICIO: Script de sincronizacion biometrica mejorado iniciado")

# ————— Función para obtener ruta de logs —————
def get_log_file_path():
    """Obtiene la ruta del archivo de log actual"""
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_dir = os.path.join(app_dir, "logs")
    if os.path.exists(log_dir):
        return os.path.join(log_dir, 'biometrico_sync.log')
    else:
        return os.path.join(app_dir, 'biometrico_sync.log')

# ————— Configuración por defecto —————
DEFAULT_CONFIG = {
    'SERVER_URL': "http://186.31.35.24:8000/api/recibir-datos-biometrico/",
    'TOKEN_API': None,
    'IP_BIOMETRICO': '192.168.1.88',
    'PUERTO_BIOMETRICO': 4370,
    'NOMBRE_ESTACION': 'Centenario',
    'INTERVALO_MINUTOS': 5,
    'AUTO_START': False,
    'MINIMIZE_TO_TRAY': True
}

# Variables globales
config_data = DEFAULT_CONFIG.copy()
config_data['sync_running'] = False

# ————— Funciones de configuración —————
def load_config():
    """Carga la configuración desde archivo"""
    try:
        if os.path.exists('biometrico_config.json'):
            with open('biometrico_config.json', 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                config_data.update(loaded_config)
                logging.info("CONFIG: Configuracion cargada desde archivo")
        else:
            logging.info("CONFIG: Usando configuracion por defecto")
    except Exception as e:
        logging.error(f"ERROR: Error cargando configuracion: {e}")

def save_config():
    """Guarda la configuración actual en archivo"""
    try:
        # Crear una copia sin datos temporales
        config_to_save = {k: v for k, v in config_data.items() 
                         if k not in ['sync_running']}
        
        with open('biometrico_config.json', 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, indent=2, ensure_ascii=False)
        logging.info("CONFIG: Configuracion guardada")
    except Exception as e:
        logging.error(f"ERROR: Error guardando configuracion: {e}")

# ————— Funciones de pruebas de conexión —————
def test_ping(ip, timeout=5):
    """Prueba ping básico"""
    try:
        logging.info(f"PING: Probando ping a {ip}...")
        result = subprocess.run(['ping', '-n', '1', '-w', str(timeout*1000), ip], 
                              capture_output=True, text=True, timeout=timeout+2)
        
        if result.returncode == 0:
            # Extraer tiempo de respuesta
            output = result.stdout
            if "tiempo=" in output:
                time_part = output.split("tiempo=")[1].split("ms")[0]
                logging.info(f"OK: Ping exitoso - Tiempo: {time_part}ms")
                return True, f"Ping exitoso - {time_part}ms"
            else:
                logging.info("OK: Ping exitoso")
                return True, "Ping exitoso"
        else:
            logging.warning(f"WARNING: Ping fallo - codigo: {result.returncode}")
            return False, f"Ping falló - código: {result.returncode}"
            
    except subprocess.TimeoutExpired:
        logging.warning("WARNING: Ping timeout")
        return False, "Ping timeout"
    except Exception as e:
        logging.warning(f"WARNING: Error en ping: {e}")
        return False, f"Error en ping: {e}"

def test_tcp_port(ip, puerto, timeout=10):
    """Prueba conectividad TCP"""
    try:
        logging.info(f"TCP: Probando puerto TCP {ip}:{puerto}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start_time = time.time()
        result = sock.connect_ex((ip, puerto))
        end_time = time.time()
        sock.close()
        
        if result == 0:
            response_time = int((end_time - start_time) * 1000)
            logging.info(f"OK: Puerto TCP accesible - Tiempo: {response_time}ms")
            return True, f"Puerto accesible - {response_time}ms"
        else:
            logging.warning(f"WARNING: Puerto TCP inaccesible - codigo: {result}")
            return False, f"Puerto inaccesible - código: {result}"
            
    except socket.timeout:
        logging.warning("WARNING: Timeout en conexion TCP")
        return False, "Timeout en conexión TCP"
    except Exception as e:
        logging.warning(f"WARNING: Error en prueba TCP: {e}")
        return False, f"Error TCP: {e}"

def conectar_dispositivo(ip, puerto=4370, timeout=30):
    """Conecta con el dispositivo biométrico usando múltiples configuraciones"""
    logging.info(f"DEVICE: Intentando conectar al dispositivo en {ip}:{puerto} (timeout: {timeout}s)")
    
    # Probar diferentes configuraciones de conexión
    configuraciones = [
        {'force_udp': False, 'ommit_ping': False, 'nombre': 'TCP con ping'},
        {'force_udp': True, 'ommit_ping': False, 'nombre': 'UDP con ping'},
        {'force_udp': False, 'ommit_ping': True, 'nombre': 'TCP sin ping'},
        {'force_udp': True, 'ommit_ping': True, 'nombre': 'UDP sin ping'}
    ]
    
    for i, config in enumerate(configuraciones, 1):
        try:
            logging.info(f"CONN: Intento {i}/4 - {config['nombre']}")
            
            # Crear conexión ZK con la configuración actual
            zk_config = {k: v for k, v in config.items() if k != 'nombre'}
            zk = ZK(ip, port=puerto, timeout=timeout, **zk_config)
            
            # Intentar conectar
            conn = zk.connect()
            
            # Probar la conexión obteniendo información del dispositivo
            firmware_version = conn.get_firmware_version()
            logging.info(f"OK: Conexion exitosa! Firmware: {firmware_version}")
            
            # Intentar deshabilitar el dispositivo temporalmente
            try:
                conn.disable_device()
                logging.info("DEVICE: Dispositivo deshabilitado temporalmente para sincronizacion")
            except Exception as disable_error:
                logging.warning(f"WARNING: No se pudo deshabilitar el dispositivo: {disable_error}")
                # Continuar sin deshabilitar
            
            return conn
            
        except Exception as e:
            logging.warning(f"ERROR: Intento {i} ({config['nombre']}) fallido: {e}")
            if i < len(configuraciones):
                logging.info("⏳ Probando siguiente configuración...")
                time.sleep(2)
            continue
    
    logging.error(f"❌ Todos los intentos de conexión fallaron para {ip}:{puerto}")
    return None

def test_device_connection(ip, puerto):
    """Prueba completa de conexión con el dispositivo"""
    logging.info(f"🧪 === INICIANDO PRUEBA COMPLETA DE CONEXIÓN ===")
    logging.info(f"🎯 Destino: {ip}:{puerto}")
    
    results = {}
    
    # Prueba 1: Ping
    ping_success, ping_msg = test_ping(ip)
    results['ping'] = {'success': ping_success, 'message': ping_msg}
    
    # Prueba 2: Puerto TCP
    tcp_success, tcp_msg = test_tcp_port(ip, puerto)
    results['tcp'] = {'success': tcp_success, 'message': tcp_msg}
    
    # Prueba 3: Conexión ZK
    device_info = {}
    conn = conectar_dispositivo(ip, puerto, timeout=30)
    if conn:
        try:
            # Obtener información del dispositivo
            device_info['name'] = conn.get_device_name()
            device_info['firmware'] = conn.get_firmware_version()
            device_info['serial'] = getattr(conn, 'get_serialnumber', lambda: 'N/A')()
            
            # Obtener estadísticas
            users = conn.get_users()
            device_info['users_count'] = len(users) if users else 0
            
            registros = conn.get_attendance()
            device_info['records_count'] = len(registros) if registros else 0
            
            # Log de información obtenida
            logging.info(f"📱 Dispositivo: {device_info['name']}")
            logging.info(f"🔧 Firmware: {device_info['firmware']}")
            logging.info(f"🆔 Serie: {device_info['serial']}")
            logging.info(f"👥 Usuarios registrados: {device_info['users_count']}")
            logging.info(f"📄 Registros de asistencia: {device_info['records_count']}")
            
            results['device'] = {'success': True, 'info': device_info}
            logging.info("✅ === PRUEBA COMPLETA EXITOSA ===")
            
        except Exception as info_error:
            logging.warning(f"⚠️ Error obteniendo información del dispositivo: {info_error}")
            results['device'] = {'success': False, 'error': str(info_error)}
        finally:
            try:
                conn.enable_device()
                conn.disconnect()
            except:
                pass
    else:
        results['device'] = {'success': False, 'error': 'No se pudo conectar'}
        logging.error("❌ === PRUEBA COMPLETA FALLIDA ===")
    
    return results

# ————— Funciones de sincronización (conservadas del script original) —————
def obtener_usuarios(conn):
    try:
        logging.info("👥 Obteniendo usuarios...")
        usuarios = conn.get_users()
        return {u.user_id: u.name for u in usuarios}
    except Exception as e:
        logging.error(f"❌ Error al obtener usuarios: {e}")
        return {}

def obtener_registros_crudos(conn, nombre_estacion):
    logging.info("📄 Obteniendo registros de asistencia...")
    try:
        # Verificar que la conexión siga activa
        try:
            device_name = conn.get_device_name()
            logging.info(f"📱 Dispositivo: {device_name}")
        except Exception as e:
            logging.warning(f"⚠️ No se pudo obtener nombre del dispositivo: {e}")
        
        # Obtener registros de asistencia
        logging.info("📥 Llamando a get_attendance()...")
        registros = conn.get_attendance()
        logging.info("✅ get_attendance() completado")
        
        if not registros:
            logging.warning("⚠️ No hay registros de asistencia en el dispositivo")
            return []

        logging.info(f"📥 Se encontraron {len(registros)} registros de asistencia")
        
        # Obtener información de usuarios para mapear nombres
        logging.info("👥 Obteniendo mapeo de usuarios...")
        user_map = obtener_usuarios(conn)
        logging.info(f"👥 Se mapearon {len(user_map)} usuarios")
        
        logging.info("🔄 Procesando registros...")
        data = []
        for i, r in enumerate(registros):
            try:
                # Verificar progreso cada 10 registros
                if i > 0 and i % 10 == 0:
                    logging.info(f"🔄 Procesados {i}/{len(registros)} registros...")
                
                registro_data = {
                    'user_id': r.user_id,
                    'nombre': user_map.get(r.user_id, f"Usuario_{r.user_id}"),
                    'timestamp': r.timestamp.isoformat() if r.timestamp else None,
                    'status': r.status,
                    'estacion': nombre_estacion,
                    'punch': getattr(r, 'punch', 0)  # Tipo de marcaje si está disponible
                }
                data.append(registro_data)
                
                # Mostrar algunos ejemplos en el log
                if i < 5:
                    logging.info(f"🧪 Registro {i+1}: Usuario {registro_data['user_id']} - {registro_data['nombre']} - {registro_data['timestamp']}")
                    
            except Exception as reg_error:
                logging.error(f"❌ Error procesando registro {i}: {reg_error}")
                continue
        
        logging.info(f"✅ Se procesaron {len(data)} registros correctamente")
        return data
        
    except Exception as e:
        logging.error(f"❌ Error al obtener registros: {e}")
        import traceback
        logging.error(f"📋 Detalles del error: {traceback.format_exc()}")
        return []

def enviar_datos(data, server_url, token=None):
    logging.info(f"📤 Enviando {len(data)} registros a {server_url}...")
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    try:
        resp = requests.post(server_url, json=data, headers=headers, timeout=30)
        logging.info(f"📨 Código de respuesta: {resp.status_code}")
        if resp.status_code == 200:
            logging.info("✅ Datos enviados correctamente")
            return True
        else:
            logging.warning(f"❌ Error en la respuesta del servidor: {resp.text}")
            return False
    except Exception as e:
        logging.error(f"❌ Error al enviar datos: {e}")
        return False

def main_cycle():
    """Ciclo principal de sincronización"""
    if not config_data['IP_BIOMETRICO'] or not config_data['NOMBRE_ESTACION']:
        logging.error("❌ Configuración incompleta (falta IP o nombre de estación)")
        return False

    logging.info(f"🚀 Iniciando ciclo de sincronización para {config_data['NOMBRE_ESTACION']}")
    logging.info(f"🎯 Objetivo: {config_data['IP_BIOMETRICO']}:{config_data['PUERTO_BIOMETRICO']}")
    
    # Verificar conectividad básica
    tcp_success, tcp_msg = test_tcp_port(config_data['IP_BIOMETRICO'], config_data['PUERTO_BIOMETRICO'])
    if not tcp_success:
        logging.warning(f"⚠️ Problema de conectividad: {tcp_msg}")

    logging.info("🔌 Estableciendo conexión con el dispositivo...")
    conn = conectar_dispositivo(config_data['IP_BIOMETRICO'], config_data['PUERTO_BIOMETRICO'])
    if not conn:
        logging.error("❌ No se pudo establecer conexión con el dispositivo")
        return False

    try:
        # Obtener información del dispositivo
        try:
            logging.info("📊 Obteniendo información del dispositivo...")
            users_count = len(conn.get_users() or [])
            logging.info(f"👥 Usuarios registrados en el dispositivo: {users_count}")
        except Exception as info_error:
            logging.warning(f"⚠️ No se pudo obtener información del dispositivo: {info_error}")

        # Obtener registros
        logging.info("📄 Iniciando obtención de registros...")
        try:
            regs = obtener_registros_crudos(conn, config_data['NOMBRE_ESTACION'])
            logging.info(f"📥 Obtención de registros completada: {len(regs)} registros")
        except Exception as reg_error:
            logging.error(f"❌ Error durante obtención de registros: {reg_error}")
            regs = []
        
        success = True
        if regs:
            logging.info(f"📤 Preparando envío de {len(regs)} registros al servidor...")
            try:
                success = enviar_datos(regs, config_data['SERVER_URL'], config_data['TOKEN_API'])
                if success:
                    logging.info("✅ Envío de datos completado")
                else:
                    logging.error("❌ Error en el envío de datos")
            except Exception as send_error:
                logging.error(f"❌ Error enviando datos: {send_error}")
                success = False
        else:
            logging.info("🟡 No hay datos para enviar en este ciclo")
            
        return success
            
    except Exception as cycle_error:
        logging.error(f"❌ Error durante el ciclo de sincronización: {cycle_error}")
        import traceback
        logging.error(f"📋 Detalles del error: {traceback.format_exc()}")
        return False
        
    finally:
        try:
            logging.info("🔌 Cerrando conexión con el dispositivo...")
            conn.enable_device()
            conn.disconnect()
            logging.info("✅ Dispositivo habilitado y desconectado correctamente")
        except Exception as e:
            logging.error(f"❌ Error al desconectar: {e}")
        
        logging.info("🏁 Ciclo de sincronización completado")

def sync_worker():
    """Worker que ejecuta la sincronización automática"""
    try:
        logging.info("🔄 Worker de sincronización iniciado")
        
        # Ejecutar primer ciclo inmediatamente
        if config_data['sync_running']:
            try:
                logging.info("🚀 === INICIANDO PRIMER CICLO DE SINCRONIZACIÓN ===")
                start_time = time.time()
                
                success = main_cycle()
                
                end_time = time.time()
                duration = end_time - start_time
                if success:
                    logging.info(f"⏱️ Primer ciclo completado exitosamente en {duration:.2f} segundos")
                else:
                    logging.warning(f"⏱️ Primer ciclo completado con errores en {duration:.2f} segundos")
            except Exception as e:
                logging.exception(f"❌ Error en primer ciclo: {e}")
        
        # Continuar con ciclos periódicos
        while config_data['sync_running']:
            try:
                intervalo = config_data.get('INTERVALO_MINUTOS', 5)
                logging.info(f"⏱️ Esperando {intervalo} minutos para la siguiente ejecución...")
                
                # Dividir la espera en pequeños intervalos para poder detener el hilo
                total_seconds = intervalo * 60
                for i in range(total_seconds):
                    if not config_data['sync_running']:
                        logging.info("🛑 Sincronización detenida durante la espera")
                        return  # Salir del worker completamente
                    
                    # Log cada minuto durante la espera
                    if i > 0 and i % 60 == 0:
                        remaining_minutes = (total_seconds - i) // 60
                        logging.info(f"⏳ Esperando... {remaining_minutes} minutos restantes")
                    
                    time.sleep(1)
                
                # Si aún está corriendo, ejecutar siguiente ciclo
                if config_data['sync_running']:
                    logging.info("🚀 === INICIANDO NUEVO CICLO DE SINCRONIZACIÓN ===")
                    start_time = time.time()
                    
                    try:
                        success = main_cycle()
                        
                        end_time = time.time()
                        duration = end_time - start_time
                        if success:
                            logging.info(f"⏱️ Ciclo completado exitosamente en {duration:.2f} segundos")
                        else:
                            logging.warning(f"⏱️ Ciclo completado con errores en {duration:.2f} segundos")
                    except Exception as cycle_error:
                        logging.exception(f"❌ Error en ciclo de sincronización: {cycle_error}")
                        # Continuar con el siguiente ciclo después del error
                    
            except Exception as e:
                logging.exception(f"❌ Error inesperado en el bucle principal: {e}")
                if config_data['sync_running']:
                    logging.info(f"⏱️ Reiniciando en {config_data.get('INTERVALO_MINUTOS', 5)} minutos...")
                    # Esperar antes de reintentar, pero salir si se detiene
                    for i in range(config_data.get('INTERVALO_MINUTOS', 5) * 60):
                        if not config_data['sync_running']:
                            return
                        time.sleep(1)
    
    except Exception as fatal_error:
        logging.exception(f"❌ Error fatal en worker de sincronización: {fatal_error}")
    finally:
        logging.info("🏁 Worker de sincronización finalizado")
        # Asegurar que la interfaz se actualice correctamente al salir
        config_data['sync_running'] = False

# ————— Funciones para bandeja del sistema —————
def create_tray_icon():
    """Crea un icono para la bandeja del sistema"""
    # Crear una imagen simple para el icono
    width = height = 64
    image = Image.new('RGB', (width, height), 'blue')
    draw = ImageDraw.Draw(image)
    
    # Dibujar un círculo simple
    draw.ellipse([width//4, height//4, 3*width//4, 3*height//4], fill='white')
    
    return image

class SyncBioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sincronización Biométrica Mejorada")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.sync_thread = None
        self.tray_icon = None
        self.hidden = False
        self.watchdog_active = False
        
        # Cargar configuración
        load_config()
        
        self.setup_ui()
        self.setup_tray()
        
        # Auto-iniciar si está configurado
        if config_data.get('AUTO_START', False):
            self.root.after(1000, self.start_sync)  # Iniciar después de 1 segundo
    
    def setup_tray(self):
        """Configura el icono de la bandeja del sistema"""
        if config_data.get('MINIMIZE_TO_TRAY', True):
            try:
                # Crear menú para la bandeja
                menu = pystray.Menu(
                    pystray.MenuItem("Mostrar", self.show_window),
                    pystray.MenuItem("Ocultar", self.hide_window),
                    pystray.MenuItem("Iniciar Sync", self.tray_start_sync),
                    pystray.MenuItem("Detener Sync", self.tray_stop_sync),
                    pystray.MenuItem("Salir", self.quit_app)
                )
                
                # Crear icono de bandeja
                self.tray_icon = pystray.Icon(
                    "sync_bio",
                    create_tray_icon(),
                    "Sincronización Biométrica",
                    menu
                )
                
                # Configurar el comportamiento de cierre de ventana
                self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
                
            except Exception as e:
                logging.warning(f"⚠️ No se pudo configurar la bandeja del sistema: {e}")
                self.tray_icon = None
    
    def show_window(self, icon=None, item=None):
        """Muestra la ventana principal"""
        self.root.deiconify()
        self.root.lift()
        self.hidden = False
    
    def hide_window(self, icon=None, item=None):
        """Oculta la ventana principal"""
        self.root.withdraw()
        self.hidden = True
    
    def tray_start_sync(self, icon=None, item=None):
        """Inicia sincronización desde la bandeja"""
        if not config_data['sync_running']:
            self.start_sync()
    
    def tray_stop_sync(self, icon=None, item=None):
        """Detiene sincronización desde la bandeja"""
        if config_data['sync_running']:
            self.stop_sync()
    
    def quit_app(self, icon=None, item=None):
        """Cierra completamente la aplicación"""
        if config_data['sync_running']:
            self.stop_sync()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.root.quit()
        self.root.destroy()
    
    def on_closing(self):
        """Maneja el cierre de la ventana principal"""
        if config_data.get('MINIMIZE_TO_TRAY', True) and self.tray_icon:
            # Minimizar a bandeja en lugar de cerrar
            self.hide_window()
        else:
            # Cerrar completamente
            self.quit_app()
    
    def setup_ui(self):
        # Frame principal con scrollbar
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Sincronización Biométrica Mejorada", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame de configuración
        config_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # IP del dispositivo
        ip_frame = ttk.Frame(config_frame)
        ip_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ip_frame, text="IP del Dispositivo:", width=20).pack(side=tk.LEFT)
        self.ip_var = tk.StringVar(value=config_data.get('IP_BIOMETRICO', '192.168.1.88'))
        ip_entry = ttk.Entry(ip_frame, textvariable=self.ip_var, width=20)
        ip_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Puerto del dispositivo
        puerto_frame = ttk.Frame(config_frame)
        puerto_frame.pack(fill=tk.X, pady=5)
        ttk.Label(puerto_frame, text="Puerto:", width=20).pack(side=tk.LEFT)
        self.puerto_var = tk.StringVar(value=str(config_data.get('PUERTO_BIOMETRICO', 4370)))
        puerto_entry = ttk.Entry(puerto_frame, textvariable=self.puerto_var, width=20)
        puerto_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Nombre de la estación
        estacion_frame = ttk.Frame(config_frame)
        estacion_frame.pack(fill=tk.X, pady=5)
        ttk.Label(estacion_frame, text="Nombre de la Estación:", width=20).pack(side=tk.LEFT)
        self.estacion_var = tk.StringVar(value=config_data.get('NOMBRE_ESTACION', 'Centenario'))
        estacion_entry = ttk.Entry(estacion_frame, textvariable=self.estacion_var, width=20)
        estacion_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Intervalo de sincronización
        intervalo_frame = ttk.Frame(config_frame)
        intervalo_frame.pack(fill=tk.X, pady=5)
        ttk.Label(intervalo_frame, text="Intervalo (minutos):", width=20).pack(side=tk.LEFT)
        self.intervalo_var = tk.StringVar(value=str(config_data.get('INTERVALO_MINUTOS', 5)))
        intervalo_entry = ttk.Entry(intervalo_frame, textvariable=self.intervalo_var, width=20)
        intervalo_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # URL del servidor
        server_frame = ttk.Frame(config_frame)
        server_frame.pack(fill=tk.X, pady=5)
        ttk.Label(server_frame, text="URL del Servidor:", width=20).pack(side=tk.LEFT)
        self.server_var = tk.StringVar(value=config_data.get('SERVER_URL', DEFAULT_CONFIG['SERVER_URL']))
        server_entry = ttk.Entry(server_frame, textvariable=self.server_var, width=40)
        server_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Checkboxes de opciones
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.auto_start_var = tk.BooleanVar(value=config_data.get('AUTO_START', False))
        auto_start_check = ttk.Checkbutton(options_frame, text="Auto-iniciar al abrir la aplicación", 
                                          variable=self.auto_start_var)
        auto_start_check.pack(side=tk.LEFT)
        
        self.minimize_tray_var = tk.BooleanVar(value=config_data.get('MINIMIZE_TO_TRAY', True))
        minimize_check = ttk.Checkbutton(options_frame, text="Minimizar a bandeja del sistema", 
                                        variable=self.minimize_tray_var)
        minimize_check.pack(side=tk.LEFT, padx=(20, 0))
        
        # Botones de configuración
        config_buttons_frame = ttk.Frame(config_frame)
        config_buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(config_buttons_frame, text="Guardar Configuración", 
                  command=self.save_config_ui).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_buttons_frame, text="Cargar Configuración", 
                  command=self.load_config_ui).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_buttons_frame, text="Exportar Config", 
                  command=self.export_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_buttons_frame, text="Importar Config", 
                  command=self.import_config).pack(side=tk.LEFT)
        
        # Frame de pruebas
        test_frame = ttk.LabelFrame(main_frame, text="Pruebas de Conexión", padding="10")
        test_frame.pack(fill=tk.X, pady=(0, 10))
        
        test_buttons_frame = ttk.Frame(test_frame)
        test_buttons_frame.pack(fill=tk.X)
        
        self.ping_button = ttk.Button(test_buttons_frame, text="Probar Ping", 
                                     command=self.test_ping_ui)
        self.ping_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.tcp_button = ttk.Button(test_buttons_frame, text="Probar Puerto TCP", 
                                    command=self.test_tcp_ui)
        self.tcp_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.full_test_button = ttk.Button(test_buttons_frame, text="Prueba Completa", 
                                          command=self.test_full_connection)
        self.full_test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Frame de control
        control_frame = ttk.LabelFrame(main_frame, text="Control de Sincronización", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        control_buttons_frame = ttk.Frame(control_frame)
        control_buttons_frame.pack(fill=tk.X)
        
        self.manual_button = ttk.Button(control_buttons_frame, text="Ejecutar Ahora", 
                                       command=self.manual_sync)
        self.manual_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_button = ttk.Button(control_buttons_frame, text="Iniciar Sincronización Automática", 
                                      command=self.start_sync, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_buttons_frame, text="Detener Sincronización", 
                                     command=self.stop_sync, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.diagnostico_button = ttk.Button(control_buttons_frame, text="Diagnóstico", 
                                           command=self.show_diagnostics)
        self.diagnostico_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.hide_button = ttk.Button(control_buttons_frame, text="Ocultar en Segundo Plano", 
                                     command=self.hide_window)
        self.hide_button.pack(side=tk.LEFT)
        
        # Estado
        status_frame = ttk.LabelFrame(main_frame, text="Estado", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Detenido")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     font=("Arial", 11, "bold"))
        self.status_label.pack()
        
        # Log de actividades
        log_frame = ttk.LabelFrame(main_frame, text="Log de Actividades", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Text widget con scrollbar para logs
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_text_frame, height=12, width=80, wrap=tk.WORD, 
                               font=("Consolas", 9))
        log_scrollbar_v = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar_h = ttk.Scrollbar(log_text_frame, orient=tk.HORIZONTAL, command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=log_scrollbar_v.set, xscrollcommand=log_scrollbar_h.set)
        
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scrollbar_v.grid(row=0, column=1, sticky="ns")
        log_scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        log_text_frame.rowconfigure(0, weight=1)
        log_text_frame.columnconfigure(0, weight=1)
        
        # Botones para logs
        log_buttons_frame = ttk.Frame(log_frame)
        log_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(log_buttons_frame, text="Limpiar Log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_buttons_frame, text="Exportar Log", 
                  command=self.export_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_buttons_frame, text="Abrir Carpeta Logs", 
                  command=self.open_logs_folder).pack(side=tk.LEFT)
        
        # Configurar el canvas y scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configurar scrolling con rueda del mouse
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Configurar logging para mostrar en la interfaz
        self.setup_logging_handler()
        
        # Iniciar el icono de bandeja en un hilo separado
        if self.tray_icon:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def setup_logging_handler(self):
        """Configura un handler personalizado para mostrar logs en la interfaz"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget, root):
                super().__init__()
                self.text_widget = text_widget
                self.root = root
            
            def emit(self, record):
                msg = self.format(record)
                # Programar la actualización de la interfaz en el hilo principal
                self.root.after(0, lambda: self.append_log(msg))
            
            def append_log(self, msg):
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
                # Limitar el número de líneas para evitar consumo excesivo de memoria
                lines = int(self.text_widget.index('end').split('.')[0])
                if lines > 200:
                    self.text_widget.delete('1.0', '50.0')
        
        # Agregar el handler a logging
        gui_handler = GUILogHandler(self.log_text, self.root)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(gui_handler)
    
    def update_config_from_ui(self):
        """Actualiza la configuración global desde la interfaz"""
        try:
            config_data['IP_BIOMETRICO'] = self.ip_var.get().strip()
            config_data['PUERTO_BIOMETRICO'] = int(self.puerto_var.get().strip() or "4370")
            config_data['NOMBRE_ESTACION'] = self.estacion_var.get().strip()
            config_data['INTERVALO_MINUTOS'] = int(self.intervalo_var.get().strip() or "5")
            config_data['SERVER_URL'] = self.server_var.get().strip()
            config_data['AUTO_START'] = self.auto_start_var.get()
            config_data['MINIMIZE_TO_TRAY'] = self.minimize_tray_var.get()
            return True
        except ValueError as e:
            messagebox.showerror("Error", f"Error en la configuración: {e}")
            return False
    
    def save_config_ui(self):
        """Guarda la configuración desde la interfaz"""
        if self.update_config_from_ui():
            save_config()
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
    
    def load_config_ui(self):
        """Carga la configuración en la interfaz"""
        load_config()
        self.ip_var.set(config_data.get('IP_BIOMETRICO', ''))
        self.puerto_var.set(str(config_data.get('PUERTO_BIOMETRICO', 4370)))
        self.estacion_var.set(config_data.get('NOMBRE_ESTACION', ''))
        self.intervalo_var.set(str(config_data.get('INTERVALO_MINUTOS', 5)))
        self.server_var.set(config_data.get('SERVER_URL', DEFAULT_CONFIG['SERVER_URL']))
        self.auto_start_var.set(config_data.get('AUTO_START', False))
        self.minimize_tray_var.set(config_data.get('MINIMIZE_TO_TRAY', True))
        messagebox.showinfo("Éxito", "Configuración cargada correctamente")
    
    def export_config(self):
        """Exporta la configuración a un archivo"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Exportar configuración"
            )
            if filename:
                self.update_config_from_ui()
                config_to_export = {k: v for k, v in config_data.items() 
                                  if k not in ['sync_running']}
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_to_export, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Éxito", f"Configuración exportada a {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exportando configuración: {e}")
    
    def import_config(self):
        """Importa la configuración desde un archivo"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Importar configuración"
            )
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                config_data.update(imported_config)
                self.load_config_ui()
                messagebox.showinfo("Éxito", f"Configuración importada desde {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error importando configuración: {e}")
    
    def validate_inputs(self):
        """Valida que los campos requeridos estén completos"""
        if not self.ip_var.get().strip():
            messagebox.showerror("Error", "La IP del dispositivo es requerida")
            return False
        
        try:
            puerto = int(self.puerto_var.get().strip() or "4370")
            if puerto <= 0 or puerto > 65535:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "El puerto debe ser un número válido entre 1 y 65535")
            return False
        
        if not self.estacion_var.get().strip():
            messagebox.showerror("Error", "El nombre de la estación es requerido")
            return False
        
        try:
            intervalo = int(self.intervalo_var.get().strip() or "5")
            if intervalo <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "El intervalo debe ser un número positivo")
            return False
        
        return True
    
    def test_ping_ui(self):
        """Interfaz para probar ping"""
        if not self.ip_var.get().strip():
            messagebox.showerror("Error", "Ingresa una IP válida")
            return
        
        self.ping_button.config(state="disabled", text="Probando...")
        
        def ping_worker():
            try:
                success, message = test_ping(self.ip_var.get().strip())
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Ping Exitoso", message))
                else:
                    self.root.after(0, lambda: messagebox.showwarning("Ping Fallido", message))
            finally:
                self.root.after(0, lambda: (
                    self.ping_button.config(state="normal", text="Probar Ping")
                ))
        
        threading.Thread(target=ping_worker, daemon=True).start()
    
    def test_tcp_ui(self):
        """Interfaz para probar puerto TCP"""
        if not self.validate_inputs():
            return
        
        self.tcp_button.config(state="disabled", text="Probando...")
        
        def tcp_worker():
            try:
                ip = self.ip_var.get().strip()
                puerto = int(self.puerto_var.get().strip())
                success, message = test_tcp_port(ip, puerto)
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Puerto TCP Accesible", message))
                else:
                    self.root.after(0, lambda: messagebox.showwarning("Puerto TCP Inaccesible", message))
            finally:
                self.root.after(0, lambda: (
                    self.tcp_button.config(state="normal", text="Probar Puerto TCP")
                ))
        
        threading.Thread(target=tcp_worker, daemon=True).start()
    
    def test_full_connection(self):
        """Prueba completa de conexión con el dispositivo"""
        if not self.validate_inputs():
            return
        
        self.full_test_button.config(state="disabled", text="Probando...")
        
        def full_test_worker():
            try:
                ip = self.ip_var.get().strip()
                puerto = int(self.puerto_var.get().strip())
                
                results = test_device_connection(ip, puerto)
                
                # Crear mensaje de resultado
                message = f"Resultados de la prueba completa para {ip}:{puerto}\n\n"
                
                # Ping
                ping_result = results.get('ping', {})
                message += f"🏓 Ping: {'✅' if ping_result.get('success') else '❌'} {ping_result.get('message', 'N/A')}\n"
                
                # TCP
                tcp_result = results.get('tcp', {})
                message += f"🔌 Puerto TCP: {'✅' if tcp_result.get('success') else '❌'} {tcp_result.get('message', 'N/A')}\n"
                
                # Dispositivo
                device_result = results.get('device', {})
                if device_result.get('success'):
                    info = device_result.get('info', {})
                    message += f"📱 Dispositivo: ✅ Conectado\n"
                    message += f"   Nombre: {info.get('name', 'N/A')}\n"
                    message += f"   Firmware: {info.get('firmware', 'N/A')}\n"
                    message += f"   Serie: {info.get('serial', 'N/A')}\n"
                    message += f"   Usuarios: {info.get('users_count', 'N/A')}\n"
                    message += f"   Registros: {info.get('records_count', 'N/A')}\n"
                else:
                    message += f"📱 Dispositivo: ❌ {device_result.get('error', 'Error desconocido')}\n"
                
                # Mostrar resultado
                if device_result.get('success'):
                    self.root.after(0, lambda: messagebox.showinfo("Prueba Completa Exitosa", message))
                else:
                    self.root.after(0, lambda: messagebox.showwarning("Prueba Completa con Errores", message))
                    
            except Exception as e:
                logging.error(f"Error en prueba completa: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error durante la prueba: {e}"))
            finally:
                self.root.after(0, lambda: (
                    self.full_test_button.config(state="normal", text="Prueba Completa")
                ))
        
        threading.Thread(target=full_test_worker, daemon=True).start()
    
    def manual_sync(self):
        """Ejecuta un ciclo de sincronización manual"""
        if not self.validate_inputs():
            return
        
        if not self.update_config_from_ui():
            return
        
        self.manual_button.config(state="disabled", text="Ejecutando...")
        
        def manual_worker():
            try:
                logging.info("🔧 === EJECUCIÓN MANUAL INICIADA ===")
                success = main_cycle()
                
                if success:
                    logging.info("✅ === EJECUCIÓN MANUAL COMPLETADA EXITOSAMENTE ===")
                    self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                        "Ejecución manual completada exitosamente.\n\nRevisa el log para ver los detalles del proceso."))
                else:
                    logging.warning("⚠️ === EJECUCIÓN MANUAL COMPLETADA CON ERRORES ===")
                    self.root.after(0, lambda: messagebox.showwarning("Completado con errores", 
                        "Ejecución manual completada pero con algunos errores.\n\nRevisa el log para más detalles."))
                    
            except Exception as manual_error:
                logging.error(f"❌ Error en ejecución manual: {manual_error}")
                import traceback
                logging.error(f"📋 Detalles: {traceback.format_exc()}")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Error durante la ejecución manual:\n{manual_error}"))
            finally:
                self.root.after(0, lambda: (
                    self.manual_button.config(state="normal", text="Ejecutar Ahora")
                ))
        
        threading.Thread(target=manual_worker, daemon=True).start()
    
    def start_sync(self):
        """Inicia la sincronización automática"""
        try:
            if not self.validate_inputs():
                return
            
            if not self.update_config_from_ui():
                return
            
            # Verificar que no haya otro hilo corriendo
            if hasattr(self, 'sync_thread') and self.sync_thread and self.sync_thread.is_alive():
                logging.warning("⚠️ Ya hay un hilo de sincronización ejecutándose")
                messagebox.showwarning("Sincronización en progreso", 
                    "Ya hay una sincronización en progreso. Detén la sincronización actual antes de iniciar una nueva.")
                return
            
            # Actualizar configuración global
            config_data['sync_running'] = True
            
            # Actualizar interfaz ANTES de iniciar el hilo
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_var.set(f"Iniciando... (cada {config_data['INTERVALO_MINUTOS']} min)")
            
            # Forzar actualización de la interfaz
            self.root.update_idletasks()
            
            def start_sync_worker():
                """Worker para iniciar la sincronización de forma segura"""
                try:
                    # Actualizar estado en la interfaz
                    self.root.after(0, lambda: self.status_var.set(f"Ejecutándose (cada {config_data['INTERVALO_MINUTOS']} min)"))
                    
                    # Iniciar el worker de sincronización
                    sync_worker()
                    
                except Exception as e:
                    logging.exception(f"❌ Error fatal en worker de inicio: {e}")
                    # Restaurar interfaz en caso de error
                    self.root.after(0, lambda: (
                        self.start_button.config(state="normal"),
                        self.stop_button.config(state="disabled"),
                        self.status_var.set("Error - Detenido"),
                        messagebox.showerror("Error", f"Error iniciando sincronización:\n{e}")
                    ))
                finally:
                    # Asegurar que el estado se actualice correctamente
                    config_data['sync_running'] = False
                    self.root.after(0, lambda: (
                        self.start_button.config(state="normal"),
                        self.stop_button.config(state="disabled"),
                        self.status_var.set("Detenido")
                    ))
            
            # Iniciar hilo de sincronización
            self.sync_thread = threading.Thread(target=start_sync_worker, daemon=True)
            self.sync_thread.start()
            
            # Iniciar sistema de monitoreo
            self.start_watchdog()
            
            # Guardar configuración automáticamente
            save_config()
            
            logging.info(f"🚀 Sincronización automática iniciada - IP: {config_data['IP_BIOMETRICO']}, "
                        f"Puerto: {config_data['PUERTO_BIOMETRICO']}, "
                        f"Estación: {config_data['NOMBRE_ESTACION']}, "
                        f"Intervalo: {config_data['INTERVALO_MINUTOS']} min")
            
        except Exception as e:
            logging.exception(f"❌ Error iniciando sincronización: {e}")
            # Restaurar estado de la interfaz
            config_data['sync_running'] = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_var.set("Error - No iniciado")
            messagebox.showerror("Error", f"Error iniciando sincronización:\n{e}")
    
    def stop_sync(self):
        """Detiene la sincronización automática"""
        try:
            logging.info("🛑 Deteniendo sincronización automática...")
            
            # Detener watchdog
            self.stop_watchdog()
            
            # Cambiar el flag para detener el worker
            config_data['sync_running'] = False
            
            # Actualizar interfaz inmediatamente
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_var.set("Deteniendo...")
            
            # Forzar actualización de la interfaz
            self.root.update_idletasks()
            
            def wait_for_stop():
                """Esperar a que el hilo termine y actualizar interfaz"""
                try:
                    # Esperar un momento para que el hilo termine limpiamente
                    if hasattr(self, 'sync_thread') and self.sync_thread and self.sync_thread.is_alive():
                        # Dar tiempo al hilo para que termine naturalmente
                        for i in range(10):  # Esperar hasta 10 segundos
                            if not self.sync_thread.is_alive():
                                break
                            time.sleep(1)
                        
                        if self.sync_thread.is_alive():
                            logging.warning("⚠️ El hilo de sincronización no terminó en el tiempo esperado")
                    
                    # Actualizar estado final en la interfaz
                    self.root.after(0, lambda: self.status_var.set("Detenido"))
                    logging.info("✅ Sincronización automática detenida correctamente")
                    
                except Exception as e:
                    logging.exception(f"❌ Error esperando detención del hilo: {e}")
                    self.root.after(0, lambda: self.status_var.set("Detenido (con advertencias)"))
            
            # Ejecutar la espera en un hilo separado para no bloquear la UI
            threading.Thread(target=wait_for_stop, daemon=True).start()
            
        except Exception as e:
            logging.exception(f"❌ Error deteniendo sincronización: {e}")
            # Asegurar que el estado se actualice
            config_data['sync_running'] = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_var.set("Detenido (con errores)")
    
    def start_watchdog(self):
        """Inicia el sistema de monitoreo del hilo de sincronización"""
        if self.watchdog_active:
            return  # Ya está activo
        
        self.watchdog_active = True
        
        def watchdog():
            """Monitorea el estado del hilo de sincronización"""
            try:
                while self.watchdog_active and config_data.get('sync_running', False):
                    # Verificar cada 30 segundos
                    time.sleep(30)
                    
                    if not self.watchdog_active:
                        break
                    
                    # Verificar si el hilo sigue vivo
                    if hasattr(self, 'sync_thread') and self.sync_thread:
                        if not self.sync_thread.is_alive() and config_data.get('sync_running', False):
                            # El hilo murió pero debería estar corriendo
                            logging.warning("⚠️ Hilo de sincronización se detuvo inesperadamente")
                            self.root.after(0, lambda: (
                                self.status_var.set("Error - Hilo detenido"),
                                self.start_button.config(state="normal"),
                                self.stop_button.config(state="disabled")
                            ))
                            config_data['sync_running'] = False
                            break
                    
                    # Actualizar estado cada cierto tiempo
                    if config_data.get('sync_running', False):
                        current_status = self.status_var.get()
                        if "Ejecutándose" not in current_status:
                            self.root.after(0, lambda: self.status_var.set(
                                f"Ejecutándose (cada {config_data.get('INTERVALO_MINUTOS', 5)} min)"
                            ))
                
            except Exception as e:
                logging.exception(f"❌ Error en watchdog: {e}")
            finally:
                self.watchdog_active = False
        
        # Iniciar watchdog en hilo separado
        threading.Thread(target=watchdog, daemon=True).start()
    
    def stop_watchdog(self):
        """Detiene el sistema de monitoreo"""
        self.watchdog_active = False
    
    def show_diagnostics(self):
        """Muestra información de diagnóstico del sistema"""
        try:
            # Recopilar información de diagnóstico
            diag_info = []
            diag_info.append("=== DIAGNÓSTICO DEL SISTEMA ===\n")
            
            # Estado general
            diag_info.append(f"Estado actual: {self.status_var.get()}")
            diag_info.append(f"Sincronización activa: {config_data.get('sync_running', False)}")
            diag_info.append(f"Watchdog activo: {self.watchdog_active}")
            
            # Estado del hilo
            if hasattr(self, 'sync_thread') and self.sync_thread:
                diag_info.append(f"Hilo de sincronización existe: Sí")
                diag_info.append(f"Hilo está vivo: {self.sync_thread.is_alive()}")
                diag_info.append(f"Hilo es daemon: {self.sync_thread.daemon}")
            else:
                diag_info.append(f"Hilo de sincronización existe: No")
            
            # Configuración actual
            diag_info.append(f"\n=== CONFIGURACIÓN ===")
            diag_info.append(f"IP Dispositivo: {config_data.get('IP_BIOMETRICO', 'No configurada')}")
            diag_info.append(f"Puerto: {config_data.get('PUERTO_BIOMETRICO', 'No configurado')}")
            diag_info.append(f"Estación: {config_data.get('NOMBRE_ESTACION', 'No configurada')}")
            diag_info.append(f"Intervalo: {config_data.get('INTERVALO_MINUTOS', 'No configurado')} min")
            
            # Información del sistema
            diag_info.append(f"\n=== SISTEMA ===")
            diag_info.append(f"Threads activos: {threading.active_count()}")
            
            # Información de logging
            diag_info.append(f"\n=== LOGGING ===")
            log_file_path = get_log_file_path()
            diag_info.append(f"Archivo de log: {log_file_path}")
            diag_info.append(f"Log existe: {'Sí' if os.path.exists(log_file_path) else 'No'}")
            if os.path.exists(log_file_path):
                try:
                    log_size = os.path.getsize(log_file_path)
                    diag_info.append(f"Tamaño del log: {log_size} bytes")
                    
                    # Leer últimas líneas del archivo de log
                    with open(log_file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        last_lines = lines[-5:] if len(lines) >= 5 else lines
                        if last_lines:
                            diag_info.append(f"Últimas entradas del log:")
                            for line in last_lines:
                                diag_info.append(f"  {line.strip()}")
                        else:
                            diag_info.append("Archivo de log vacío")
                except Exception as e:
                    diag_info.append(f"Error leyendo log: {e}")
            
            # Estado de la bandeja
            diag_info.append(f"\n=== INTERFAZ ===")
            diag_info.append(f"Bandeja del sistema: {'Activa' if self.tray_icon else 'Inactiva'}")
            diag_info.append(f"Ventana oculta: {self.hidden}")
            
            # Últimos logs (del widget de texto)
            diag_info.append(f"\n=== LOGS DEL WIDGET ===")
            try:
                log_content = self.log_text.get('end-10l', 'end-1l')
                if log_content.strip():
                    diag_info.append("Últimos logs del widget:")
                    diag_info.append(log_content)
                else:
                    diag_info.append("No hay logs en el widget")
            except:
                diag_info.append("Error obteniendo logs del widget")
            
            # Mostrar información en ventana de diálogo
            diag_text = "\n".join(diag_info)
            
            # Crear ventana de diagnóstico
            diag_window = tk.Toplevel(self.root)
            diag_window.title("Diagnóstico del Sistema")
            diag_window.geometry("600x500")
            
            # Área de texto con scroll
            text_frame = ttk.Frame(diag_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            diag_text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 9))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=diag_text_widget.yview)
            diag_text_widget.configure(yscrollcommand=scrollbar.set)
            
            diag_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Insertar texto de diagnóstico
            diag_text_widget.insert('1.0', diag_text)
            diag_text_widget.config(state='disabled')  # Solo lectura
            
            # Botones
            button_frame = ttk.Frame(diag_window)
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            ttk.Button(button_frame, text="Actualizar", 
                      command=lambda: self.update_diagnostics(diag_text_widget)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Copiar al Portapapeles", 
                      command=lambda: self.copy_to_clipboard(diag_text)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Cerrar", 
                      command=diag_window.destroy).pack(side=tk.RIGHT)
            
        except Exception as e:
            logging.exception(f"❌ Error mostrando diagnóstico: {e}")
            messagebox.showerror("Error", f"Error mostrando diagnóstico:\n{e}")
    
    def update_diagnostics(self, text_widget):
        """Actualiza la información de diagnóstico"""
        try:
            text_widget.config(state='normal')
            text_widget.delete('1.0', tk.END)
            self.show_diagnostics()  # Esto creará una nueva ventana, pero es simple
            text_widget.config(state='disabled')
        except Exception as e:
            logging.error(f"Error actualizando diagnóstico: {e}")
    
    def copy_to_clipboard(self, text):
        """Copia texto al portapapeles"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Copiado", "Información de diagnóstico copiada al portapapeles")
        except Exception as e:
            logging.error(f"Error copiando al portapapeles: {e}")
            messagebox.showerror("Error", f"No se pudo copiar al portapapeles:\n{e}")
    
    def clear_log(self):
        """Limpia el log de la interfaz"""
        self.log_text.delete('1.0', tk.END)
    
    def export_log(self):
        """Exporta el log actual a un archivo"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Exportar log",
                initialname=f"biometrico_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            if filename:
                content = self.log_text.get('1.0', tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Éxito", f"Log exportado a {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exportando log: {e}")
    
    def open_logs_folder(self):
        """Abre la carpeta de logs"""
        try:
            log_dir = os.path.abspath("logs")
            if os.path.exists(log_dir):
                os.startfile(log_dir)  # Windows
            else:
                messagebox.showwarning("Carpeta no encontrada", f"La carpeta de logs no existe: {log_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta de logs: {e}")

# ————— Ejecución principal —————
if __name__ == '__main__':
    try:
        # Verificar si ya hay una instancia corriendo
        import tempfile
        
        # Crear archivo de bloqueo para evitar múltiples instancias
        lock_file = os.path.join(tempfile.gettempdir(), 'sync_bio_app.lock')
        
        try:
            if os.name == 'nt':  # Windows
                # En Windows, simplemente verificamos si el archivo existe
                if os.path.exists(lock_file):
                    # Verificar si el proceso anterior sigue corriendo
                    try:
                        with open(lock_file, 'r') as f:
                            old_pid = f.read().strip()
                        # Si llegamos aquí, probablemente el proceso anterior terminó mal
                        os.remove(lock_file)
                    except:
                        pass
                
                # Crear archivo de bloqueo con PID actual
                with open(lock_file, 'w') as f:
                    f.write(str(os.getpid()))
                lock_handle = None
            else:  # Unix/Linux
                import fcntl
                lock_handle = open(lock_file, 'w')
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
        except (IOError, OSError):
            messagebox.showwarning("Aplicación ya ejecutándose", 
                "Ya hay una instancia de la aplicación ejecutándose.\n\n"
                "Busca el icono en la bandeja del sistema o cierra la aplicación anterior.")
            sys.exit(1)
        
        # Crear y ejecutar la aplicación
        root = tk.Tk()
        app = SyncBioApp(root)
        
        logging.info("🖥️ Interfaz gráfica iniciada")
        
        # Ejecutar la aplicación
        root.mainloop()
        
    except KeyboardInterrupt:
        logging.warning("⚡ Ejecución interrumpida por el usuario")
    except Exception as e:
        logging.exception(f"❌ Error inesperado en la aplicación: {e}")
        try:
            messagebox.showerror("Error", f"Error inesperado: {e}")
        except:
            pass
    finally:
        # Limpiar archivo de bloqueo
        try:
            if 'lock_handle' in locals() and lock_handle:
                lock_handle.close()
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except:
            pass
        
        logging.info("🏁 Aplicación finalizada")
