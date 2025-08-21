# sincronizar_biometrico.py

import os
import json
import requests
import logging
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from zk import ZK
from datetime import datetime

# ————— Configuración de logging —————
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
log_file_path = os.path.join(script_dir, 'biometrico_sync.log')

# Configurar logging con rotación de archivos
from logging.handlers import RotatingFileHandler

# Crear logger personalizado
logger = logging.getLogger('BiometricoSync')
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

# Handler para consola (solo si no es EXE o si está en modo debug)
if not getattr(sys, 'frozen', False) or '--debug' in sys.argv:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

# Configurar el logger raíz para usar nuestro logger
logging.root = logger
logging.basicConfig = lambda **kwargs: None  # Evitar reconfiguración

logger.info("🚀 Script de sincronización biométrica iniciado")
logger.info(f"📁 Directorio de trabajo: {script_dir}")
logger.info(f"📄 Archivo de log: {log_file_path}")
logger.info(f"💻 Ejecutándose como: {'EXE compilado' if getattr(sys, 'frozen', False) else 'Script Python'}")

# ————— Funciones auxiliares de logging —————
def log_info(message):
    """Log info message"""
    logger.info(message)

def log_error(message):
    """Log error message"""
    logger.error(message)

def log_warning(message):
    """Log warning message"""
    logger.warning(message)

def log_debug(message):
    """Log debug message"""
    logger.debug(message)

def log_exception(message):
    """Log exception with traceback"""
    logger.exception(message)

# ————— Configuración por defecto —————
SERVER_URL = "http://186.31.35.24:8000/api/recibir-datos-biometrico/"
TOKEN_API = None  # Si tienes token, escríbelo aquí: "abcd1234..."

# Variables globales para la configuración
config_data = {
    'IP_BIOMETRICO': '',
    'PUERTO_BIOMETRICO': 4370,
    'NOMBRE_ESTACION': '',
    'sync_running': False
}

# ————— Funciones —————
def conectar_dispositivo(ip, puerto=4370, timeout=30):
    logging.info(f"🔌 Intentando conectar al dispositivo en {ip}:{puerto} (timeout: {timeout}s)")
    
    # Probar diferentes configuraciones de conexión
    configuraciones = [
        {'force_udp': False, 'ommit_ping': False},
        {'force_udp': True, 'ommit_ping': False},
        {'force_udp': False, 'ommit_ping': True},
        {'force_udp': True, 'ommit_ping': True}
    ]
    
    for i, config in enumerate(configuraciones, 1):
        try:
            logging.info(f"🔄 Intento {i}/4 - UDP: {config['force_udp']}, Ping: {not config['ommit_ping']}")
            zk = ZK(ip, port=puerto, timeout=timeout, **config)
            conn = zk.connect()
            
            # Probar la conexión obteniendo información del dispositivo
            firmware_version = conn.get_firmware_version()
            logging.info(f"✅ Conexión exitosa! Firmware: {firmware_version}")
            
            # Intentar deshabilitar el dispositivo temporalmente
            try:
                conn.disable_device()
                logging.info("🔒 Dispositivo deshabilitado temporalmente para sincronización")
            except Exception as disable_error:
                logging.warning(f"⚠️ No se pudo deshabilitar el dispositivo: {disable_error}")
                # Continuar sin deshabilitar
            
            return conn
            
        except Exception as e:
            logging.warning(f"❌ Intento {i} fallido: {e}")
            if i < len(configuraciones):
                logging.info("⏳ Probando siguiente configuración...")
                time.sleep(2)
            continue
    
    logging.error(f"❌ Todos los intentos de conexión fallaron para {ip}:{puerto}")
    return None

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
        
        # Obtener registros de asistencia con timeout implícito
        logging.info("📥 Llamando a get_attendance()...")
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Timeout obteniendo registros")
        
        # Configurar timeout solo en sistemas Unix-like
        try:
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)  # 30 segundos timeout
        except:
            pass
        
        try:
            registros = conn.get_attendance()
            logging.info("✅ get_attendance() completado")
        finally:
            # Cancelar timeout
            try:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
            except:
                pass
        
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
        
    except TimeoutError as te:
        logging.error(f"⏰ Timeout obteniendo registros: {te}")
        return []
    except Exception as e:
        logging.error(f"❌ Error al obtener registros: {e}")
        import traceback
        logging.error(f"📋 Detalles del error: {traceback.format_exc()}")
        return []

def enviar_datos(data, token=None):
    logging.info(f"📤 Enviando {len(data)} registros...")
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    try:
        logging.debug(json.dumps(data, indent=2, ensure_ascii=False))
        resp = requests.post(SERVER_URL, json=data, headers=headers, timeout=10)
        logging.info(f"📨 Código de respuesta: {resp.status_code}")
        if resp.status_code == 200:
            logging.info("✅ Datos enviados correctamente")
        else:
            logging.warning(f"❌ Error en la respuesta del servidor: {resp.text}")
    except Exception as e:
        logging.error(f"❌ Error al enviar datos: {e}")

def main_cycle():
    if not config_data['IP_BIOMETRICO'] or not config_data['NOMBRE_ESTACION']:
        logging.error("❌ Configuración incompleta (falta IP o nombre de estación)")
        logging.error(f"   IP: '{config_data['IP_BIOMETRICO']}'")
        logging.error(f"   Estación: '{config_data['NOMBRE_ESTACION']}'")
        return

    logging.info(f"🚀 Iniciando ciclo de sincronización para {config_data['NOMBRE_ESTACION']}")
    logging.info(f"🎯 Objetivo: {config_data['IP_BIOMETRICO']}:{config_data['PUERTO_BIOMETRICO']}")
    logging.info(f"📊 Estado de configuración: sync_running = {config_data['sync_running']}")
    
    # Verificar conectividad básica
    try:
        import socket
        logging.info("🔍 Verificando conectividad TCP...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((config_data['IP_BIOMETRICO'], config_data['PUERTO_BIOMETRICO']))
        sock.close()
        
        if result == 0:
            logging.info("✅ Puerto TCP accesible")
        else:
            logging.warning(f"⚠️ Puerto TCP no responde (código: {result})")
            logging.warning("   Esto puede indicar que el dispositivo está apagado o inaccesible")
    except Exception as net_error:
        logging.warning(f"⚠️ Error verificando conectividad: {net_error}")

    logging.info("🔌 Estableciendo conexión con el dispositivo...")
    conn = conectar_dispositivo(config_data['IP_BIOMETRICO'], config_data['PUERTO_BIOMETRICO'])
    if not conn:
        logging.error("❌ No se pudo establecer conexión con el dispositivo")
        logging.error("   Verifique que:")
        logging.error("   • El dispositivo esté encendido")
        logging.error("   • La IP y puerto sean correctos")
        logging.error("   • No haya firewall bloqueando la conexión")
        return

    try:
        # Obtener información del dispositivo
        try:
            logging.info("📊 Obteniendo información del dispositivo...")
            users_count = len(conn.get_users() or [])
            logging.info(f"👥 Usuarios registrados en el dispositivo: {users_count}")
        except Exception as info_error:
            logging.warning(f"⚠️ No se pudo obtener información del dispositivo: {info_error}")

        # Obtener registros - CON TIMEOUT ESPECÍFICO
        logging.info("📄 Iniciando obtención de registros...")
        try:
            regs = obtener_registros_crudos(conn, config_data['NOMBRE_ESTACION'])
            logging.info(f"📥 Obtención de registros completada: {len(regs)} registros")
        except Exception as reg_error:
            logging.error(f"❌ Error durante obtención de registros: {reg_error}")
            regs = []
        
        if regs:
            logging.info(f"📤 Preparando envío de {len(regs)} registros al servidor...")
            try:
                enviar_datos(regs, TOKEN_API)
                logging.info("✅ Envío de datos completado")
            except Exception as send_error:
                logging.error(f"❌ Error enviando datos: {send_error}")
        else:
            logging.info("🟡 No hay datos para enviar en este ciclo")
            
    except Exception as cycle_error:
        logging.error(f"❌ Error durante el ciclo de sincronización: {cycle_error}")
        import traceback
        logging.error(f"📋 Detalles del error: {traceback.format_exc()}")
        
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
    """Función que ejecuta la sincronización en un hilo separado"""
    logging.info("🔄 Worker de sincronización iniciado")
    
    try:
        # Ejecutar primer ciclo inmediatamente
        if config_data['sync_running']:
            try:
                logging.info("🚀 === INICIANDO PRIMER CICLO DE SINCRONIZACIÓN AUTOMÁTICA ===")
                start_time = time.time()
                
                main_cycle()
                
                end_time = time.time()
                duration = end_time - start_time
                logging.info(f"⏱️ Primer ciclo completado en {duration:.2f} segundos")
            except Exception as e:
                logging.exception(f"❌ Error en primer ciclo: {e}")
                import traceback
                logging.error(f"📋 Stack trace: {traceback.format_exc()}")
        
        # Continuar con ciclos cada 5 minutos
        cycle_count = 1
        while config_data['sync_running']:
            try:
                logging.info(f"⏱️ Esperando 5 minutos para la siguiente ejecución (Ciclo #{cycle_count + 1})...")
                
                # Dividir la espera en pequeños intervalos para poder detener el hilo
                for i in range(300):  # 300 segundos = 5 minutos
                    if not config_data['sync_running']:
                        logging.info("🛑 Sincronización detenida durante la espera")
                        break
                    
                    # Log cada minuto durante la espera
                    if i > 0 and i % 60 == 0:
                        remaining_minutes = (300 - i) // 60
                        logging.info(f"⏳ Esperando... {remaining_minutes} minutos restantes para el ciclo #{cycle_count + 1}")
                    
                    time.sleep(1)
                
                # Si aún está corriendo, ejecutar siguiente ciclo
                if config_data['sync_running']:
                    cycle_count += 1
                    logging.info(f"🚀 === INICIANDO CICLO DE SINCRONIZACIÓN #{cycle_count} ===")
                    start_time = time.time()
                    
                    main_cycle()
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    logging.info(f"⏱️ Ciclo #{cycle_count} completado en {duration:.2f} segundos")
                    
            except Exception as e:
                logging.exception(f"❌ Error inesperado en el ciclo #{cycle_count}: {e}")
                import traceback
                logging.error(f"📋 Stack trace completo: {traceback.format_exc()}")
                logging.info("⏱️ Reiniciando en 5 minutos...")
                
                # Esperar antes de reintentar
                for i in range(300):
                    if not config_data['sync_running']:
                        break
                    time.sleep(1)
    
    except Exception as fatal_error:
        logging.exception(f"❌ Error fatal en sync_worker: {fatal_error}")
        import traceback
        logging.error(f"📋 Stack trace fatal: {traceback.format_exc()}")
    
    finally:
        logging.info(f"🏁 Worker de sincronización finalizado (Total de ciclos ejecutados: {cycle_count})")

class SyncBioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sincronización Biométrica")
        self.root.geometry("700x450")
        self.root.resizable(False, False)
        
        self.sync_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="Configuración de Sincronización Biométrica", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # IP del dispositivo
        ttk.Label(main_frame, text="IP del Dispositivo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ip_var = tk.StringVar(value="192.168.1.88")
        ip_entry = ttk.Entry(main_frame, textvariable=self.ip_var, width=30)
        ip_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Puerto del dispositivo
        ttk.Label(main_frame, text="Puerto:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.puerto_var = tk.StringVar(value="4370")
        puerto_entry = ttk.Entry(main_frame, textvariable=self.puerto_var, width=30)
        puerto_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Nombre de la estación
        ttk.Label(main_frame, text="Nombre de la Estación:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.estacion_var = tk.StringVar(value="Centenario")
        estacion_entry = ttk.Entry(main_frame, textvariable=self.estacion_var, width=30)
        estacion_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Primera fila de botones
        first_row = ttk.Frame(button_frame)
        first_row.pack(fill=tk.X, pady=(0, 5))
        
        # Botón de prueba de conexión
        self.test_button = ttk.Button(first_row, text="Probar Conexión", 
                                     command=self.test_connection)
        self.test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón de ejecución manual
        self.manual_button = ttk.Button(first_row, text="Ejecutar Ahora", 
                                       command=self.manual_sync)
        self.manual_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón de prueba rápida
        self.quick_test_button = ttk.Button(first_row, text="Prueba Rápida", 
                                          command=self.quick_test)
        self.quick_test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Segunda fila de botones
        second_row = ttk.Frame(button_frame)
        second_row.pack(fill=tk.X)
        
        self.start_button = ttk.Button(second_row, text="Iniciar Sincronización Automática", 
                                      command=self.start_sync, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(second_row, text="Detener Sincronización", 
                                     command=self.stop_sync, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Estado
        self.status_var = tk.StringVar(value="Detenido")
        status_frame = ttk.LabelFrame(main_frame, text="Estado", padding="10")
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     font=("Arial", 10, "bold"))
        self.status_label.pack()
        
        # Log de actividades
        log_frame = ttk.LabelFrame(main_frame, text="Log de Actividades", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Text widget con scrollbar
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(text_frame, height=8, width=60, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar el grid para que se expanda
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Configurar logging para mostrar en la interfaz
        self.setup_logging_handler()
    
    def setup_logging_handler(self):
        """Configura un handler personalizado para mostrar logs en la interfaz"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget, app_instance):
                super().__init__()
                self.text_widget = text_widget
                self.app_instance = app_instance
                self.max_lines = 200  # Máximo de líneas en la GUI
            
            def emit(self, record):
                try:
                    msg = self.format(record)
                    # Programar la actualización de la interfaz en el hilo principal
                    self.text_widget.after(0, lambda: self.append_log(msg))
                except Exception as e:
                    # Si hay error en GUI, al menos log al archivo
                    logger.error(f"Error en GUILogHandler: {e}")
            
            def append_log(self, msg):
                try:
                    # Insertar el mensaje
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    
                    # Limitar el número de líneas para evitar consumo excesivo de memoria
                    lines = int(self.text_widget.index('end').split('.')[0])
                    if lines > self.max_lines:
                        # Eliminar las primeras 50 líneas
                        self.text_widget.delete('1.0', '51.0')
                        
                    # Actualizar la ventana
                    self.text_widget.update_idletasks()
                    
                except Exception as e:
                    # Si hay error, intentar al menos mostrar en título
                    try:
                        self.app_instance.root.title(f"Sincronización Biométrica - Error en log: {e}")
                    except:
                        pass
        
        # Crear y configurar el handler GUI
        self.gui_handler = GUILogHandler(self.log_text, self)
        self.gui_handler.setLevel(logging.INFO)
        gui_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.gui_handler.setFormatter(gui_formatter)
        
        # Agregar el handler al logger
        logger.addHandler(self.gui_handler)
        
        # Log inicial en la GUI
        logger.info("🖥️ Interfaz gráfica iniciada")
        logger.info(f"📊 Logger configurado con {len(logger.handlers)} handlers")
    
    def quick_test(self):
        """Prueba rápida del ciclo automático (30 segundos en lugar de 5 minutos)"""
        if not self.validate_inputs():
            return
        
        # Mostrar confirmación
        result = messagebox.askquestion("Prueba Rápida", 
            "¿Iniciar prueba rápida de sincronización automática?\n\n"
            "Ejecutará 2 ciclos con 30 segundos de espera entre ellos\n"
            "para verificar que el mecanismo automático funciona.")
        
        if result != 'yes':
            return
        
        # Actualizar configuración global
        config_data['IP_BIOMETRICO'] = self.ip_var.get().strip()
        config_data['PUERTO_BIOMETRICO'] = int(self.puerto_var.get().strip() or "4370")
        config_data['NOMBRE_ESTACION'] = self.estacion_var.get().strip()
        config_data['sync_running'] = True
        
        def quick_test_worker():
            """Worker para prueba rápida"""
            try:
                logging.info("🧪 === INICIANDO PRUEBA RÁPIDA ===")
                
                # Primer ciclo
                logging.info("🚀 Ejecutando primer ciclo...")
                main_cycle()
                
                # Espera de 30 segundos
                logging.info("⏱️ Esperando 30 segundos...")
                for i in range(30):
                    if not config_data['sync_running']:
                        break
                    if i % 10 == 0 and i > 0:
                        logging.info(f"⏳ {30-i} segundos restantes...")
                    time.sleep(1)
                
                # Segundo ciclo si aún está corriendo
                if config_data['sync_running']:
                    logging.info("🚀 Ejecutando segundo ciclo...")
                    main_cycle()
                    logging.info("✅ === PRUEBA RÁPIDA COMPLETADA ===")
                    
                    self.root.after(0, lambda: messagebox.showinfo("Prueba Completada", 
                        "Prueba rápida completada exitosamente!\n\n"
                        "El mecanismo de sincronización automática funciona correctamente."))
                else:
                    logging.info("🛑 Prueba rápida detenida por el usuario")
                    
            except Exception as e:
                logging.error(f"❌ Error en prueba rápida: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Error durante la prueba rápida:\n{e}"))
            finally:
                config_data['sync_running'] = False
                # Restaurar interfaz
                self.root.after(0, lambda: (
                    self.start_button.config(state="normal"),
                    self.stop_button.config(state="disabled"),
                    self.status_var.set("Detenido")
                ))
        
        # Actualizar interfaz
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_var.set("Prueba Rápida")
        
        # Ejecutar en hilo separado
        self.sync_thread = threading.Thread(target=quick_test_worker, daemon=True)
        self.sync_thread.start()

    def manual_sync(self):
        """Ejecuta un ciclo de sincronización manual"""
        if not self.validate_inputs():
            return
        
        # Deshabilitar botón durante la ejecución
        self.manual_button.config(state="disabled")
        self.manual_button.config(text="Ejecutando...")
        
        def manual_worker():
            try:
                # Actualizar configuración temporal
                config_data['IP_BIOMETRICO'] = self.ip_var.get().strip()
                config_data['PUERTO_BIOMETRICO'] = int(self.puerto_var.get().strip() or "4370")
                config_data['NOMBRE_ESTACION'] = self.estacion_var.get().strip()
                
                logging.info("🔧 === EJECUCIÓN MANUAL INICIADA ===")
                main_cycle()
                logging.info("✅ === EJECUCIÓN MANUAL COMPLETADA ===")
                
                self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                    "Ejecución manual completada.\n\nRevisa el log para ver los detalles del proceso."))
                    
            except Exception as manual_error:
                logging.error(f"❌ Error en ejecución manual: {manual_error}")
                import traceback
                logging.error(f"📋 Detalles: {traceback.format_exc()}")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Error durante la ejecución manual:\n{manual_error}"))
            finally:
                # Restaurar botón
                self.root.after(0, lambda: (
                    self.manual_button.config(state="normal"),
                    self.manual_button.config(text="Ejecutar Ahora")
                ))
        
        # Ejecutar en hilo separado
        import threading
        manual_thread = threading.Thread(target=manual_worker, daemon=True)
        manual_thread.start()

    def test_connection(self):
        """Prueba la conexión con el dispositivo biométrico"""
        if not self.validate_inputs():
            return
        
        # Deshabilitar botón durante la prueba
        self.test_button.config(state="disabled")
        self.test_button.config(text="Probando...")
        
        def test_worker():
            try:
                ip = self.ip_var.get().strip()
                puerto = int(self.puerto_var.get().strip() or "4370")
                
                logging.info(f"🧪 === INICIANDO PRUEBA DE CONEXIÓN ===")
                logging.info(f"🎯 Destino: {ip}:{puerto}")
                
                # Prueba 1: Ping básico
                import subprocess
                try:
                    result = subprocess.run(['ping', '-n', '1', ip], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        logging.info("✅ Ping exitoso")
                    else:
                        logging.warning("⚠️ Ping falló")
                except Exception as ping_error:
                    logging.warning(f"⚠️ Error en ping: {ping_error}")
                
                # Prueba 2: Conectividad TCP
                import socket
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    result = sock.connect_ex((ip, puerto))
                    sock.close()
                    
                    if result == 0:
                        logging.info("✅ Puerto TCP accesible")
                    else:
                        logging.warning(f"⚠️ Puerto TCP inaccesible (código: {result})")
                except Exception as tcp_error:
                    logging.warning(f"⚠️ Error en prueba TCP: {tcp_error}")
                
                # Prueba 3: Conexión con el dispositivo
                conn = conectar_dispositivo(ip, puerto, timeout=30)
                if conn:
                    try:
                        # Obtener información del dispositivo
                        device_name = conn.get_device_name()
                        firmware = conn.get_firmware_version()
                        users = conn.get_users()
                        
                        logging.info(f"📱 Dispositivo: {device_name}")
                        logging.info(f"🔧 Firmware: {firmware}")
                        logging.info(f"👥 Usuarios registrados: {len(users) if users else 0}")
                        
                        # Prueba de obtención de registros
                        registros = conn.get_attendance()
                        logging.info(f"📄 Registros de asistencia: {len(registros) if registros else 0}")
                        
                        logging.info("✅ === PRUEBA DE CONEXIÓN EXITOSA ===")
                        self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                            f"Conexión exitosa con el dispositivo!\n\n"
                            f"Dispositivo: {device_name}\n"
                            f"Firmware: {firmware}\n"
                            f"Usuarios: {len(users) if users else 0}\n"
                            f"Registros: {len(registros) if registros else 0}"))
                        
                    except Exception as info_error:
                        logging.warning(f"⚠️ Error obteniendo información: {info_error}")
                        self.root.after(0, lambda: messagebox.showwarning("Conexión parcial", 
                            "Se conectó al dispositivo pero hubo problemas obteniendo información"))
                    finally:
                        try:
                            conn.enable_device()
                            conn.disconnect()
                        except:
                            pass
                else:
                    logging.error("❌ === PRUEBA DE CONEXIÓN FALLIDA ===")
                    self.root.after(0, lambda: messagebox.showerror("Error de conexión", 
                        "No se pudo conectar al dispositivo biométrico.\n\n"
                        "Verifica:\n"
                        "• La IP y puerto son correctos\n"
                        "• El dispositivo está encendido\n"
                        "• No hay firewall bloqueando\n"
                        "• Revisa el log para más detalles"))
                        
            except Exception as test_error:
                logging.error(f"❌ Error en prueba de conexión: {test_error}")
                import traceback
                logging.error(f"📋 Detalles: {traceback.format_exc()}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error durante la prueba: {test_error}"))
            finally:
                # Restaurar botón
                self.root.after(0, lambda: (
                    self.test_button.config(state="normal"),
                    self.test_button.config(text="Probar Conexión")
                ))
        
        # Ejecutar prueba en hilo separado
        import threading
        test_thread = threading.Thread(target=test_worker, daemon=True)
        test_thread.start()

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
        
        return True
    
    def start_sync(self):
        """Inicia la sincronización"""
        if not self.validate_inputs():
            return
        
        # Verificar si ya hay una sincronización en curso
        if config_data['sync_running']:
            messagebox.showwarning("Advertencia", "La sincronización ya está en ejecución")
            return
        
        # Actualizar configuración global
        config_data['IP_BIOMETRICO'] = self.ip_var.get().strip()
        config_data['PUERTO_BIOMETRICO'] = int(self.puerto_var.get().strip() or "4370")
        config_data['NOMBRE_ESTACION'] = self.estacion_var.get().strip()
        config_data['sync_running'] = True
        
        # Crear y iniciar hilo de sincronización
        try:
            self.sync_thread = threading.Thread(target=sync_worker, daemon=True)
            self.sync_thread.start()
            
            # Actualizar interfaz
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_var.set("Ejecutándose")
            
            # Iniciar watchdog para mantener la interfaz responsiva
            self.start_watchdog()
            
            logging.info(f"🚀 Sincronización automática iniciada - IP: {config_data['IP_BIOMETRICO']}, "
                        f"Puerto: {config_data['PUERTO_BIOMETRICO']}, "
                        f"Estación: {config_data['NOMBRE_ESTACION']}")
            
            messagebox.showinfo("Iniciado", 
                "Sincronización automática iniciada exitosamente.\n\n"
                "El sistema ejecutará la sincronización cada 5 minutos.\n"
                "Revisa el log para ver el progreso.")
                
        except Exception as e:
            logging.error(f"❌ Error al iniciar sincronización: {e}")
            config_data['sync_running'] = False
            messagebox.showerror("Error", f"Error al iniciar la sincronización:\n{e}")
    
    def start_watchdog(self):
        """Inicia un watchdog para mantener la interfaz responsiva y monitorear el hilo"""
        def watchdog():
            try:
                if config_data['sync_running']:
                    # Verificar si el hilo sigue vivo
                    if self.sync_thread and not self.sync_thread.is_alive():
                        logging.warning("⚠️ Hilo de sincronización se detuvo inesperadamente")
                        logging.info("🔄 Intentando reiniciar la sincronización...")
                        
                        # Intentar reiniciar el hilo
                        try:
                            self.sync_thread = threading.Thread(target=sync_worker, daemon=True)
                            self.sync_thread.start()
                            logging.info("✅ Hilo de sincronización reiniciado exitosamente")
                        except Exception as restart_error:
                            logging.error(f"❌ Error al reiniciar hilo: {restart_error}")
                            self.stop_sync()
                            messagebox.showerror("Error", 
                                "El hilo de sincronización se detuvo inesperadamente y no se pudo reiniciar.\n"
                                "Puedes intentar iniciar la sincronización nuevamente.")
                    
                    # Programar siguiente verificación en 30 segundos
                    self.root.after(30000, watchdog)
                else:
                    logging.info("🛑 Watchdog detenido - sincronización no activa")
                    
            except Exception as watchdog_error:
                logging.error(f"❌ Error en watchdog: {watchdog_error}")
                # Programar siguiente verificación en caso de error
                if config_data['sync_running']:
                    self.root.after(60000, watchdog)  # Esperar más tiempo si hay error
        
        # Iniciar el watchdog en 30 segundos
        self.root.after(30000, watchdog)
    
    def stop_sync(self):
        """Detiene la sincronización"""
        if not config_data['sync_running']:
            logging.info("ℹ️ La sincronización ya está detenida")
            return
            
        logging.info("🛑 Deteniendo sincronización automática...")
        config_data['sync_running'] = False
        
        # Actualizar interfaz
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_var.set("Deteniendo...")
        
        # Dar tiempo para que el hilo termine limpiamente
        def finish_stop():
            try:
                if self.sync_thread and self.sync_thread.is_alive():
                    logging.info("⏳ Esperando que termine el hilo de sincronización...")
                    # Esperar hasta 10 segundos para que termine limpiamente
                    for i in range(10):
                        if not self.sync_thread.is_alive():
                            break
                        time.sleep(1)
                    
                    if self.sync_thread.is_alive():
                        logging.warning("⚠️ El hilo no terminó en el tiempo esperado")
                    else:
                        logging.info("✅ Hilo de sincronización terminado correctamente")
                
                self.status_var.set("Detenido")
                logging.info("🛑 Sincronización automática detenida completamente")
                
                messagebox.showinfo("Detenido", 
                    "La sincronización automática ha sido detenida exitosamente.")
                    
            except Exception as e:
                logging.error(f"❌ Error al detener sincronización: {e}")
                self.status_var.set("Error al detener")
        
        # Ejecutar la finalización en un hilo separado para no bloquear la UI
        threading.Thread(target=finish_stop, daemon=True).start()
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        logger.info("🚪 Cerrando aplicación...")
        
        if config_data['sync_running']:
            if messagebox.askquestion("Confirmar", "La sincronización está en ejecución. ¿Desea detenerla y salir?") == "yes":
                logger.info("🛑 Usuario confirmó detener sincronización y salir")
                self.stop_sync()
                # Esperar un momento para que se detenga limpiamente
                self.root.after(2000, self._force_close)
            else:
                logger.info("❌ Usuario canceló el cierre")
                return
        else:
            self._force_close()
    
    def _force_close(self):
        """Fuerza el cierre de la aplicación"""
        try:
            # Remover el handler GUI del logger
            if hasattr(self, 'gui_handler') and self.gui_handler in logger.handlers:
                logger.removeHandler(self.gui_handler)
                logger.info("🗑️ Handler GUI removido del logger")
            
            logger.info("👋 Aplicación cerrada correctamente")
            
            # Cerrar la ventana
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            # Si hay error, forzar cierre
            try:
                logger.error(f"❌ Error al cerrar aplicación: {e}")
            except:
                pass
            self.root.quit()
            self.root.destroy()

# ————— Ejecución con interfaz gráfica —————
if __name__ == '__main__':
    try:
        logger.info("🖥️ Iniciando aplicación con interfaz gráfica")
        logger.info(f"🐍 Python {sys.version}")
        logger.info(f"📍 Argumentos: {sys.argv}")
        
        root = tk.Tk()
        app = SyncBioApp(root)
        
        # Configurar el protocolo de cierre de ventana
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        logger.info("🚀 Aplicación lista, iniciando loop principal")
        
        # Ejecutar la aplicación
        root.mainloop()
        
    except KeyboardInterrupt:
        logger.warning("⚡ Ejecución interrumpida por el usuario (Ctrl+C)")
    except Exception as e:
        logger.exception(f"❌ Error inesperado en la aplicación: {e}")
        try:
            messagebox.showerror("Error", f"Error inesperado: {e}")
        except:
            pass
    finally:
        try:
            # Asegurar que se detenga la sincronización
            if 'config_data' in globals() and config_data.get('sync_running', False):
                logger.info("🛑 Deteniendo sincronización antes del cierre...")
                config_data['sync_running'] = False
            
            logger.info("🏁 Aplicación finalizada correctamente")
            
            # Limpiar y cerrar handlers de logging
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
                
        except Exception as final_error:
            # Si hay error en la limpieza final, intentar log básico
            try:
                print(f"Error en limpieza final: {final_error}")
            except:
                pass
