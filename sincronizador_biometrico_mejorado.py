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
        print(f"WARNING: No se pudo crear directorio logs, usando: {log_file_path}")
    
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
        print(f"OK: Logging configurado correctamente: {log_file_path}")
    except Exception as e:
        print(f"ERROR: Error configurando file logging: {e}")
    
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
    'MINIMIZE_TO_TRAY': True,
    'START_WITH_WINDOWS': False
}

# Variables globales
config_data = DEFAULT_CONFIG.copy()
config_data['sync_running'] = False
app = None  # Referencia global a la aplicación para acceso desde funciones

# ————— Funciones de configuración mejoradas —————
def get_config_path():
    """Obtiene la ruta del archivo de configuración de manera robusta"""
    # Prioridades de búsqueda:
    # 1. Directorio actual de trabajo
    # 2. Directorio del script actual
    # 3. Directorio del ejecutable (si es ejecutable compilado)
    # 4. Directorio AppData del usuario
    
    config_paths = []
    
    # 1. Directorio actual
    config_paths.append(os.path.join(os.getcwd(), 'biometrico_config.json'))
    
    # 2. Directorio del script
    if hasattr(sys, '_MEIPASS'):
        # Si es ejecutable compilado con PyInstaller
        app_dir = os.path.dirname(sys.executable)
    else:
        # Si es script Python
        app_dir = os.path.dirname(os.path.abspath(__file__))
    config_paths.append(os.path.join(app_dir, 'biometrico_config.json'))
    
    # 3. AppData del usuario (Windows) o directorio home (Unix)
    if os.name == 'nt':  # Windows
        appdata_dir = os.path.expanduser('~\\AppData\\Local\\SyncBio')
    else:  # Unix/Linux
        appdata_dir = os.path.expanduser('~/.config/syncbio')
    
    os.makedirs(appdata_dir, exist_ok=True)
    config_paths.append(os.path.join(appdata_dir, 'biometrico_config.json'))
    
    return config_paths

def load_config():
    """Carga la configuración desde archivo con búsqueda robusta"""
    try:
        config_paths = get_config_path()
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        loaded_config = json.load(f)
                        config_data.update(loaded_config)
                        logging.info(f"CONFIG: Configuracion cargada desde: {config_path}")
                        return
                except Exception as e:
                    logging.warning(f"CONFIG: Error leyendo {config_path}: {e}")
                    continue
        
        # Si no se encontró configuración, crear una por defecto
        logging.info("CONFIG: No se encontro configuracion existente, usando valores por defecto")
        save_config()  # Crear archivo de configuración por defecto
        
    except Exception as e:
        logging.error(f"ERROR: Error cargando configuracion: {e}")

def save_config():
    """Guarda la configuración actual en archivo con gestión robusta"""
    try:
        # Crear una copia sin datos temporales
        config_to_save = {k: v for k, v in config_data.items() 
                         if k not in ['sync_running', '_autostart_mode']}
        
        config_paths = get_config_path()
        
        # Intentar guardar en el primer directorio accesible
        for config_path in config_paths:
            try:
                # Asegurar que el directorio existe
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                
                # Crear un archivo temporal primero para evitar corrupción
                temp_config_path = config_path + '.tmp'
                
                with open(temp_config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_to_save, f, indent=2, ensure_ascii=False)
                
                # Si la escritura fue exitosa, reemplazar el archivo original
                if os.path.exists(temp_config_path):
                    if os.path.exists(config_path):
                        os.remove(config_path)
                    os.rename(temp_config_path, config_path)
                
                logging.info(f"CONFIG: Configuracion guardada exitosamente en: {config_path}")
                return True
                
            except Exception as e:
                logging.warning(f"CONFIG: No se pudo guardar en {config_path}: {e}")
                # Limpiar archivo temporal si existe
                temp_config_path = config_path + '.tmp'
                if os.path.exists(temp_config_path):
                    try:
                        os.remove(temp_config_path)
                    except:
                        pass
                continue
        
        # Si no se pudo guardar en ningún lado
        logging.error("CONFIG: No se pudo guardar la configuracion en ninguna ubicacion")
        return False
        
    except Exception as e:
        logging.error(f"ERROR: Error guardando configuracion: {e}")
        return False

def auto_save_config():
    """Guarda la configuración automáticamente en segundo plano"""
    try:
        if save_config():
            logging.debug("CONFIG: Auto-guardado exitoso")
        else:
            logging.warning("CONFIG: Fallo en auto-guardado")
    except Exception as e:
        logging.error(f"ERROR: Error en auto-guardado: {e}")

# ————— Funciones de inicio automático con Windows —————
def get_app_executable_path():
    """Obtiene la ruta del ejecutable de la aplicación"""
    if getattr(sys, 'frozen', False):
        # Si es un ejecutable compilado
        return sys.executable
    else:
        # Si es un script de Python, usar python.exe + script
        python_exe = sys.executable
        script_path = os.path.abspath(__file__)
        return f'"{python_exe}" "{script_path}"'

def is_startup_enabled():
    """Verifica si el inicio automático está habilitado en Windows"""
    # Verificar ambos métodos: registro y tareas programadas
    registry_result = is_startup_enabled_registry()
    
    # Verificar tareas programadas
    task_result = False
    try:
        import subprocess
        task_name = "SincronizadorBiometrico"
        
        # Verificar si la tarea existe usando schtasks
        result = subprocess.run([
            'schtasks', '/query', '/tn', task_name
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            # La tarea existe, verificar si está habilitada
            # Usar formato CSV para parsear más fácilmente
            result_csv = subprocess.run([
                'schtasks', '/query', '/tn', task_name, '/fo', 'csv'
            ], capture_output=True, text=True, shell=True)
            
            if result_csv.returncode == 0:
                lines = result_csv.stdout.strip().split('\n')
                if len(lines) >= 2:
                    # La segunda línea contiene los datos
                    data = lines[1].split(',')
                    if len(data) >= 3:
                        # El tercer campo es el estado (Ready/Listo, Running, Disabled)
                        status = data[2].strip('"').lower()
                        task_result = status in ['ready', 'listo', 'running']
                        logging.debug(f"STARTUP: Estado de tarea programada: {status} -> {task_result}")
        
    except Exception as e:
        logging.warning(f"WARNING: Error verificando tarea programada: {e}")
    
    # Retornar True si cualquiera de los dos métodos está habilitado
    result = registry_result or task_result
    logging.debug(f"STARTUP: Resultado final - Registro: {registry_result}, Tarea: {task_result}, Total: {result}")
    return result

def is_startup_enabled_registry():
    """Método de fallback: verifica el startup usando el registro de Windows"""
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SincronizadorBiometrico"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            
            # Si existe la entrada y contiene contenido relevante
            if value and len(value.strip()) > 0:
                # Verificar que la entrada contiene referencias al script actual
                current_script = os.path.abspath(__file__)
                current_executable = sys.executable
                
                # La entrada debe contener alguna referencia al script o ejecutable actual
                if (current_script.lower() in value.lower() or 
                    current_executable.lower() in value.lower() or
                    "sincronizador" in value.lower()):
                    logging.info(f"STARTUP: Entrada válida encontrada en registro: {value}")
                    return True
                else:
                    logging.warning(f"STARTUP: Entrada obsoleta en registro: {value}")
                    return False
            else:
                return False
                
        except FileNotFoundError:
            logging.debug("STARTUP: No hay entrada en el registro")
            return False
        except WindowsError as e:
            logging.warning(f"WARNING: Error accediendo al registro: {e}")
            return False
    except ImportError:
        logging.warning("WARNING: winreg no disponible - funcionalidad de inicio automatico limitada")
        return False
    except Exception as e:
        logging.error(f"ERROR: Error verificando registro: {e}")
        return False

def enable_startup():
    """Habilita el inicio automático en Windows usando el Programador de Tareas"""
    try:
        import subprocess
        import tempfile
        task_name = "SincronizadorBiometrico"
        working_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Primero, eliminar la tarea si ya existe
        subprocess.run([
            'schtasks', '/delete', '/tn', task_name, '/f'
        ], capture_output=True, shell=True)
        
        # Crear archivo XML temporal para la tarea
        if getattr(sys, 'frozen', False):
            # Ejecutable compilado
            program = sys.executable
            arguments = '--autostart'
        else:
            # Script Python
            program = sys.executable
            script_path = os.path.abspath(__file__)
            arguments = f'"{script_path}" --autostart'
        
        # Crear XML para la tarea con configuración mejorada
        xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Sincronizador Biométrico - Inicio automático</Description>
    <Author>{os.getenv('USERNAME', 'Usuario')}</Author>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT30S</Delay>
      <UserId>{os.getenv('USERDOMAIN', '')}\\{os.getenv('USERNAME', '')}</UserId>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{os.getenv('USERDOMAIN', '')}\\{os.getenv('USERNAME', '')}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{program}</Command>
      <Arguments>{arguments}</Arguments>
      <WorkingDirectory>{working_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
        
        # Escribir archivo XML temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-16') as f:
            f.write(xml_content)
            xml_file = f.name
        
        try:
            # Crear la tarea usando el archivo XML
            cmd = ['schtasks', '/create', '/tn', task_name, '/xml', xml_file, '/f']
            
            logging.info(f"STARTUP: Creando tarea programada con XML")
            logging.info(f"STARTUP: Programa: {program}")
            logging.info(f"STARTUP: Argumentos: {arguments}")
            logging.info(f"STARTUP: Directorio: {working_dir}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                logging.info("STARTUP: Tarea programada creada exitosamente")
                return True
            else:
                logging.error(f"STARTUP: Error creando tarea programada: {result.stderr}")
                # Intentar método de fallback (registro)
                return enable_startup_registry()
                
        finally:
            # Limpiar archivo XML temporal
            try:
                os.unlink(xml_file)
            except:
                pass
            
    except Exception as e:
        logging.error(f"ERROR: Error habilitando inicio automatico con tareas programadas: {e}")
        # Intentar método de fallback (registro)
        return enable_startup_registry()

def enable_startup_registry():
    """Método de fallback: habilita el inicio automático usando el registro de Windows"""
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SincronizadorBiometrico"
        app_path = get_app_executable_path()
        
        # Agregar parámetro para inicio automático silencioso
        if getattr(sys, 'frozen', False):
            # Para ejecutable, agregar parámetro --autostart
            app_path = f'"{app_path}" --autostart'
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(key)
        
        logging.info("STARTUP: Inicio automatico habilitado en Windows (registro)")
        return True
    except ImportError:
        logging.error("ERROR: winreg no disponible - no se puede configurar inicio automatico")
        return False
    except Exception as e:
        logging.error(f"ERROR: Error habilitando inicio automatico: {e}")
        return False

def disable_startup():
    """Deshabilita el inicio automático en Windows"""
    try:
        import subprocess
        task_name = "SincronizadorBiometrico"
        
        # Intentar eliminar la tarea programada
        result = subprocess.run([
            'schtasks', '/delete', '/tn', task_name, '/f'
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            logging.info("STARTUP: Tarea programada eliminada exitosamente")
            task_deleted = True
        else:
            logging.info("STARTUP: No se encontró tarea programada para eliminar")
            task_deleted = False
        
        # También limpiar del registro por si acaso
        registry_cleaned = disable_startup_registry()
        
        if task_deleted or registry_cleaned:
            logging.info("STARTUP: Inicio automatico deshabilitado en Windows")
            return True
        else:
            logging.info("STARTUP: Inicio automatico ya estaba deshabilitado")
            return True
            
    except Exception as e:
        logging.error(f"ERROR: Error deshabilitando inicio automatico: {e}")
        # Intentar solo con registro como fallback
        return disable_startup_registry()

def disable_startup_registry():
    """Método de fallback: deshabilita el startup usando el registro de Windows"""
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SincronizadorBiometrico"
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        try:
            winreg.DeleteValue(key, app_name)
            logging.info("STARTUP: Inicio automatico deshabilitado en Windows (registro)")
            result = True
        except FileNotFoundError:
            logging.info("STARTUP: Inicio automatico ya estaba deshabilitado (registro)")
            result = True
        finally:
            winreg.CloseKey(key)
        return result
    except ImportError:
        logging.error("ERROR: winreg no disponible - no se puede configurar inicio automatico")
        return False
    except Exception as e:
        logging.error(f"ERROR: Error deshabilitando inicio automatico: {e}")
        return False

def toggle_startup(enable):
    """Habilita o deshabilita el inicio automático"""
    if enable:
        success = enable_startup()
        if success:
            config_data['START_WITH_WINDOWS'] = True
            save_config()
            return True
    else:
        success = disable_startup()
        if success:
            config_data['START_WITH_WINDOWS'] = False
            save_config()
            return True
    return False

def test_startup_functionality():
    """Función de prueba para verificar el funcionamiento del startup"""
    logging.info("🔧 TESTING: Probando funcionalidad de inicio automático")
    
    # Verificar estado actual
    current_status = is_startup_enabled()
    logging.info(f"🔧 TESTING: Estado actual del startup: {current_status}")
    
    # Probar habilitar
    logging.info("🔧 TESTING: Probando habilitar startup...")
    enable_result = enable_startup()
    logging.info(f"🔧 TESTING: Resultado habilitar: {enable_result}")
    
    # Verificar que se habilitó
    enabled_status = is_startup_enabled()
    logging.info(f"🔧 TESTING: Estado después de habilitar: {enabled_status}")
    
    # Probar deshabilitar
    logging.info("🔧 TESTING: Probando deshabilitar startup...")
    disable_result = disable_startup()
    logging.info(f"🔧 TESTING: Resultado deshabilitar: {disable_result}")
    
    # Verificar que se deshabilitó
    disabled_status = is_startup_enabled()
    logging.info(f"🔧 TESTING: Estado después de deshabilitar: {disabled_status}")
    
    # Restaurar estado original si era necesario
    if current_status:
        logging.info("🔧 TESTING: Restaurando estado original (habilitado)")
        enable_startup()
    
    logging.info("🔧 TESTING: Prueba de funcionalidad completada")
    return {
        'initial_status': current_status,
        'enable_result': enable_result,
        'enabled_status': enabled_status,
        'disable_result': disable_result,
        'disabled_status': disabled_status
    }

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
                logging.info("WAIT: Probando siguiente configuración...")
                time.sleep(2)
            continue
    
    logging.error(f"ERROR: Todos los intentos de conexión fallaron para {ip}:{puerto}")
    return None

def test_device_connection(ip, puerto):
    """Prueba completa de conexión con el dispositivo"""
    logging.info(f"TEST: === INICIANDO PRUEBA COMPLETA DE CONEXIÓN ===")
    logging.info(f"TARGET: Destino: {ip}:{puerto}")
    
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
            logging.info(f"DEVICE: Dispositivo: {device_info['name']}")
            logging.info(f"CONFIG: Firmware: {device_info['firmware']}")
            logging.info(f"ID: Serie: {device_info['serial']}")
            logging.info(f"USERS: Usuarios registrados: {device_info['users_count']}")
            logging.info(f"RECORDS: Registros de asistencia: {device_info['records_count']}")
            
            results['device'] = {'success': True, 'info': device_info}
            logging.info("OK: === PRUEBA COMPLETA EXITOSA ===")
            
        except Exception as info_error:
            logging.warning(f"WARNING: Error obteniendo información del dispositivo: {info_error}")
            results['device'] = {'success': False, 'error': str(info_error)}
        finally:
            try:
                conn.enable_device()
                conn.disconnect()
            except:
                pass
    else:
        results['device'] = {'success': False, 'error': 'No se pudo conectar'}
        logging.error("ERROR: === PRUEBA COMPLETA FALLIDA ===")
    
    return results

# ————— Funciones de sincronización (conservadas del script original) —————
def validar_user_id(user_id):
    """
    Valida que el user_id tenga más de 5 dígitos.
    Retorna True si el user_id es válido (más de 5 dígitos), False en caso contrario.
    """
    try:
        # Convertir user_id a string para verificar longitud
        user_id_str = str(user_id)
        
        # Verificar que solo contenga dígitos y tenga más de 5 caracteres
        if user_id_str.isdigit() and len(user_id_str) > 5:
            return True
        else:
            return False
    except Exception as e:
        logging.warning(f"WARNING: Error validando user_id {user_id}: {e}")
        return False

def obtener_usuarios(conn):
    try:
        logging.info("USERS: Obteniendo usuarios...")
        usuarios = conn.get_users()
        return {u.user_id: u.name for u in usuarios}
    except Exception as e:
        logging.error(f"ERROR: Error al obtener usuarios: {e}")
        return {}

def obtener_registros_crudos(conn, nombre_estacion):
    logging.info("RECORDS: Obteniendo registros de asistencia...")
    try:
        # Verificar que la conexión siga activa
        try:
            device_name = conn.get_device_name()
            logging.info(f"DEVICE: Dispositivo: {device_name}")
        except Exception as e:
            logging.warning(f"WARNING: No se pudo obtener nombre del dispositivo: {e}")
        
        # Obtener registros de asistencia
        logging.info("GET: Llamando a get_attendance()...")
        registros = conn.get_attendance()
        logging.info("OK: get_attendance() completado")
        
        if not registros:
            logging.warning("WARNING: No hay registros de asistencia en el dispositivo")
            return []

        logging.info(f"GET: Se encontraron {len(registros)} registros de asistencia")
        
        # Obtener información de usuarios para mapear nombres
        logging.info("USERS: Obteniendo mapeo de usuarios...")
        user_map = obtener_usuarios(conn)
        logging.info(f"USERS: Se mapearon {len(user_map)} usuarios")
        
        logging.info("SYNC: Procesando registros...")
        data = []
        registros_filtrados = 0  # Contador de registros filtrados
        for i, r in enumerate(registros):
            try:
                # Verificar progreso cada 10 registros
                if i > 0 and i % 10 == 0:
                    logging.info(f"SYNC: Procesados {i}/{len(registros)} registros...")
                
                # FILTRO: Validar que el user_id tenga más de 5 dígitos
                if not validar_user_id(r.user_id):
                    registros_filtrados += 1
                    logging.debug(f"FILTER: Registro filtrado - user_id '{r.user_id}' tiene menos de 6 dígitos")
                    continue
                
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
                    logging.info(f"TEST: Registro {i+1}: Usuario {registro_data['user_id']} - {registro_data['nombre']} - {registro_data['timestamp']}")
                    
            except Exception as reg_error:
                logging.error(f"ERROR: Error procesando registro {i}: {reg_error}")
                continue
        
        # Log de resultados del filtrado
        logging.info(f"FILTER: Se filtraron {registros_filtrados} registros con user_id de menos de 6 dígitos")
        logging.info(f"OK: Se procesaron {len(data)} registros válidos de {len(registros)} registros totales")
        return data
        
    except Exception as e:
        logging.error(f"ERROR: Error al obtener registros: {e}")
        import traceback
        logging.error(f"DATA: Detalles del error: {traceback.format_exc()}")
        return []

def enviar_datos(data, server_url, token=None):
    logging.info(f"SEND: Enviando {len(data)} registros a {server_url}...")
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    try:
        resp = requests.post(server_url, json=data, headers=headers, timeout=30)
        logging.info(f"📨 Código de respuesta: {resp.status_code}")
        if resp.status_code == 200:
            logging.info("OK: Datos enviados correctamente")
            return True
        else:
            logging.warning(f"ERROR: Error en la respuesta del servidor: {resp.text}")
            return False
    except Exception as e:
        logging.error(f"ERROR: Error al enviar datos: {e}")
        return False

def main_cycle():
    """Ciclo principal de sincronización"""
    # Forzar actualización de configuración desde la UI antes de cada ciclo
    try:
        if 'app' in globals() and app and hasattr(app, 'update_config_from_ui'):
            logging.info("CONFIG: Actualizando configuración desde la interfaz...")
            if app.update_config_from_ui():
                logging.info("CONFIG: ✅ Configuración actualizada correctamente desde la UI")
            else:
                logging.warning("CONFIG: ⚠️ Error al actualizar configuración desde la UI")
    except Exception as config_error:
        logging.warning(f"CONFIG: Error al actualizar configuración: {config_error}")
    
    # Verificar configuración completa
    if not config_data['IP_BIOMETRICO'] or not config_data['NOMBRE_ESTACION']:
        logging.error("ERROR: Configuración incompleta (falta IP o nombre de estación)")
        return False

    # Logs de configuración actual para verificación
    logging.info(f"INICIO: Iniciando ciclo de sincronización para {config_data['NOMBRE_ESTACION']}")
    logging.info(f"TARGET: Objetivo: {config_data['IP_BIOMETRICO']}:{config_data['PUERTO_BIOMETRICO']}")
    logging.info(f"SERVER: URL del servidor: {config_data['SERVER_URL']}")
    logging.info(f"TOKEN: Token API configurado: {'Sí' if config_data.get('TOKEN_API') else 'No'}")
    logging.info(f"INTERVAL: Intervalo de sincronización: {config_data.get('INTERVALO_MINUTOS', 5)} minutos")
    
    # Verificar conectividad básica
    tcp_success, tcp_msg = test_tcp_port(config_data['IP_BIOMETRICO'], config_data['PUERTO_BIOMETRICO'])
    if not tcp_success:
        logging.warning(f"WARNING: Problema de conectividad: {tcp_msg}")

    logging.info("DEVICE: Estableciendo conexión con el dispositivo...")
    conn = conectar_dispositivo(config_data['IP_BIOMETRICO'], config_data['PUERTO_BIOMETRICO'])
    if not conn:
        logging.error("ERROR: No se pudo establecer conexión con el dispositivo")
        return False

    try:
        # Obtener información del dispositivo
        try:
            logging.info("INFO: Obteniendo información del dispositivo...")
            users_count = len(conn.get_users() or [])
            logging.info(f"USERS: Usuarios registrados en el dispositivo: {users_count}")
        except Exception as info_error:
            logging.warning(f"WARNING: No se pudo obtener información del dispositivo: {info_error}")

        # Obtener registros
        logging.info("RECORDS: Iniciando obtención de registros...")
        try:
            regs = obtener_registros_crudos(conn, config_data['NOMBRE_ESTACION'])
            logging.info(f"GET: Obtención de registros completada: {len(regs)} registros")
        except Exception as reg_error:
            logging.error(f"ERROR: Error durante obtención de registros: {reg_error}")
            regs = []
        
        success = True
        if regs:
            logging.info(f"SEND: Preparando envío de {len(regs)} registros al servidor...")
            logging.info(f"SEND: 🌐 URL del servidor que se va a usar: {config_data['SERVER_URL']}")
            logging.info(f"SEND: 🔑 Token API configurado: {'Sí (' + str(len(config_data['TOKEN_API'])) + ' caracteres)' if config_data.get('TOKEN_API') else 'No'}")
            try:
                success = enviar_datos(regs, config_data['SERVER_URL'], config_data['TOKEN_API'])
                if success:
                    logging.info("OK: ✅ Envío de datos completado exitosamente")
                else:
                    logging.error("ERROR: ❌ Error en el envío de datos")
            except Exception as send_error:
                logging.error(f"ERROR: ❌ Error enviando datos: {send_error}")
                success = False
        else:
            logging.info("🟡 No hay datos para enviar en este ciclo")
            
        return success
            
    except Exception as cycle_error:
        logging.error(f"ERROR: Error durante el ciclo de sincronización: {cycle_error}")
        import traceback
        logging.error(f"DATA: Detalles del error: {traceback.format_exc()}")
        return False
        
    finally:
        try:
            logging.info("DEVICE: Cerrando conexión con el dispositivo...")
            conn.enable_device()
            conn.disconnect()
            logging.info("OK: Dispositivo habilitado y desconectado correctamente")
        except Exception as e:
            logging.error(f"ERROR: Error al desconectar: {e}")
        
        logging.info("🏁 Ciclo de sincronización completado")

def sync_worker(stop_event=None):
    """Worker que ejecuta la sincronización automática"""
    try:
        logging.info("SYNC: Worker de sincronización iniciado")
        
        # Ejecutar primer ciclo inmediatamente
        if config_data['sync_running']:
            try:
                logging.info("INICIO: === INICIANDO PRIMER CICLO DE SINCRONIZACIÓN ===")
                start_time = time.time()
                
                success = main_cycle()
                
                end_time = time.time()
                duration = end_time - start_time
                if success:
                    logging.info(f"⏱️ Primer ciclo completado exitosamente en {duration:.2f} segundos")
                else:
                    logging.warning(f"⏱️ Primer ciclo completado con errores en {duration:.2f} segundos")
            except Exception as e:
                logging.exception(f"ERROR: Error en primer ciclo: {e}")
        
        # Continuar con ciclos periódicos
        while config_data['sync_running']:
            try:
                intervalo = config_data.get('INTERVALO_MINUTOS', 5)
                logging.info(f"⏱️ Esperando {intervalo} minutos para la siguiente ejecución...")
                
                # Usar threading.Event para espera interrumpible
                total_seconds = intervalo * 60
                if stop_event:
                    # Esperar usando el event, que puede ser interrumpido
                    if stop_event.wait(timeout=total_seconds):
                        # El event fue activado, significa que debemos parar
                        logging.info("🛑 Sincronización detenida durante la espera")
                        return  # Salir del worker completamente
                else:
                    # Fallback al método anterior si no hay stop_event
                    for i in range(total_seconds):
                        if not config_data['sync_running']:
                            logging.info("🛑 Sincronización detenida durante la espera")
                            return  # Salir del worker completamente
                        
                        # Log cada minuto durante la espera
                        if i > 0 and i % 60 == 0:
                            remaining_minutes = (total_seconds - i) // 60
                            logging.info(f"WAIT: Esperando... {remaining_minutes} minutos restantes")
                        
                        time.sleep(1)
                
                # Si aún está corriendo, ejecutar siguiente ciclo
                if config_data['sync_running']:
                    logging.info("INICIO: === INICIANDO NUEVO CICLO DE SINCRONIZACIÓN ===")
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
                        logging.exception(f"ERROR: Error en ciclo de sincronización: {cycle_error}")
                        # Continuar con el siguiente ciclo después del error
                    
            except Exception as e:
                logging.exception(f"ERROR: Error inesperado en el bucle principal: {e}")
                if config_data['sync_running']:
                    logging.info(f"⏱️ Reiniciando en {config_data.get('INTERVALO_MINUTOS', 5)} minutos...")
                    # Esperar antes de reintentar usando stop_event si está disponible
                    retry_seconds = config_data.get('INTERVALO_MINUTOS', 5) * 60
                    if stop_event:
                        if stop_event.wait(timeout=retry_seconds):
                            return  # Parar si se activó el event
                    else:
                        # Fallback al método anterior
                        for i in range(retry_seconds):
                            if not config_data['sync_running']:
                                return
                            time.sleep(1)
    
    except Exception as fatal_error:
        logging.exception(f"ERROR: Error fatal en worker de sincronización: {fatal_error}")
    finally:
        logging.info("🏁 Worker de sincronización finalizado")
        # Asegurar que la interfaz se actualice correctamente al salir
        config_data['sync_running'] = False

# ————— Funciones para bandeja del sistema —————
def create_tray_icon():
    """Crea un icono para la bandeja del sistema"""
    try:
        # Crear una imagen simple para el icono
        width = height = 64
        image = Image.new('RGB', (width, height), (52, 152, 219))  # Azul moderno
        draw = ImageDraw.Draw(image)
        
        # Dibujar un círculo blanco en el centro
        margin = 8
        draw.ellipse([margin, margin, width-margin, height-margin], fill=(255, 255, 255))
        
        # Dibujar las letras "SB" (Sync Bio) en el centro
        try:
            from PIL import ImageFont
            # Intentar usar una fuente más grande
            font = ImageFont.load_default()
        except:
            font = None
        
        # Calcular posición del texto
        text = "SB"
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(text) * 6
            text_height = 11
        
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2
        
        draw.text((text_x, text_y), text, fill=(52, 152, 219), font=font)
        
        return image
        
    except Exception as e:
        logging.warning(f"WARNING: Error creando icono de bandeja personalizado: {e}")
        # Crear un icono simple de respaldo
        width = height = 64
        image = Image.new('RGB', (width, height), (52, 152, 219))
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill=(255, 255, 255))
        return image

class SyncBioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sincronización Biométrica Mejorada")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.sync_thread = None
        self.tray_icon = None
        self.tray_thread = None
        self.hidden = False
        self.watchdog_active = False
        self.ui_ready = False
        self.stop_event = threading.Event()  # Añadir Event para comunicación entre hilos
        
        # Cargar configuración
        load_config()
        
        # Verificar y sincronizar el estado del inicio automático con Windows
        startup_enabled = is_startup_enabled()
        if startup_enabled != config_data.get('START_WITH_WINDOWS', False):
            config_data['START_WITH_WINDOWS'] = startup_enabled
            save_config()
            logging.info(f"STARTUP: Estado de inicio automatico sincronizado: {startup_enabled}")
        
        # Configurar la UI primero
        self.setup_ui()
        self.ui_ready = True
        
        # Configurar guardado automático periódico (cada 5 minutos)
        self.schedule_auto_save()
        
        # Configurar bandeja del sistema después de que la UI esté lista
        # Usar after para programar la configuración de bandeja
        self.root.after(1000, self.setup_tray)
        
        # Auto-iniciar si está configurado
        if config_data.get('AUTO_START', False):
            self.root.after(2000, self.start_sync)  # Iniciar después de 2 segundos
    
    def schedule_auto_save(self):
        """Programa el auto-guardado periódico de configuración"""
        def periodic_auto_save():
            try:
                auto_save_config()
                logging.debug("CONFIG: Auto-guardado periódico ejecutado")
            except Exception as e:
                logging.warning(f"WARNING: Error en auto-guardado periódico: {e}")
            finally:
                # Reprogramar para dentro de 5 minutos (300000 ms)
                self.root.after(300000, periodic_auto_save)
        
        # Iniciar el primer auto-guardado en 5 minutos
        self.root.after(300000, periodic_auto_save)
    
    def setup_tray(self):
        """Configura el icono de la bandeja del sistema de manera no bloqueante"""
        # TEMPORAL: Deshabilitar bandeja del sistema para evitar bloqueos en PyInstaller
        if False:  # config_data.get('MINIMIZE_TO_TRAY', True):
            try:
                logging.info("TRAY: Configurando icono de bandeja del sistema...")
                
                # Configurar el comportamiento de cierre de ventana primero
                self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
                
                # Crear el icono en un hilo separado para evitar bloqueos
                def create_tray_in_thread():
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
                        
                        logging.info("TRAY: Icono de bandeja creado correctamente")
                        
                        # Ejecutar el icono de bandeja (esto es bloqueante)
                        self.tray_icon.run()
                        
                    except Exception as e:
                        logging.error(f"ERROR: Error en hilo de bandeja: {e}")
                        self.tray_icon = None
                
                # Iniciar el hilo de bandeja
                self.tray_thread = threading.Thread(target=create_tray_in_thread, daemon=True)
                self.tray_thread.start()
                
                # Dar tiempo para que se inicialice
                time.sleep(0.5)
                
                logging.info("TRAY: Hilo de bandeja iniciado correctamente")
                
            except Exception as e:
                logging.error(f"ERROR: No se pudo configurar la bandeja del sistema: {e}")
                self.tray_icon = None
                # Configurar solo el comportamiento de cierre
                self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        else:
            logging.info("TRAY: Bandeja del sistema DESHABILITADA para evitar bloqueos en PyInstaller")
            # Solo configurar el comportamiento de cierre
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.tray_icon = None
    
    def show_window(self, icon=None, item=None):
        """Muestra la ventana principal"""
        try:
            if self.ui_ready:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                self.hidden = False
                logging.info("TRAY: Ventana mostrada desde bandeja")
            else:
                logging.warning("TRAY: UI no está lista para mostrar")
        except Exception as e:
            logging.error(f"ERROR: Error mostrando ventana: {e}")
    
    def hide_window(self, icon=None, item=None):
        """Oculta la ventana principal"""
        try:
            if self.ui_ready:
                self.root.withdraw()
                self.hidden = True
                logging.info("TRAY: Ventana ocultada a bandeja")
            else:
                logging.warning("TRAY: UI no está lista para ocultar")
        except Exception as e:
            logging.error(f"ERROR: Error ocultando ventana: {e}")
    
    def tray_start_sync(self, icon=None, item=None):
        """Inicia sincronización desde la bandeja"""
        try:
            if not config_data['sync_running']:
                logging.info("TRAY: Iniciando sincronización desde bandeja")
                self.start_sync()
        except Exception as e:
            logging.error(f"ERROR: Error iniciando sync desde bandeja: {e}")
    
    def tray_stop_sync(self, icon=None, item=None):
        """Detiene sincronización desde la bandeja"""
        try:
            if config_data['sync_running']:
                logging.info("TRAY: Deteniendo sincronización desde bandeja")
                self.stop_sync()
        except Exception as e:
            logging.error(f"ERROR: Error deteniendo sync desde bandeja: {e}")
    
    def schedule_auto_save(self):
        """Programa el auto-guardado periódico de configuración"""
        def periodic_auto_save():
            try:
                auto_save_config()
                logging.debug("CONFIG: Auto-guardado periódico ejecutado")
            except Exception as e:
                logging.warning(f"WARNING: Error en auto-guardado periódico: {e}")
            finally:
                # Reprogramar para dentro de 5 minutos (300000 ms)
                self.root.after(300000, periodic_auto_save)
        
        # Iniciar el primer auto-guardado en 5 minutos
        self.root.after(300000, periodic_auto_save)
    
    def quit_app(self, icon=None, item=None):
        """Cierra completamente la aplicación"""
        try:
            logging.info("SYSTEM: Cerrando aplicación completamente...")
            logging.info("SYSTEM: Iniciando cierre de aplicación...")
            
            # Verificar si la sincronización está corriendo
            sync_was_running = config_data.get('sync_running', False)
            thread_is_alive = hasattr(self, 'sync_thread') and self.sync_thread and self.sync_thread.is_alive()
            
            if sync_was_running or thread_is_alive:
                logging.info("SYSTEM: Deteniendo sincronización antes del cierre...")
                
                # Activar stop_event para interrumpir inmediatamente cualquier espera
                if hasattr(self, 'stop_event'):
                    self.stop_event.set()
                    logging.info("SYSTEM: Stop event activado para terminación inmediata")
                
                # Solo llamar stop_sync si realmente está corriendo
                if sync_was_running:
                    # Detener sincronización sin wait_for_stop thread adicional durante cierre
                    config_data['sync_running'] = False
                    self.stop_watchdog()
                
                # Esperar a que termine el hilo solo si está vivo
                if thread_is_alive:
                    logging.info("SYSTEM: Esperando a que termine el hilo de sincronización...")
                    self.sync_thread.join(timeout=2.0)  # Reducido a 2 segundos para cierre más rápido
                    
                    if self.sync_thread.is_alive():
                        logging.warning("WARNING: El hilo de sincronización no terminó en el tiempo esperado")
                        # En este punto, el hilo daemon se cerrará automáticamente al salir del programa
                    else:
                        logging.info("OK: Hilo de sincronización terminado correctamente")
                else:
                    logging.info("SYSTEM: Hilo de sincronización ya terminado")
            else:
                logging.info("SYSTEM: No hay sincronización activa para detener")
            
            # Parar watchdog (por si acaso no se hizo arriba)
            self.stop_watchdog()
            
            # Guardar configuración antes de salir
            save_config()
            logging.info("SYSTEM: Configuración guardada antes de salir")
            
            # Cerrar icono de bandeja
            if self.tray_icon:
                logging.info("TRAY: Cerrando icono de bandeja...")
                try:
                    self.tray_icon.stop()
                    self.tray_icon = None
                except Exception as tray_error:
                    logging.warning(f"WARNING: Error cerrando bandeja: {tray_error}")
            
            # Cerrar ventana principal
            logging.info("SYSTEM: Cerrando interfaz gráfica...")
            self.root.quit()
            self.root.destroy()
            
            logging.info("SYSTEM: Aplicación cerrada completamente")
            
        except Exception as e:
            logging.error(f"ERROR: Error durante el cierre de la aplicación: {e}")
            try:
                # Intento forzado de cierre
                if hasattr(self, 'stop_event'):
                    self.stop_event.set()  # Asegurar que se active el stop event
                self.root.quit()
                self.root.destroy()
            except:
                pass
    
    def on_closing(self):
        """Maneja el cierre de la ventana principal"""
        try:
            # Verificar si hay sincronización activa
            sync_running = config_data.get('sync_running', False)
            thread_alive = hasattr(self, 'sync_thread') and self.sync_thread and self.sync_thread.is_alive()
            
            if sync_running or thread_alive:
                logging.info("SYSTEM: Detectada sincronización activa durante cierre por botón X")
                
                # Activar stop_event inmediatamente para acelerar el cierre
                if hasattr(self, 'stop_event'):
                    self.stop_event.set()
                    logging.info("SYSTEM: Stop event activado preventivamente")
                
                # Usar after() para evitar bloqueo del main thread
                def show_dialog():
                    try:
                        from tkinter import messagebox
                        result = messagebox.askyesnocancel(
                            "Sincronización en progreso",
                            "La sincronización está ejecutándose.\n\n" + 
                            "¿Desea detener la sincronización y cerrar la aplicación?\n\n" +
                            "• Sí: Detener sincronización y cerrar\n" +
                            "• No: Minimizar a bandeja (si está habilitada)\n" +
                            "• Cancelar: Continuar con la aplicación"
                        )
                        
                        if result is True:  # Sí - Detener y cerrar
                            logging.info("SYSTEM: Usuario eligió detener sincronización y cerrar")
                            self.quit_app()
                        elif result is False:  # No - Minimizar si está disponible
                            if config_data.get('MINIMIZE_TO_TRAY', True) and self.tray_icon:
                                logging.info("SYSTEM: Usuario eligió minimizar a bandeja")
                                self.hide_window()
                            else:
                                logging.info("SYSTEM: Bandeja no disponible, cerrando de todas formas")
                                self.quit_app()
                        else:  # Cancelar - No hacer nada
                            logging.info("SYSTEM: Usuario canceló el cierre")
                            # Reactivar sync si fue cancelado
                            if hasattr(self, 'stop_event'):
                                self.stop_event.clear()
                            return
                    except Exception as e:
                        logging.error(f"ERROR: Error en diálogo de cierre: {e}")
                        # En caso de error en el diálogo, cerrar directamente
                        self.quit_app()
                
                # Mostrar diálogo después de que el main thread esté libre
                self.root.after(100, show_dialog)
                
            else:
                # No hay sincronización activa, proceder normalmente
                logging.info("SYSTEM: No hay sincronización activa, procediendo con cierre normal")
                if config_data.get('MINIMIZE_TO_TRAY', True) and self.tray_icon:
                    # Minimizar a bandeja en lugar de cerrar
                    logging.info("TRAY: Minimizando a bandeja del sistema...")
                    self.hide_window()
                else:
                    # Cerrar completamente
                    logging.info("SYSTEM: Cerrando aplicación completamente...")
                    self.quit_app()
                    
        except Exception as e:
            logging.error(f"ERROR: Error en cierre de ventana: {e}")
            # En caso de error, forzar cierre inmediatamente
            logging.info("SYSTEM: Forzando cierre debido a error")
            try:
                if hasattr(self, 'stop_event'):
                    self.stop_event.set()
                config_data['sync_running'] = False
                self.root.quit()
                self.root.destroy()
            except:
                pass
    
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
        
        # Segunda fila de opciones
        options_frame2 = ttk.Frame(config_frame)
        options_frame2.pack(fill=tk.X, pady=5)
        
        self.start_with_windows_var = tk.BooleanVar(value=config_data.get('START_WITH_WINDOWS', False))
        start_windows_check = ttk.Checkbutton(options_frame2, text="Iniciar con Windows (arranque automático)", 
                                            variable=self.start_with_windows_var,
                                            command=self.toggle_windows_startup)
        start_windows_check.pack(side=tk.LEFT)
        
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
        
        self.hide_button = ttk.Button(control_buttons_frame, text="Minimizar a Bandeja", 
                                     command=self.hide_window)
        self.hide_button.pack(side=tk.LEFT)
        
        # Estado
        status_frame = ttk.LabelFrame(main_frame, text="Estado", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Detenido")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     font=("Arial", 11, "bold"))
        self.status_label.pack()
        
        # Frame de herramientas de desarrollo
        dev_frame = ttk.LabelFrame(main_frame, text="Herramientas de Desarrollo", padding="10")
        dev_frame.pack(fill=tk.X, pady=(0, 10))
        
        dev_buttons_frame = ttk.Frame(dev_frame)
        dev_buttons_frame.pack(fill=tk.X)
        
        self.compile_button = ttk.Button(dev_buttons_frame, text="Compilar a EXE", 
                                        command=self.open_compile_dialog)
        self.compile_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.startup_manager_button = ttk.Button(dev_buttons_frame, text="Gestor de Startup", 
                                               command=self.open_startup_manager)
        self.startup_manager_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.open_project_button = ttk.Button(dev_buttons_frame, text="Abrir Proyecto", 
                                            command=self.open_project_folder)
        self.open_project_button.pack(side=tk.LEFT)
        
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
            config_data['START_WITH_WINDOWS'] = self.start_with_windows_var.get()
            
            # Auto-guardar inmediatamente después de actualizar
            auto_save_config()
            
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
        self.start_with_windows_var.set(config_data.get('START_WITH_WINDOWS', False))
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
                message += f"PING: Ping: {'OK:' if ping_result.get('success') else 'ERROR:'} {ping_result.get('message', 'N/A')}\n"
                
                # TCP
                tcp_result = results.get('tcp', {})
                message += f"DEVICE: Puerto TCP: {'OK:' if tcp_result.get('success') else 'ERROR:'} {tcp_result.get('message', 'N/A')}\n"
                
                # Dispositivo
                device_result = results.get('device', {})
                if device_result.get('success'):
                    info = device_result.get('info', {})
                    message += f"DEVICE: Dispositivo: OK: Conectado\n"
                    message += f"   Nombre: {info.get('name', 'N/A')}\n"
                    message += f"   Firmware: {info.get('firmware', 'N/A')}\n"
                    message += f"   Serie: {info.get('serial', 'N/A')}\n"
                    message += f"   Usuarios: {info.get('users_count', 'N/A')}\n"
                    message += f"   Registros: {info.get('records_count', 'N/A')}\n"
                else:
                    message += f"DEVICE: Dispositivo: ERROR: {device_result.get('error', 'Error desconocido')}\n"
                
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
                logging.info("CONFIG: === EJECUCIÓN MANUAL INICIADA ===")
                success = main_cycle()
                
                if success:
                    logging.info("OK: === EJECUCIÓN MANUAL COMPLETADA EXITOSAMENTE ===")
                    self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                        "Ejecución manual completada exitosamente.\n\nRevisa el log para ver los detalles del proceso."))
                else:
                    logging.warning("WARNING: === EJECUCIÓN MANUAL COMPLETADA CON ERRORES ===")
                    self.root.after(0, lambda: messagebox.showwarning("Completado con errores", 
                        "Ejecución manual completada pero con algunos errores.\n\nRevisa el log para más detalles."))
                    
            except Exception as manual_error:
                logging.error(f"ERROR: Error en ejecución manual: {manual_error}")
                import traceback
                logging.error(f"DATA: Detalles: {traceback.format_exc()}")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Error durante la ejecución manual:\n{manual_error}"))
            finally:
                self.root.after(0, lambda: (
                    self.manual_button.config(state="normal", text="Ejecutar Ahora")
                ))
        
        threading.Thread(target=manual_worker, daemon=True).start()
    
    def toggle_windows_startup(self):
        """Configura o desconfigura el inicio automático con Windows"""
        try:
            enable = self.start_with_windows_var.get()
            logging.info(f"STARTUP: Intentando {'habilitar' if enable else 'deshabilitar'} inicio automatico")
            
            if enable:
                # Habilitar inicio automático
                success = enable_startup()
                if success:
                    config_data['START_WITH_WINDOWS'] = True
                    auto_save_config()  # Guardar inmediatamente
                    logging.info("STARTUP: Inicio automatico con Windows habilitado y guardado")
                    messagebox.showinfo("Inicio Automático", 
                        "La aplicación se configuró para iniciarse automáticamente con Windows.\n\n"
                        "La aplicación se ejecutará cada vez que inicies el sistema.")
                else:
                    logging.error("ERROR: No se pudo habilitar el inicio automatico")
                    messagebox.showerror("Error", 
                        "No se pudo configurar el inicio automático.\n\n"
                        "Verifica que tengas permisos para modificar el registro de Windows.")
                    # Revertir el checkbox si falló
                    self.start_with_windows_var.set(False)
                    config_data['START_WITH_WINDOWS'] = False
            else:
                # Deshabilitar inicio automático
                success = disable_startup()
                if success:
                    config_data['START_WITH_WINDOWS'] = False
                    auto_save_config()  # Guardar inmediatamente
                    logging.info("STARTUP: Inicio automatico con Windows deshabilitado y guardado")
                    messagebox.showinfo("Inicio Automático", 
                        "El inicio automático con Windows ha sido deshabilitado.")
                else:
                    logging.error("ERROR: No se pudo deshabilitar el inicio automatico")
                    messagebox.showerror("Error", 
                        "No se pudo deshabilitar el inicio automático.\n\n"
                        "Verifica que tengas permisos para modificar el registro de Windows.")
                    # Revertir el checkbox si falló
                    self.start_with_windows_var.set(True)
                    config_data['START_WITH_WINDOWS'] = True
                    
        except Exception as e:
            logging.error(f"ERROR: Error configurando inicio automatico: {e}")
            messagebox.showerror("Error", f"Error configurando inicio automático:\n{e}")
            # Revertir el checkbox si hubo error
            self.start_with_windows_var.set(not self.start_with_windows_var.get())
            config_data['START_WITH_WINDOWS'] = self.start_with_windows_var.get()
    
    def start_sync(self):
        """Inicia la sincronización automática"""
        try:
            if not self.validate_inputs():
                return
            
            if not self.update_config_from_ui():
                return
            
            # Verificar que no haya otro hilo corriendo
            if hasattr(self, 'sync_thread') and self.sync_thread and self.sync_thread.is_alive():
                logging.warning("WARNING: Ya hay un hilo de sincronización ejecutándose")
                messagebox.showwarning("Sincronización en progreso", 
                    "Ya hay una sincronización en progreso. Detén la sincronización actual antes de iniciar una nueva.")
                return
            
            # Actualizar configuración global
            config_data['sync_running'] = True
            
            # Reinicializar el stop_event
            self.stop_event = threading.Event()
            
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
                    
                    # Limpiar el event antes de iniciar
                    self.stop_event.clear()
                    
                    # Iniciar el worker de sincronización pasando el event
                    sync_worker(self.stop_event)
                    
                except Exception as e:
                    logging.exception(f"ERROR: Error fatal en worker de inicio: {e}")
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
            
            logging.info(f"INICIO: Sincronización automática iniciada - IP: {config_data['IP_BIOMETRICO']}, "
                        f"Puerto: {config_data['PUERTO_BIOMETRICO']}, "
                        f"Estación: {config_data['NOMBRE_ESTACION']}, "
                        f"Intervalo: {config_data['INTERVALO_MINUTOS']} min")
            
        except Exception as e:
            logging.exception(f"ERROR: Error iniciando sincronización: {e}")
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
            
            # Cambiar el flag para detener el worker y activar event
            config_data['sync_running'] = False
            self.stop_event.set()  # Señalar al hilo que debe terminar
            
            # Actualizar interfaz inmediatamente
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_var.set("Deteniendo...")
            
            # Forzar actualización de la interfaz
            self.root.update_idletasks()
            
            def wait_for_stop():
                """Esperar a que el hilo termine y actualizar interfaz"""
                try:
                    # Esperar a que el hilo termine limpiamente con timeout más corto
                    if hasattr(self, 'sync_thread') and self.sync_thread and self.sync_thread.is_alive():
                        # Esperar máximo 3 segundos en lugar de 10
                        self.sync_thread.join(timeout=3.0)
                        
                        if self.sync_thread.is_alive():
                            logging.warning("WARNING: El hilo de sincronización no terminó en el tiempo esperado")
                            # Nota: No forzamos el cierre del hilo, solo registramos el warning
                    
                    # Limpiar el event para próximo uso
                    self.stop_event.clear()
                    
                    # Actualizar estado final en la interfaz
                    self.root.after(0, lambda: self.status_var.set("Detenido"))
                    logging.info("OK: Sincronización automática detenida correctamente")
                    
                except Exception as e:
                    logging.exception(f"ERROR: Error esperando detención del hilo: {e}")
                    self.root.after(0, lambda: self.status_var.set("Detenido (con advertencias)"))
            
            # Ejecutar la espera en un hilo separado para no bloquear la UI
            threading.Thread(target=wait_for_stop, daemon=True).start()
            
        except Exception as e:
            logging.exception(f"ERROR: Error deteniendo sincronización: {e}")
            # Asegurar que el estado se actualice
            config_data['sync_running'] = False
            self.stop_event.set()
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
                            logging.warning("WARNING: Hilo de sincronización se detuvo inesperadamente")
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
                logging.exception(f"ERROR: Error en watchdog: {e}")
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
            logging.exception(f"ERROR: Error mostrando diagnóstico: {e}")
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
    
    def open_compile_dialog(self):
        """Abre un diálogo para compilar el proyecto a EXE"""
        compile_window = tk.Toplevel(self.root)
        compile_window.title("Compilar a EXE")
        compile_window.geometry("600x500")
        compile_window.resizable(False, False)
        compile_window.transient(self.root)
        compile_window.grab_set()
        
        # Centrar ventana
        compile_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        main_frame = ttk.Frame(compile_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Compilador a Ejecutables", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Opciones de compilación
        options_frame = ttk.LabelFrame(main_frame, text="Opciones de Compilación", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Variables para opciones
        self.compile_main_var = tk.BooleanVar(value=True)
        self.compile_startup_var = tk.BooleanVar(value=True)
        self.compile_installer_var = tk.BooleanVar(value=False)
        self.onefile_var = tk.BooleanVar(value=True)
        self.debug_var = tk.BooleanVar(value=False)
        self.windowed_var = tk.BooleanVar(value=True)
        
        # Checkboxes para componentes
        ttk.Checkbutton(options_frame, text="Compilar Sincronizador Principal", 
                       variable=self.compile_main_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Compilar Gestor de Startup", 
                       variable=self.compile_startup_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Compilar Instalador Completo", 
                       variable=self.compile_installer_var).pack(anchor=tk.W, pady=2)
        
        ttk.Separator(options_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Opciones avanzadas
        ttk.Checkbutton(options_frame, text="Un solo archivo (onefile)", 
                       variable=self.onefile_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Sin ventana de consola (windowed)", 
                       variable=self.windowed_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Incluir información de debug", 
                       variable=self.debug_var).pack(anchor=tk.W, pady=2)
        
        # Frame de salida
        output_frame = ttk.LabelFrame(main_frame, text="Salida de Compilación", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Text widget para mostrar output
        self.compile_output = tk.Text(output_frame, height=15, width=70, font=("Consolas", 8))
        compile_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, 
                                         command=self.compile_output.yview)
        self.compile_output.configure(yscrollcommand=compile_scrollbar.set)
        
        self.compile_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        compile_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_compile_button = ttk.Button(buttons_frame, text="Iniciar Compilación", 
                                              command=lambda: self.start_compilation(compile_window))
        self.start_compile_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="Abrir Carpeta Dist", 
                  command=self.open_dist_folder).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="Cerrar", 
                  command=compile_window.destroy).pack(side=tk.RIGHT)
    
    def start_compilation(self, parent_window):
        """Inicia el proceso de compilación"""
        # Deshabilitar botón durante compilación
        self.start_compile_button.config(state="disabled", text="Compilando...")
        
        # Limpiar output
        self.compile_output.delete('1.0', tk.END)
        
        def compile_thread():
            try:
                # Construir argumentos
                args = []
                
                if self.compile_main_var.get() and not self.compile_startup_var.get() and not self.compile_installer_var.get():
                    args.append("--main-only")
                elif self.compile_startup_var.get() and not self.compile_main_var.get() and not self.compile_installer_var.get():
                    args.append("--startup-only")
                elif self.compile_installer_var.get() and not self.compile_main_var.get() and not self.compile_startup_var.get():
                    args.append("--installer-only")
                
                if not self.onefile_var.get():
                    args.append("--onedir")
                if not self.windowed_var.get():
                    args.append("--console")
                if self.debug_var.get():
                    args.append("--debug")
                
                # Mostrar comando que se va a ejecutar
                self.log_compile_output(f"🔨 Iniciando compilación con argumentos: {' '.join(args)}\n")
                self.log_compile_output("=" * 60 + "\n")
                
                # Ejecutar compilador
                python_exe = sys.executable.replace("python.exe", "python.exe")
                if os.path.exists("env/Scripts/python.exe"):
                    python_exe = "env/Scripts/python.exe"
                
                import subprocess
                cmd = [python_exe, "compilar_sincronizador.py"] + args
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Leer output en tiempo real
                for line in iter(process.stdout.readline, ''):
                    self.log_compile_output(line)
                    parent_window.update()
                
                process.wait()
                
                if process.returncode == 0:
                    self.log_compile_output("\n" + "=" * 60 + "\n")
                    self.log_compile_output("✅ COMPILACIÓN COMPLETADA EXITOSAMENTE\n")
                    self.log_compile_output("Los ejecutables se encuentran en la carpeta 'dist/'\n")
                else:
                    self.log_compile_output("\n" + "=" * 60 + "\n")
                    self.log_compile_output("❌ ERROR EN LA COMPILACIÓN\n")
                    self.log_compile_output(f"Código de error: {process.returncode}\n")
            
            except Exception as e:
                self.log_compile_output(f"\n❌ Error durante la compilación: {e}\n")
            
            finally:
                # Rehabilitar botón
                self.start_compile_button.config(state="normal", text="Iniciar Compilación")
        
        # Ejecutar en hilo separado
        threading.Thread(target=compile_thread, daemon=True).start()
    
    def log_compile_output(self, text):
        """Agregar texto al output de compilación"""
        self.compile_output.insert(tk.END, text)
        self.compile_output.see(tk.END)
        self.compile_output.update()
    
    def open_dist_folder(self):
        """Abre la carpeta dist con los ejecutables"""
        try:
            dist_dir = os.path.abspath("dist")
            if os.path.exists(dist_dir):
                os.startfile(dist_dir)  # Windows
            else:
                messagebox.showwarning("Carpeta no encontrada", 
                                     f"La carpeta dist no existe: {dist_dir}\nPrimero compile el proyecto.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta dist: {e}")
    
    def open_startup_manager(self):
        """Abre el gestor de startup en una nueva ventana"""
        try:
            python_exe = sys.executable
            if os.path.exists("env/Scripts/python.exe"):
                python_exe = "env/Scripts/python.exe"
            
            import subprocess
            subprocess.Popen([python_exe, "startup_manager.py", "--status"], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el gestor de startup: {e}")
    
    def open_project_folder(self):
        """Abre la carpeta del proyecto"""
        try:
            project_dir = os.path.abspath(".")
            os.startfile(project_dir)  # Windows
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta del proyecto: {e}")

# ————— Ejecución principal —————
if __name__ == '__main__':
    try:
        # Configurar logging primero
        setup_logging()
        
        # Cargar configuración al inicio
        load_config()
        
        # Verificar parámetros de línea de comandos
        autostart_mode = '--autostart' in sys.argv
        test_startup_mode = '--test-startup' in sys.argv
        
        # Si es modo de prueba de startup
        if test_startup_mode:
            logging.info("🔧 TESTING: Modo de prueba de startup activado")
            test_results = test_startup_functionality()
            print("\n" + "="*50)
            print("RESULTADOS DE LA PRUEBA DE STARTUP")
            print("="*50)
            for key, value in test_results.items():
                print(f"{key}: {value}")
            print("="*50)
            sys.exit(0)
        
        if autostart_mode:
            logging.info("STARTUP: Aplicacion iniciada desde arranque automatico de Windows")
        
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
            if not autostart_mode:
                messagebox.showwarning("Aplicación ya ejecutándose", 
                    "Ya hay una instancia de la aplicación ejecutándose.\n\n"
                    "Busca el icono en la bandeja del sistema o cierra la aplicación anterior.")
            sys.exit(1)
        
        # Crear y ejecutar la aplicación
        root = tk.Tk()
        app = SyncBioApp(root)
        
        # Si se inició desde Windows startup, configurar comportamiento especial
        if autostart_mode:
            logging.info("="*60)
            logging.info("STARTUP: MODO AUTOSTART ACTIVADO")
            logging.info("="*60)
            logging.info(f"STARTUP: Configuración actual:")
            logging.info(f"  - AUTO_START: {config_data.get('AUTO_START', False)}")
            logging.info(f"  - MINIMIZE_TO_TRAY: {config_data.get('MINIMIZE_TO_TRAY', True)}")
            logging.info(f"  - START_WITH_WINDOWS: {config_data.get('START_WITH_WINDOWS', False)}")
            logging.info(f"  - IP_BIOMETRICO: {config_data.get('IP_BIOMETRICO', 'No configurado')}")
            logging.info(f"  - INTERVALO_MINUTOS: {config_data.get('INTERVALO_MINUTOS', 5)}")
            
            # Actualizar configuración para indicar que estamos en modo autostart
            config_data['_autostart_mode'] = True
            
            # Iniciar sincronización automáticamente si está configurado
            if config_data.get('AUTO_START', False):
                logging.info("STARTUP: ✅ Sincronización automática HABILITADA - iniciando en 3 segundos")
                root.after(3000, app.start_sync)  # Iniciar después de 3 segundos
            else:
                logging.info("STARTUP: ⚠️  Sincronización automática DESHABILITADA")
            
            # Minimizar a bandeja automáticamente
            if config_data.get('MINIMIZE_TO_TRAY', True):
                logging.info("STARTUP: ✅ Minimización a bandeja HABILITADA - minimizando en 5 segundos")
                root.after(5000, app.hide_window)  # Minimizar después de 5 segundos
            else:
                logging.info("STARTUP: ⚠️  Minimización a bandeja DESHABILITADA - la ventana permanecerá visible")
            
            logging.info("="*60)
        else:
            logging.info("NORMAL: Aplicación iniciada en modo normal (no autostart)")
        
        logging.info("SYSTEM: Interfaz grafica iniciada")
        
        # Ejecutar la aplicación
        root.mainloop()
        
    except KeyboardInterrupt:
        logging.warning("⚡ Ejecución interrumpida por el usuario")
    except Exception as e:
        logging.exception(f"ERROR: Error inesperado en la aplicación: {e}")
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
