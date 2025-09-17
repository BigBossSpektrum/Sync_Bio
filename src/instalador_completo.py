import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import sys
import os
import json
import threading
import urllib.request
import urllib.parse
import shutil
import zipfile
import platform
import requests
from pathlib import Path
import time
from datetime import datetime
import tempfile

# Importaciones para bandeja del sistema
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# Importaciones específicas por plataforma
if platform.system() == 'Windows':
    import msvcrt
    import winreg
else:
    import fcntl

class InstaladorCompleto:
    def __init__(self):
        # Verificar si ya hay una instancia ejecutándose
        if not self.verificar_instancia_unica():
            # Salir silenciosamente sin mostrar ninguna ventana
            sys.exit(0)
        
        # Variables de configuración (definir ANTES de usar)
        self.config_path = "../config/biometrico_config.json"
        self.config = self.cargar_configuracion()
        self.lock_file_path = None
        
        # Variables para system tray
        self.tray_icon = None
        self.window_visible = True
        
        self.root = tk.Tk()
        self.root.title("Instalador Sincronizador Biométrico")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Verificar si debe iniciarse minimizado (solo cuando viene del startup con --startup)
        self.inicio_desde_startup = '--startup' in sys.argv
        if self.inicio_desde_startup and self.config.get("MINIMIZE_TO_TRAY", True):
            self.root.withdraw()  # Ocultar ventana al inicio
            self.window_visible = False
            if TRAY_AVAILABLE:
                self.crear_system_tray()
        else:
            self.window_visible = True
            # Crear system tray si está habilitado, incluso cuando se ejecuta manualmente
            if self.config.get("MINIMIZE_TO_TRAY", True) and TRAY_AVAILABLE:
                self.crear_system_tray()
        
        # Configurar el cierre de la aplicación
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        
        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Crear pestañas
        self.crear_pestana_instalacion()
        self.crear_pestana_configuracion_general()
        self.crear_pestana_configuracion_biometrico()
        self.crear_pestana_sincronizacion()
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def verificar_instancia_unica(self):
        """Verificar que solo hay una instancia de la aplicación ejecutándose"""
        try:
            # Usar un archivo de bloqueo simple
            lock_file_path = os.path.join(tempfile.gettempdir(), "instalador_biometrico.lock")
            
            # Verificar si el archivo ya existe y contiene un PID válido
            if os.path.exists(lock_file_path):
                try:
                    with open(lock_file_path, 'r') as f:
                        existing_pid = int(f.read().strip())
                    
                    # Verificar si el proceso aún existe
                    if platform.system() == 'Windows':
                        import subprocess
                        try:
                            # En Windows, usar tasklist para verificar si el PID existe
                            result = subprocess.run(['tasklist', '/FI', f'PID eq {existing_pid}'], 
                                                  capture_output=True, text=True, timeout=5)
                            if f'{existing_pid}' in result.stdout:
                                # El proceso aún existe, intentar traer la ventana al frente
                                try:
                                    import win32gui
                                    import win32con
                                    
                                    def enum_windows_callback(hwnd, windows):
                                        if win32gui.IsWindowVisible(hwnd):
                                            window_text = win32gui.GetWindowText(hwnd)
                                            if "Instalador Sincronizador Biométrico" in window_text:
                                                windows.append(hwnd)
                                        return True
                                    
                                    windows = []
                                    win32gui.EnumWindows(enum_windows_callback, windows)
                                    
                                    if windows:
                                        # Traer la ventana al frente
                                        hwnd = windows[0]
                                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                                        win32gui.SetForegroundWindow(hwnd)
                                        win32gui.BringWindowToTop(hwnd)
                                except ImportError:
                                    # Si win32gui no está disponible, continuar silenciosamente
                                    pass
                                except Exception:
                                    # Si hay algún error trayendo la ventana al frente, continuar silenciosamente
                                    pass
                                
                                return False  # El proceso aún existe
                        except:
                            pass  # Si falla, asumir que el proceso no existe
                    else:
                        # En Unix-like, verificar si el PID existe
                        try:
                            os.kill(existing_pid, 0)
                            return False  # El proceso aún existe
                        except OSError:
                            pass  # El proceso no existe
                            
                    # Si llegamos aquí, el proceso no existe, eliminar el archivo
                    os.remove(lock_file_path)
                except (ValueError, FileNotFoundError):
                    # Archivo corrupto o no existe, continuar
                    pass
            
            # Crear el archivo de bloqueo con nuestro PID
            with open(lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            
            self.lock_file_path = lock_file_path
            return True
            
        except Exception as e:
            print(f"Error verificando instancia única: {e}")
            return True  # En caso de error, permitir ejecución
    
    def liberar_lock(self):
        """Liberar el archivo de bloqueo"""
        try:
            if hasattr(self, 'lock_file_path') and os.path.exists(self.lock_file_path):
                os.remove(self.lock_file_path)
        except Exception as e:
            print(f"Error liberando lock: {e}")
    
    def cerrar_aplicacion(self):
        """Manejar el cierre de la aplicación"""
        try:
            # Si está activada la opción de minimizar a la bandeja y hay tray disponible
            if self.config.get("MINIMIZE_TO_TRAY", True) and TRAY_AVAILABLE:
                self.root.withdraw()
                self.window_visible = False
                if not self.tray_icon:
                    self.crear_system_tray()
                return
            # Si no, cerrar completamente
            self.cerrar_aplicacion_completa()
        except Exception as e:
            print(f"Error cerrando aplicación: {e}")
            self.root.destroy()
    
    def crear_system_tray(self):
        """Crear icono en la bandeja del sistema"""
        if not TRAY_AVAILABLE:
            return
        
        def crear_imagen():
            # Crear una imagen simple para el icono
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color='blue')
            draw = ImageDraw.Draw(image)
            
            # Dibujar un círculo simple
            draw.ellipse([16, 16, 48, 48], fill='white')
            draw.ellipse([20, 20, 44, 44], fill='blue')
            
            return image
        
        def mostrar_ventana(icon, item):
            self.mostrar_ventana()
        
        def salir_aplicacion(icon, item):
            self.cerrar_aplicacion_completa()
        
        # Crear menú
        menu = pystray.Menu(
            pystray.MenuItem("Mostrar", mostrar_ventana, default=True),
            pystray.MenuItem("Salir", salir_aplicacion)
        )
        
        # Crear icono
        image = crear_imagen()
        self.tray_icon = pystray.Icon("SincronizadorBiometrico", image, 
                                      "Sincronizador Biométrico", menu)
        
        # Ejecutar en hilo separado
        def ejecutar_tray():
            self.tray_icon.run()
        
        threading.Thread(target=ejecutar_tray, daemon=True).start()
    
    def mostrar_ventana(self):
        """Mostrar la ventana principal"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.window_visible = True
    
    def cerrar_aplicacion_completa(self):
        """Cerrar completamente la aplicación incluyendo system tray"""
        try:
            # Detener sincronización si está ejecutándose
            if hasattr(self, 'sync_running') and self.sync_running:
                self.sync_running = False
                if hasattr(self, 'sync_log_text'):
                    self.log_message("Aplicación cerrándose, deteniendo sincronización...", self.sync_log_text)
            
            # Detener system tray
            if self.tray_icon:
                self.tray_icon.stop()
            
            # Liberar el archivo de bloqueo
            self.liberar_lock()
            
            # Cerrar la ventana
            self.root.destroy()
            
        except Exception as e:
            print(f"Error cerrando aplicación completa: {e}")
            if hasattr(self, 'root'):
                self.root.destroy()
    
    def configurar_startup_windows(self, activar):
        """Configurar startup en Windows"""
        if platform.system() != 'Windows':
            return False
            
        try:
            # Obtener la ruta del ejecutable actual
            if getattr(sys, 'frozen', False):
                # Ejecutable compilado (.exe) - usar ruta absoluta
                exe_path = os.path.abspath(sys.executable)
                app_path = f'"{exe_path}" --startup'
            else:
                # Script Python
                script_path = os.path.abspath(__file__)
                python_path = sys.executable
                app_path = f'"{python_path}" "{script_path}" --startup'
            
            # Clave del registro para startup
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "SincronizadorBiometrico"
            
            if activar:
                try:
                    # Crear o abrir la clave de registro
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                    print(f"✅ Agregado al startup exitosamente: {app_path}")
                    
                    # Verificar que se guardó correctamente
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                        value, _ = winreg.QueryValueEx(key, app_name)
                        print(f"✅ Verificación: {value}")
                        
                    return True
                except Exception as e:
                    print(f"❌ Error agregando al startup: {e}")
                    return False
            else:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, app_name)
                    print(f"✅ Removido del startup exitosamente")
                    return True
                except FileNotFoundError:
                    print(f"✅ Entrada no existía en startup (esto es normal)")
                    return True
                except Exception as e:
                    print(f"❌ Error quitando del startup: {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error configurando startup: {e}")
            return False
    
    def verificar_startup_activo(self):
        """Verificar si el programa está en el startup"""
        if platform.system() != 'Windows':
            return False
            
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "SincronizadorBiometrico"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, app_name)
                    print(f"✅ Entrada en startup encontrada: {value}")
                    return True
                except FileNotFoundError:
                    print(f"ℹ️ No hay entrada en startup")
                    return False
                    
        except Exception as e:
            print(f"❌ Error verificando startup: {e}")
            return False
    
    def diagnosticar_startup(self):
        """Diagnosticar problemas con el startup de Windows"""
        print("\n🔍 DIAGNÓSTICO DE STARTUP:")
        print("=" * 50)
        
        try:
            # 1. Verificar si estamos en Windows
            print(f"📋 Sistema operativo: {platform.system()}")
            
            # 2. Verificar ruta del ejecutable
            if getattr(sys, 'frozen', False):
                exe_path = os.path.abspath(sys.executable)
                print(f"📁 Ruta del ejecutable: {exe_path}")
                print(f"📁 Ejecutable existe: {os.path.exists(exe_path)}")
            else:
                print(f"📁 Ejecutándose como script Python")
            
            # 3. Verificar entrada en el registro
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "SincronizadorBiometrico"
            
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                    try:
                        value, _ = winreg.QueryValueEx(key, app_name)
                        print(f"✅ Entrada en registro: {value}")
                        
                        # Verificar si el archivo en la entrada existe
                        import shlex
                        parts = shlex.split(value)
                        if parts:
                            exe_in_registry = parts[0]
                            print(f"📁 Archivo del registro existe: {os.path.exists(exe_in_registry)}")
                            
                    except FileNotFoundError:
                        print(f"❌ No hay entrada en el registro de startup")
                        
            except Exception as e:
                print(f"❌ Error accediendo al registro: {e}")
            
            # 4. Verificar configuración
            print(f"⚙️ AUTO_START en config: {self.config.get('AUTO_START', False)}")
            print(f"⚙️ MINIMIZE_TO_TRAY en config: {self.config.get('MINIMIZE_TO_TRAY', True)}")
            
            # 5. Verificar argumentos actuales
            print(f"📝 Argumentos actuales: {sys.argv}")
            print(f"📝 Viene del startup: {'--startup' in sys.argv}")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error en diagnóstico: {e}")
    
    def probar_startup_manual(self):
        """Probar el startup ejecutando el programa como si viniera del inicio de Windows"""
        try:
            if getattr(sys, 'frozen', False):
                exe_path = os.path.abspath(sys.executable)
                comando = f'"{exe_path}" --startup'
                
                print(f"🧪 Probando startup con comando: {comando}")
                
                # Ejecutar el comando en un proceso separado
                import subprocess
                result = subprocess.Popen(comando, shell=True)
                
                messagebox.showinfo("Prueba de Startup", 
                                  f"Se ha iniciado una nueva instancia del programa con --startup\n"
                                  f"Comando: {comando}\n\n"
                                  f"Verifica que se haya iniciado minimizado en la bandeja del sistema.")
                
            else:
                messagebox.showwarning("Prueba de Startup", 
                                     "Esta función solo funciona con el ejecutable compilado (.exe)")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error probando startup: {e}")
            print(f"❌ Error probando startup: {e}")
    
    def verificar_inicio_desde_startup(self):
        """Verificar si el programa fue iniciado desde el startup de Windows"""
        try:
            # Método simple y confiable: verificar si se pasó el argumento --startup
            if '--startup' in sys.argv:
                print(f"✅ Detectado inicio desde startup (argumento --startup presente)")
                return True
                
            # Método adicional: verificar tiempo de arranque del sistema si no hay argumento
            try:
                import time
                import subprocess
                
                # En Windows, verificar tiempo de arranque del sistema
                if platform.system() == 'Windows':
                    # Obtener tiempo de arranque usando systeminfo
                    result = subprocess.run(['systeminfo'], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'System Boot Time' in line or 'Hora de inicio del sistema' in line:
                                # Si han pasado menos de 2 minutos desde el arranque
                                import datetime
                                current_time = time.time()
                                # Asumimos que si no hay argumentos y han pasado menos de 2 minutos, viene del startup
                                if len(sys.argv) == 1:
                                    # Para ser conservadores, no asumir startup sin --startup
                                    pass
                                    
            except Exception:
                pass  # Si falla, continuar
                
            print(f"ℹ️ No detectado inicio desde startup")
            return False
            
        except Exception as e:
            print(f"❌ Error verificando inicio desde startup: {e}")
            return False
        
    def cargar_configuracion(self):
        """Cargar configuración desde archivo JSON"""
        config_default = {
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
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Actualizar con valores por defecto si faltan claves
                    for key, value in config_default.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            messagebox.showwarning("Advertencia", f"Error al cargar configuración: {e}")
        
        return config_default
    
    def guardar_configuracion(self):
        """Guardar configuración en archivo JSON"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar configuración: {e}")
            return False
    
    def crear_pestana_instalacion(self):
        """Crear pestaña de instalación de Python y dependencias"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Instalación")
        
        # Título
        title_label = tk.Label(frame, text="Instalación de Python y Dependencias", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Frame para verificación de Python
        python_frame = ttk.LabelFrame(frame, text="Estado de Python", padding=10)
        python_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.python_status = tk.StringVar()
        self.python_status.set("Verificando...")
        python_label = tk.Label(python_frame, textvariable=self.python_status)
        python_label.pack(anchor=tk.W)
        
        # Botones de Python
        python_buttons_frame = tk.Frame(python_frame)
        python_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.verificar_python_btn = tk.Button(python_buttons_frame, text="Verificar Python", 
                                             command=self.verificar_python)
        self.verificar_python_btn.pack(side=tk.LEFT, padx=5)
        
        self.instalar_python_btn = tk.Button(python_buttons_frame, text="Descargar e Instalar Python", 
                                            command=self.instalar_python, state=tk.DISABLED)
        self.instalar_python_btn.pack(side=tk.LEFT, padx=5)
        
        # Frame para dependencias
        deps_frame = ttk.LabelFrame(frame, text="Dependencias de Python", padding=10)
        deps_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.deps_status = tk.StringVar()
        self.deps_status.set("No verificado")
        deps_label = tk.Label(deps_frame, textvariable=self.deps_status)
        deps_label.pack(anchor=tk.W)
        
        # Botones de dependencias
        deps_buttons_frame = tk.Frame(deps_frame)
        deps_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.verificar_deps_btn = tk.Button(deps_buttons_frame, text="Verificar Dependencias", 
                                           command=self.verificar_dependencias)
        self.verificar_deps_btn.pack(side=tk.LEFT, padx=5)
        
        self.instalar_deps_btn = tk.Button(deps_buttons_frame, text="Instalar Dependencias", 
                                          command=self.instalar_dependencias)
        self.instalar_deps_btn.pack(side=tk.LEFT, padx=5)
        
        # Área de log
        log_frame = ttk.LabelFrame(frame, text="Log de Instalación", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # Verificar Python al inicio
        self.root.after(1000, self.verificar_python)
    
    def crear_pestana_configuracion_general(self):
        """Crear pestaña de configuración general"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Configuración General")
        
        # Título
        title_label = tk.Label(frame, text="Configuración General del Sistema", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Frame principal con scroll
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Token API
        token_frame = ttk.LabelFrame(scrollable_frame, text="Token API", padding=10)
        token_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(token_frame, text="Token de API:").pack(anchor=tk.W)
        self.token_entry = tk.Entry(token_frame, width=50, show="*")
        self.token_entry.pack(fill=tk.X, pady=2)
        self.token_entry.insert(0, self.config.get("TOKEN_API", "") or "")
        
        # Intervalo de sincronización
        intervalo_frame = ttk.LabelFrame(scrollable_frame, text="Configuración de Sincronización", padding=10)
        intervalo_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(intervalo_frame, text="Intervalo de sincronización (minutos):").pack(anchor=tk.W)
        self.intervalo_var = tk.IntVar(value=self.config.get("INTERVALO_MINUTOS", 5))
        intervalo_spin = tk.Spinbox(intervalo_frame, from_=1, to=60, textvariable=self.intervalo_var, width=10)
        intervalo_spin.pack(anchor=tk.W, pady=2)
        
        # Opciones de inicio
        startup_frame = ttk.LabelFrame(scrollable_frame, text="Opciones de Inicio", padding=10)
        startup_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Verificar el estado real del startup y sincronizar con la configuración
        startup_real = self.verificar_startup_activo()
        auto_start_config = self.config.get("AUTO_START", False)
        
        # Si hay discrepancia, usar el estado real del sistema
        if startup_real != auto_start_config:
            self.config["AUTO_START"] = startup_real
            self.guardar_configuracion()
        
        self.auto_start_var = tk.BooleanVar(value=startup_real)
        auto_start_check = tk.Checkbutton(startup_frame, text="Iniciar automáticamente con el sistema", 
                                         variable=self.auto_start_var)
        auto_start_check.pack(anchor=tk.W)
        
        self.minimize_tray_var = tk.BooleanVar(value=self.config.get("MINIMIZE_TO_TRAY", True))
        minimize_tray_check = tk.Checkbutton(startup_frame, text="Minimizar a la bandeja del sistema", 
                                           variable=self.minimize_tray_var)
        minimize_tray_check.pack(anchor=tk.W)
        
        # Botones
        buttons_frame = tk.Frame(scrollable_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        save_btn = tk.Button(buttons_frame, text="Guardar Configuración", 
                           command=self.guardar_config_general, bg="#4CAF50", fg="white")
        save_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(buttons_frame, text="Restablecer", 
                            command=self.restablecer_config_general, bg="#f44336", fg="white")
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón de diagnóstico del startup
        diagnostico_btn = tk.Button(buttons_frame, text="🔍 Diagnosticar Startup", 
                                   command=self.diagnosticar_startup, bg="#2196F3", fg="white")
        diagnostico_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón para probar startup manualmente
        test_startup_btn = tk.Button(buttons_frame, text="🧪 Probar Startup", 
                                    command=self.probar_startup_manual, bg="#FF9800", fg="white")
        test_startup_btn.pack(side=tk.LEFT, padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def crear_pestana_configuracion_biometrico(self):
        """Crear pestaña de configuración del biométrico"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Config. Biométrico")
        
        # Título
        title_label = tk.Label(frame, text="Configuración del Dispositivo Biométrico", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Frame principal
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Configuración de red
        red_frame = ttk.LabelFrame(main_frame, text="Configuración de Red", padding=10)
        red_frame.pack(fill=tk.X, pady=5)
        
        # IP del biométrico
        tk.Label(red_frame, text="IP del Dispositivo Biométrico:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ip_bio_entry = tk.Entry(red_frame, width=20)
        self.ip_bio_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=2)
        self.ip_bio_entry.insert(0, self.config.get("IP_BIOMETRICO", "192.168.1.88"))
        
        # Puerto del biométrico
        tk.Label(red_frame, text="Puerto:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.puerto_bio_var = tk.IntVar(value=self.config.get("PUERTO_BIOMETRICO", 4370))
        puerto_spin = tk.Spinbox(red_frame, from_=1, to=65535, textvariable=self.puerto_bio_var, width=10)
        puerto_spin.grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Configuración de estación
        estacion_frame = ttk.LabelFrame(main_frame, text="Configuración de Estación", padding=10)
        estacion_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(estacion_frame, text="Nombre de la Estación:").pack(anchor=tk.W)
        self.nombre_estacion_entry = tk.Entry(estacion_frame, width=30)
        self.nombre_estacion_entry.pack(anchor=tk.W, pady=2)
        self.nombre_estacion_entry.insert(0, self.config.get("NOMBRE_ESTACION", "Centenario"))
        
        # Test de conexión
        test_frame = ttk.LabelFrame(main_frame, text="Prueba de Conexión", padding=10)
        test_frame.pack(fill=tk.X, pady=5)
        
        test_btn = tk.Button(test_frame, text="Probar Conexión con Biométrico", 
                           command=self.probar_conexion_biometrico, bg="#2196F3", fg="white")
        test_btn.pack(side=tk.LEFT, padx=5)
        
        self.conexion_status = tk.StringVar()
        self.conexion_status.set("No probado")
        conexion_label = tk.Label(test_frame, textvariable=self.conexion_status)
        conexion_label.pack(side=tk.LEFT, padx=10)
        
        # Botones
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        save_bio_btn = tk.Button(buttons_frame, text="Guardar Configuración Biométrica", 
                               command=self.guardar_config_biometrico, bg="#4CAF50", fg="white")
        save_bio_btn.pack(side=tk.LEFT, padx=5)
        
        reset_bio_btn = tk.Button(buttons_frame, text="Restablecer", 
                                command=self.restablecer_config_biometrico, bg="#f44336", fg="white")
        reset_bio_btn.pack(side=tk.LEFT, padx=5)
    
    def crear_pestana_sincronizacion(self):
        """Crear pestaña de sincronización"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Sincronización")
        
        # Título
        title_label = tk.Label(frame, text="Sincronización Biométrica", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Configuración del servidor (solo lectura)
        servidor_frame = ttk.LabelFrame(frame, text="Configuración del Servidor", padding=10)
        servidor_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(servidor_frame, text="URL del Servidor:").pack(anchor=tk.W)
        self.server_url_entry = tk.Entry(servidor_frame, width=60, state='readonly')
        self.server_url_entry.pack(fill=tk.X, pady=2)
        self.server_url_entry.config(state='normal')
        self.server_url_entry.delete(0, tk.END)
        self.server_url_entry.insert(0, self.config.get("SERVER_URL", ""))
        self.server_url_entry.config(state='readonly')
        
        tk.Label(servidor_frame, text="* La URL del servidor no se puede modificar por seguridad", 
                fg="red", font=("Arial", 8)).pack(anchor=tk.W)
        
        # Estado de sincronización
        estado_frame = ttk.LabelFrame(frame, text="Estado de Sincronización", padding=10)
        estado_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.sync_status = tk.StringVar()
        self.sync_status.set("Detenido")
        status_label = tk.Label(estado_frame, textvariable=self.sync_status, font=("Arial", 12, "bold"))
        status_label.pack()
        
        # Controles de sincronización
        control_frame = ttk.LabelFrame(frame, text="Control de Sincronización", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        buttons_sync_frame = tk.Frame(control_frame)
        buttons_sync_frame.pack()
        
        self.start_sync_btn = tk.Button(buttons_sync_frame, text="Iniciar Sincronización", 
                                       command=self.iniciar_sincronizacion, bg="#4CAF50", fg="white")
        self.start_sync_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_sync_btn = tk.Button(buttons_sync_frame, text="Detener Sincronización", 
                                      command=self.detener_sincronizacion, bg="#f44336", fg="white", 
                                      state=tk.DISABLED)
        self.stop_sync_btn.pack(side=tk.LEFT, padx=5)
        
        self.sync_manual_btn = tk.Button(buttons_sync_frame, text="Sincronización Manual", 
                                        command=self.sincronizacion_manual, bg="#FF9800", fg="white")
        self.sync_manual_btn.pack(side=tk.LEFT, padx=5)
        
        # Log de sincronización
        log_sync_frame = ttk.LabelFrame(frame, text="Log de Sincronización", padding=10)
        log_sync_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.sync_log_text = scrolledtext.ScrolledText(log_sync_frame, height=10)
        self.sync_log_text.pack(fill=tk.BOTH, expand=True)
        
        # Variables de control
        self.sync_thread = None
        self.sync_running = False
    
    def log_message(self, message, log_widget=None):
        """Agregar mensaje al log"""
        if log_widget is None:
            log_widget = self.log_text
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        log_widget.insert(tk.END, formatted_message)
        log_widget.see(tk.END)
        self.root.update_idletasks()
    
    def verificar_python(self):
        """Verificar si Python está instalado"""
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.python_status.set(f"✓ Python instalado: {version}")
                self.instalar_python_btn.config(state=tk.DISABLED)
                self.verificar_deps_btn.config(state=tk.NORMAL)
                self.log_message(f"Python verificado: {version}")
                return True
            else:
                raise Exception("Python no encontrado")
        except Exception as e:
            self.python_status.set("✗ Python no está instalado o no está en PATH")
            self.instalar_python_btn.config(state=tk.NORMAL)
            self.verificar_deps_btn.config(state=tk.DISABLED)
            self.log_message(f"Error verificando Python: {e}")
            return False
    
    def instalar_python(self):
        """Descargar e instalar Python"""
        def install_thread():
            try:
                self.progress.start()
                self.status_var.set("Descargando Python...")
                self.log_message("Iniciando descarga de Python...")
                
                # URL de descarga de Python (versión estable)
                python_version = "3.11.9"
                if platform.machine().endswith('64'):
                    python_url = f"https://www.python.org/ftp/python/{python_version}/python-{python_version}-amd64.exe"
                else:
                    python_url = f"https://www.python.org/ftp/python/{python_version}/python-{python_version}.exe"
                
                # Descargar Python
                filename = f"python-{python_version}-installer.exe"
                
                self.log_message(f"Descargando desde: {python_url}")
                urllib.request.urlretrieve(python_url, filename)
                self.log_message("Descarga completada")
                
                # Ejecutar instalador
                self.status_var.set("Instalando Python...")
                self.log_message("Iniciando instalación de Python...")
                
                # Parámetros para instalación silenciosa
                install_cmd = [
                    filename,
                    "/quiet",
                    "InstallAllUsers=1",
                    "PrependPath=1",
                    "Include_test=0"
                ]
                
                process = subprocess.run(install_cmd, timeout=600)  # 10 minutos timeout
                
                if process.returncode == 0:
                    self.log_message("Python instalado exitosamente")
                    self.status_var.set("Python instalado")
                    
                    # Limpiar archivo temporal
                    try:
                        os.remove(filename)
                    except:
                        pass
                    
                    # Verificar instalación
                    self.root.after(2000, self.verificar_python)
                else:
                    raise Exception(f"Error en la instalación (código: {process.returncode})")
                
            except Exception as e:
                self.log_message(f"Error instalando Python: {e}")
                messagebox.showerror("Error", f"Error instalando Python: {e}")
            finally:
                self.progress.stop()
                self.status_var.set("Listo")
        
        # Confirmar instalación
        if messagebox.askyesno("Confirmar", "¿Desea descargar e instalar Python? Esto puede tomar varios minutos."):
            threading.Thread(target=install_thread, daemon=True).start()
    
    def verificar_dependencias(self):
        """Verificar si las dependencias están instaladas"""
        try:
            if not os.path.exists("../config/requirements.txt"):
                self.deps_status.set("✗ Archivo ../config/requirements.txt no encontrado")
                return False
            
            self.log_message("Verificando dependencias...")
            
            # Leer ../config/requirements.txt
            with open("../config/requirements.txt", "r", encoding="utf-8") as f:
                requirements = f.read().strip().split("\n")
            
            missing_packages = []
            installed_packages = []
            
            for req in requirements:
                if req.strip() and not req.strip().startswith("#"):
                    package_name = req.split("==")[0].split(">=")[0].split("<=")[0].strip()
                    try:
                        result = subprocess.run([sys.executable, "-m", "pip", "show", package_name], 
                                              capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            installed_packages.append(package_name)
                        else:
                            missing_packages.append(package_name)
                    except Exception:
                        missing_packages.append(package_name)
            
            if missing_packages:
                self.deps_status.set(f"✗ Faltan {len(missing_packages)} dependencias")
                self.log_message(f"Dependencias faltantes: {', '.join(missing_packages)}")
            else:
                self.deps_status.set(f"✓ Todas las dependencias están instaladas ({len(installed_packages)})")
                self.log_message("Todas las dependencias están instaladas")
            
            return len(missing_packages) == 0
            
        except Exception as e:
            self.deps_status.set("✗ Error verificando dependencias")
            self.log_message(f"Error verificando dependencias: {e}")
            return False
    
    def instalar_dependencias(self):
        """Instalar dependencias desde requirements.txt"""
        def install_deps_thread():
            try:
                self.progress.start()
                self.status_var.set("Instalando dependencias...")
                self.log_message("Iniciando instalación de dependencias...")
                
                # Actualizar pip primero
                self.log_message("Actualizando pip...")
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                             timeout=120)
                
                # Instalar dependencias
                self.log_message("Instalando dependencias desde ../config/requirements.txt...")
                result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "../config/requirements.txt"], 
                                      capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    self.log_message("Dependencias instaladas exitosamente")
                    self.status_var.set("Dependencias instaladas")
                    
                    # Verificar instalación
                    self.root.after(1000, self.verificar_dependencias)
                else:
                    raise Exception(f"Error en pip install: {result.stderr}")
                
            except Exception as e:
                self.log_message(f"Error instalando dependencias: {e}")
                messagebox.showerror("Error", f"Error instalando dependencias: {e}")
            finally:
                self.progress.stop()
                self.status_var.set("Listo")
        
        if not os.path.exists("requirements.txt"):
            messagebox.showerror("Error", "Archivo requirements.txt no encontrado")
            return
        
        threading.Thread(target=install_deps_thread, daemon=True).start()
    
    def guardar_config_general(self):
        """Guardar configuración general"""
        try:
            self.config["TOKEN_API"] = self.token_entry.get().strip() or None
            self.config["INTERVALO_MINUTOS"] = self.intervalo_var.get()
            auto_start_nuevo = self.auto_start_var.get()
            auto_start_anterior = self.config.get("AUTO_START", False)
            
            self.config["AUTO_START"] = auto_start_nuevo
            self.config["MINIMIZE_TO_TRAY"] = self.minimize_tray_var.get()
            
            # Configurar startup solo si cambió la opción
            if auto_start_nuevo != auto_start_anterior:
                if self.configurar_startup_windows(auto_start_nuevo):
                    if auto_start_nuevo:
                        self.log_message("✅ Programa agregado al inicio automático del sistema")
                        # Ejecutar diagnóstico para verificar
                        self.diagnosticar_startup()
                    else:
                        self.log_message("✅ Programa removido del inicio automático del sistema")
                else:
                    # Si falla la configuración del startup, revertir la opción
                    self.auto_start_var.set(auto_start_anterior)
                    self.config["AUTO_START"] = auto_start_anterior
                    if auto_start_nuevo:
                        messagebox.showerror("Error", "No se pudo agregar el programa al inicio automático")
                        self.log_message("❌ Error agregando al inicio automático")
                    else:
                        messagebox.showerror("Error", "No se pudo quitar el programa del inicio automático")
                        self.log_message("❌ Error quitando del inicio automático")
                    # Ejecutar diagnóstico para ver qué falló
                    self.diagnosticar_startup()
                    return
            
            if self.guardar_configuracion():
                messagebox.showinfo("Éxito", "Configuración general guardada correctamente")
                self.log_message("Configuración general guardada")
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración: {e}")
    
    def restablecer_config_general(self):
        """Restablecer configuración general a valores por defecto"""
        if messagebox.askyesno("Confirmar", "¿Desea restablecer la configuración general a los valores por defecto?"):
            self.token_entry.delete(0, tk.END)
            self.intervalo_var.set(5)
            self.auto_start_var.set(False)
            self.minimize_tray_var.set(True)
    
    def guardar_config_biometrico(self):
        """Guardar configuración del biométrico"""
        try:
            self.config["IP_BIOMETRICO"] = self.ip_bio_entry.get().strip()
            self.config["PUERTO_BIOMETRICO"] = self.puerto_bio_var.get()
            self.config["NOMBRE_ESTACION"] = self.nombre_estacion_entry.get().strip()
            
            if self.guardar_configuracion():
                messagebox.showinfo("Éxito", "Configuración biométrica guardada correctamente")
                self.log_message("Configuración biométrica guardada")
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración biométrica: {e}")
    
    def restablecer_config_biometrico(self):
        """Restablecer configuración biométrica a valores por defecto"""
        if messagebox.askyesno("Confirmar", "¿Desea restablecer la configuración biométrica a los valores por defecto?"):
            self.ip_bio_entry.delete(0, tk.END)
            self.ip_bio_entry.insert(0, "192.168.1.88")
            self.puerto_bio_var.set(4370)
            self.nombre_estacion_entry.delete(0, tk.END)
            self.nombre_estacion_entry.insert(0, "Centenario")
    
    def probar_conexion_biometrico(self):
        """Probar conexión con el dispositivo biométrico"""
        def test_connection():
            try:
                self.conexion_status.set("Probando...")
                ip = self.ip_bio_entry.get().strip()
                puerto = self.puerto_bio_var.get()
                
                if not ip:
                    raise Exception("IP no especificada")
                
                self.log_message(f"Probando conexión con {ip}:{puerto}...", self.sync_log_text)
                
                # Primero probar conectividad básica
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((ip, puerto))
                sock.close()
                
                if result != 0:
                    raise Exception(f"No se puede conectar a {ip}:{puerto}")
                
                # Intentar conexión con pyzk si está disponible
                try:
                    from zk import ZK
                    
                    zk = ZK(ip, port=puerto, timeout=5, password=0, force_udp=False, ommit_ping=False)
                    conn = None
                    
                    try:
                        conn = zk.connect()
                        
                        # Obtener información del dispositivo
                        device_name = conn.get_device_name() or "Desconocido"
                        serial_number = conn.get_serialnumber() or "N/A"
                        firmware_version = conn.get_firmware_version() or "N/A"
                        
                        # Contar usuarios y registros
                        users = conn.get_users()
                        attendance = conn.get_attendance()
                        
                        self.conexion_status.set("✓ Conexión exitosa (ZK)")
                        self.log_message(f"Conexión ZK exitosa con {ip}:{puerto}", self.sync_log_text)
                        self.log_message(f"Dispositivo: {device_name}", self.sync_log_text)
                        self.log_message(f"Serie: {serial_number}", self.sync_log_text)
                        self.log_message(f"Firmware: {firmware_version}", self.sync_log_text)
                        self.log_message(f"Usuarios: {len(users)}, Registros: {len(attendance)}", self.sync_log_text)
                        
                    finally:
                        if conn:
                            conn.disconnect()
                            
                except ImportError:
                    # Si pyzk no está disponible, solo confirmamos conectividad TCP
                    self.conexion_status.set("✓ Conexión TCP exitosa")
                    self.log_message(f"Conexión TCP exitosa con {ip}:{puerto} (pyzk no disponible)", self.sync_log_text)
                    
                except Exception as zk_error:
                    # Error específico de ZK
                    self.conexion_status.set("⚠ TCP OK, ZK Error")
                    self.log_message(f"TCP OK pero error ZK: {zk_error}", self.sync_log_text)
                    
            except Exception as e:
                self.conexion_status.set(f"✗ Error: {str(e)[:30]}...")
                self.log_message(f"Error probando conexión: {e}", self.sync_log_text)
        
        threading.Thread(target=test_connection, daemon=True).start()
    
    def iniciar_sincronizacion(self):
        """Iniciar sincronización automática"""
        if self.sync_running:
            return
        
        def sync_worker():
            self.sync_running = True
            self.sync_status.set("Ejecutándose")
            self.start_sync_btn.config(state=tk.DISABLED)
            self.stop_sync_btn.config(state=tk.NORMAL)
            
            try:
                while self.sync_running:
                    self.log_message("Ejecutando sincronización automática...", self.sync_log_text)
                    
                    # Ejecutar sincronización real
                    success = self.ejecutar_sincronizacion()
                    
                    if success:
                        self.log_message("Sincronización automática completada exitosamente", self.sync_log_text)
                    else:
                        self.log_message("Sincronización automática falló", self.sync_log_text)
                    
                    # Esperar intervalo configurado
                    intervalo = self.config.get("INTERVALO_MINUTOS", 5) * 60
                    self.log_message(f"Esperando {self.config.get('INTERVALO_MINUTOS', 5)} minutos para la próxima sincronización...", self.sync_log_text)
                    
                    for i in range(intervalo):
                        if not self.sync_running:
                            break
                        time.sleep(1)
                        
            except Exception as e:
                self.log_message(f"Error en sincronización automática: {e}", self.sync_log_text)
            finally:
                self.sync_running = False
                self.sync_status.set("Detenido")
                self.start_sync_btn.config(state=tk.NORMAL)
                self.stop_sync_btn.config(state=tk.DISABLED)
        
        self.sync_thread = threading.Thread(target=sync_worker, daemon=True)
        self.sync_thread.start()
    
    def detener_sincronizacion(self):
        """Detener sincronización automática"""
        self.sync_running = False
        self.log_message("Deteniendo sincronización...", self.sync_log_text)
    
    def sincronizacion_manual(self):
        """Ejecutar sincronización manual"""
        def manual_sync():
            try:
                self.log_message("Iniciando sincronización manual...", self.sync_log_text)
                
                # Ejecutar sincronización real
                success = self.ejecutar_sincronizacion()
                
                if success:
                    self.log_message("Sincronización manual completada exitosamente", self.sync_log_text)
                    messagebox.showinfo("Éxito", "Sincronización manual completada")
                else:
                    self.log_message("Sincronización manual falló", self.sync_log_text)
                    messagebox.showwarning("Advertencia", "Sincronización completada con errores")
                
            except Exception as e:
                self.log_message(f"Error en sincronización manual: {e}", self.sync_log_text)
                messagebox.showerror("Error", f"Error en sincronización manual: {e}")
        
        threading.Thread(target=manual_sync, daemon=True).start()
    
    def ejecutar_sincronizacion(self):
        """Ejecutar el proceso de sincronización real"""
        try:
            # Validar configuración
            if not self.config.get("IP_BIOMETRICO"):
                raise Exception("IP del biométrico no configurada")
            
            if not self.config.get("SERVER_URL"):
                raise Exception("URL del servidor no configurada")
            
            # Importar módulos necesarios
            try:
                from zk import ZK
            except ImportError:
                self.log_message("Módulo 'zk' no disponible, usando simulación", self.sync_log_text)
                return self.simular_sincronizacion()
            
            # Conectar al dispositivo biométrico
            ip = self.config["IP_BIOMETRICO"]
            puerto = self.config["PUERTO_BIOMETRICO"]
            
            self.log_message(f"Conectando a biométrico {ip}:{puerto}...", self.sync_log_text)
            
            zk = ZK(ip, port=puerto, timeout=5, password=0, force_udp=False, ommit_ping=False)
            conn = None
            
            try:
                conn = zk.connect()
                self.log_message("Conexión establecida con el biométrico", self.sync_log_text)
                
                # Obtener registros de asistencia
                attendance = conn.get_attendance()
                self.log_message(f"Se obtuvieron {len(attendance)} registros", self.sync_log_text)
                
                if len(attendance) == 0:
                    self.log_message("No hay registros nuevos para sincronizar", self.sync_log_text)
                    return True
                
                # Obtener usuarios para mapear nombres
                try:
                    users = conn.get_users()
                    user_map = {u.user_id: u.name for u in users}
                    self.log_message(f"Obtenidos {len(users)} usuarios", self.sync_log_text)
                except Exception as e:
                    self.log_message(f"Error obteniendo usuarios: {e}", self.sync_log_text)
                    user_map = {}
                
                # Preparar datos para enviar (formato compatible con el servidor)
                datos_envio = []
                for record in attendance:
                    registro_data = {
                        'user_id': record.user_id,
                        'nombre': user_map.get(record.user_id, f"Usuario_{record.user_id}"),
                        'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                        'status': record.status,
                        'estacion': self.config.get("NOMBRE_ESTACION", "Default"),
                        'punch': getattr(record, 'punch', 0)  # Tipo de marcaje si está disponible
                    }
                    datos_envio.append(registro_data)
                
                # Enviar datos al servidor
                return self.enviar_datos_servidor(datos_envio)
                
            finally:
                if conn:
                    conn.disconnect()
                    self.log_message("Conexión cerrada", self.sync_log_text)
                    
        except Exception as e:
            self.log_message(f"Error en sincronización: {e}", self.sync_log_text)
            return False
    
    def simular_sincronizacion(self):
        """Simular proceso de sincronización cuando no hay dispositivo disponible"""
        import random
        
        self.log_message("Modo simulación activado", self.sync_log_text)
        
        # Simular datos de prueba (formato compatible con el servidor)
        datos_simulados = []
        for i in range(random.randint(1, 5)):
            user_id = random.randint(1, 100)
            datos_simulados.append({
                'user_id': user_id,
                'nombre': f"Usuario_{user_id:03d}",
                'timestamp': datetime.now().isoformat(),
                'status': 1,
                'estacion': self.config.get("NOMBRE_ESTACION", "Simulacion"),
                'punch': random.choice([0, 1, 4, 5])  # Tipo de marcaje
            })
        
        self.log_message(f"Datos simulados generados: {len(datos_simulados)} registros", self.sync_log_text)
        
        # Simular envío al servidor
        return self.enviar_datos_servidor(datos_simulados)
    
    def enviar_datos_servidor(self, datos):
        """Enviar datos al servidor"""
        try:
            url = self.config["SERVER_URL"]
            headers = {"Content-Type": "application/json"}
            
            # Agregar token si está configurado (formato compatible con el servidor)
            if self.config.get("TOKEN_API"):
                headers["Authorization"] = f"Token {self.config['TOKEN_API']}"
            
            self.log_message(f"Enviando {len(datos)} registros al servidor...", self.sync_log_text)
            
            # Enviar directamente la lista de datos como espera el servidor
            response = requests.post(url, json=datos, headers=headers, timeout=30)
            
            self.log_message(f"Código de respuesta: {response.status_code}", self.sync_log_text)
            
            if response.status_code == 200:
                self.log_message("Datos enviados exitosamente al servidor", self.sync_log_text)
                return True
            else:
                self.log_message(f"Error del servidor: {response.status_code} - {response.text}", self.sync_log_text)
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_message(f"Error de conexión con el servidor: {e}", self.sync_log_text)
            return False
        except Exception as e:
            self.log_message(f"Error enviando datos: {e}", self.sync_log_text)
            return False
    
    def run(self):
        """Ejecutar la aplicación"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.cerrar_aplicacion()
        except Exception as e:
            print(f"Error en la aplicación: {e}")
            self.cerrar_aplicacion()
        finally:
            self.liberar_lock()

if __name__ == "__main__":
    try:
        app = InstaladorCompleto()
        app.run()
    except SystemExit:
        # Salida controlada cuando ya hay una instancia ejecutándose
        pass
    except Exception as e:
        print(f"Error iniciando aplicación: {e}")
        messagebox.showerror("Error Fatal", f"Error iniciando la aplicación: {e}")
        sys.exit(1)
