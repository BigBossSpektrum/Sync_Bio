import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
from pathlib import Path
import json

class InstaladorPythonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador de Python y Dependencias")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variables de configuración
        self.python_path = tk.StringVar()
        self.requirements_path = tk.StringVar()
        self.config_file = "instalador_config.json"
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cargar configuración guardada
        self.cargar_configuracion()
        
        # Crear la interfaz
        self.crear_interfaz()
        
    def crear_interfaz(self):
        # Frame principal con notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de Configuración
        self.crear_pestana_configuracion(notebook)
        
        # Pestaña de Instalación
        self.crear_pestana_instalacion(notebook)
        
        # Pestaña de Verificación
        self.crear_pestana_verificacion(notebook)
        
    def crear_pestana_configuracion(self, notebook):
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuración")
        
        # Título
        titulo = ttk.Label(config_frame, text="Configuración de Rutas", 
                          font=("Arial", 14, "bold"))
        titulo.pack(pady=(10, 20))
        
        # Frame para Python
        python_frame = ttk.LabelFrame(config_frame, text="Ejecutable de Python", 
                                     padding=10)
        python_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(python_frame, text="Ruta del archivo python.exe:").pack(anchor=tk.W)
        
        python_path_frame = ttk.Frame(python_frame)
        python_path_frame.pack(fill=tk.X, pady=5)
        
        self.python_entry = ttk.Entry(python_path_frame, textvariable=self.python_path, 
                                     width=60)
        self.python_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(python_path_frame, text="Examinar", 
                  command=self.examinar_python).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Frame para Requirements
        req_frame = ttk.LabelFrame(config_frame, text="Archivo de Dependencias", 
                                  padding=10)
        req_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(req_frame, text="Ruta del archivo requirements.txt:").pack(anchor=tk.W)
        
        req_path_frame = ttk.Frame(req_frame)
        req_path_frame.pack(fill=tk.X, pady=5)
        
        self.req_entry = ttk.Entry(req_path_frame, textvariable=self.requirements_path, 
                                  width=60)
        self.req_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(req_path_frame, text="Examinar", 
                  command=self.examinar_requirements).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Botones de configuración
        config_buttons_frame = ttk.Frame(config_frame)
        config_buttons_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(config_buttons_frame, text="Detectar Automáticamente", 
                  command=self.detectar_automatico).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(config_buttons_frame, text="Guardar Configuración", 
                  command=self.guardar_configuracion).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(config_buttons_frame, text="Restablecer", 
                  command=self.restablecer_configuracion).pack(side=tk.LEFT)
        
        # Estado de los archivos
        self.estado_frame = ttk.LabelFrame(config_frame, text="Estado de Archivos", 
                                          padding=10)
        self.estado_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.estado_python_label = ttk.Label(self.estado_frame, text="Python: No verificado")
        self.estado_python_label.pack(anchor=tk.W)
        
        self.estado_req_label = ttk.Label(self.estado_frame, text="Requirements: No verificado")
        self.estado_req_label.pack(anchor=tk.W)
        
        ttk.Button(self.estado_frame, text="Verificar Archivos", 
                  command=self.verificar_archivos).pack(pady=10)
        
    def crear_pestana_instalacion(self, notebook):
        install_frame = ttk.Frame(notebook)
        notebook.add(install_frame, text="Instalación")
        
        # Título
        titulo = ttk.Label(install_frame, text="Instalación de Dependencias", 
                          font=("Arial", 14, "bold"))
        titulo.pack(pady=(10, 20))
        
        # Frame de botones de instalación
        install_buttons_frame = ttk.Frame(install_frame)
        install_buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.install_btn = ttk.Button(install_buttons_frame, text="Instalar Dependencias", 
                                     command=self.instalar_dependencias, 
                                     style="Accent.TButton")
        self.install_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.upgrade_pip_btn = ttk.Button(install_buttons_frame, text="Actualizar pip", 
                                         command=self.actualizar_pip)
        self.upgrade_pip_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(install_buttons_frame, text="Detener", 
                                  command=self.detener_proceso, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # Barra de progreso
        self.progress_var = tk.StringVar(value="Listo para instalar")
        progress_frame = ttk.Frame(install_frame)
        progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(progress_frame, text="Estado:").pack(anchor=tk.W)
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Log de instalación
        log_frame = ttk.LabelFrame(install_frame, text="Log de Instalación", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Botones de log
        log_buttons_frame = ttk.Frame(log_frame)
        log_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(log_buttons_frame, text="Limpiar Log", 
                  command=self.limpiar_log).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(log_buttons_frame, text="Guardar Log", 
                  command=self.guardar_log).pack(side=tk.LEFT)
        
    def crear_pestana_verificacion(self, notebook):
        verify_frame = ttk.Frame(notebook)
        notebook.add(verify_frame, text="Verificación")
        
        # Título
        titulo = ttk.Label(verify_frame, text="Verificación del Sistema", 
                          font=("Arial", 14, "bold"))
        titulo.pack(pady=(10, 20))
        
        # Botones de verificación
        verify_buttons_frame = ttk.Frame(verify_frame)
        verify_buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(verify_buttons_frame, text="Verificar Versión Python", 
                  command=self.verificar_python_version).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(verify_buttons_frame, text="Listar Paquetes Instalados", 
                  command=self.listar_paquetes).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(verify_buttons_frame, text="Verificar pip", 
                  command=self.verificar_pip).pack(side=tk.LEFT)
        
        # Segunda fila de botones
        verify_buttons_frame2 = ttk.Frame(verify_frame)
        verify_buttons_frame2.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Button(verify_buttons_frame2, text="Verificar Dependencias", 
                  command=self.verificar_dependencias).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(verify_buttons_frame2, text="Información del Sistema", 
                  command=self.info_sistema).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(verify_buttons_frame2, text="Test de Importación", 
                  command=self.test_importacion).pack(side=tk.LEFT)
        
        # Log de verificación
        verify_log_frame = ttk.LabelFrame(verify_frame, text="Resultados de Verificación", 
                                         padding=10)
        verify_log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.verify_log_text = scrolledtext.ScrolledText(verify_log_frame, height=15, 
                                                        wrap=tk.WORD)
        self.verify_log_text.pack(fill=tk.BOTH, expand=True)
        
        # Botones del log de verificación
        verify_log_buttons_frame = ttk.Frame(verify_log_frame)
        verify_log_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(verify_log_buttons_frame, text="Limpiar", 
                  command=self.limpiar_verify_log).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(verify_log_buttons_frame, text="Guardar Resultados", 
                  command=self.guardar_verify_log).pack(side=tk.LEFT)
        
    def examinar_python(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar python.exe",
            filetypes=[("Ejecutables", "*.exe"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            self.python_path.set(archivo)
            self.verificar_archivos()
            
    def examinar_requirements(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar requirements.txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            self.requirements_path.set(archivo)
            self.verificar_archivos()
            
    def detectar_automatico(self):
        """Detecta automáticamente Python y requirements.txt en el directorio actual"""
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        
        # Buscar python.exe
        python_local = os.path.join(directorio_actual, "python.exe")
        if os.path.exists(python_local):
            self.python_path.set(python_local)
        else:
            # Buscar Python en el sistema
            try:
                result = subprocess.run(["where", "python"], capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    python_sistema = result.stdout.strip().split('\n')[0]
                    self.python_path.set(python_sistema)
            except:
                pass
        
        # Buscar ../config/requirements.txt
        req_local = os.path.join(directorio_actual, "../config/requirements.txt")
        if os.path.exists(req_local):
            self.requirements_path.set(req_local)
            
        self.verificar_archivos()
        self.log_message("Detección automática completada")
        
    def verificar_archivos(self):
        """Verifica que los archivos seleccionados existan y sean válidos"""
        # Verificar Python
        python_ok = False
        if self.python_path.get():
            if os.path.exists(self.python_path.get()):
                python_ok = True
                self.estado_python_label.config(text="Python: ✓ Encontrado", foreground="green")
            else:
                self.estado_python_label.config(text="Python: ✗ No encontrado", foreground="red")
        else:
            self.estado_python_label.config(text="Python: ⚠ No especificado", foreground="orange")
            
        # Verificar Requirements
        req_ok = False
        if self.requirements_path.get():
            if os.path.exists(self.requirements_path.get()):
                req_ok = True
                self.estado_req_label.config(text="Requirements: ✓ Encontrado", foreground="green")
            else:
                self.estado_req_label.config(text="Requirements: ✗ No encontrado", foreground="red")
        else:
            self.estado_req_label.config(text="Requirements: ⚠ No especificado", foreground="orange")
            
        # Habilitar/deshabilitar botón de instalación
        if python_ok and req_ok:
            self.install_btn.config(state=tk.NORMAL)
        else:
            self.install_btn.config(state=tk.DISABLED)
            
    def cargar_configuracion(self):
        """Carga la configuración desde archivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.python_path.set(config.get('python_path', ''))
                    self.requirements_path.set(config.get('requirements_path', ''))
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            
    def guardar_configuracion(self):
        """Guarda la configuración actual en archivo JSON"""
        try:
            config = {
                'python_path': self.python_path.get(),
                'requirements_path': self.requirements_path.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración: {e}")
            
    def restablecer_configuracion(self):
        """Restablece la configuración a valores por defecto"""
        self.python_path.set('')
        self.requirements_path.set('')
        self.verificar_archivos()
        self.log_message("Configuración restablecida")
        
    def log_message(self, mensaje, log_widget=None):
        """Añade un mensaje al log especificado"""
        if log_widget is None:
            log_widget = self.log_text
            
        timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
        log_widget.insert(tk.END, f"[{timestamp}] {mensaje}\n")
        log_widget.see(tk.END)
        self.root.update_idletasks()
        
    def limpiar_log(self):
        """Limpia el log de instalación"""
        self.log_text.delete(1.0, tk.END)
        
    def limpiar_verify_log(self):
        """Limpia el log de verificación"""
        self.verify_log_text.delete(1.0, tk.END)
        
    def guardar_log(self):
        """Guarda el log de instalación en un archivo"""
        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Éxito", "Log guardado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error guardando log: {e}")
                
    def guardar_verify_log(self):
        """Guarda el log de verificación en un archivo"""
        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write(self.verify_log_text.get(1.0, tk.END))
                messagebox.showinfo("Éxito", "Resultados guardados correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error guardando resultados: {e}")
                
    def ejecutar_comando(self, comando, log_widget=None, mostrar_comando=True):
        """Ejecuta un comando y muestra la salida en el log"""
        if log_widget is None:
            log_widget = self.log_text
            
        if mostrar_comando:
            self.log_message(f"Ejecutando: {comando}", log_widget)
            
        try:
            # Usar el python configurado para comandos de Python
            if comando.startswith("python ") and self.python_path.get():
                comando = comando.replace("python ", f'"{self.python_path.get()}" ', 1)
            elif comando.startswith("pip ") and self.python_path.get():
                comando = f'"{self.python_path.get()}" -m pip ' + comando[4:]
                
            result = subprocess.run(comando, shell=True, capture_output=True, 
                                  text=True, encoding='utf-8')
            
            if result.stdout:
                self.log_message(result.stdout, log_widget)
            if result.stderr:
                self.log_message(f"Error: {result.stderr}", log_widget)
                
            return result.returncode == 0
            
        except Exception as e:
            self.log_message(f"Error ejecutando comando: {e}", log_widget)
            return False
            
    def instalar_dependencias(self):
        """Instala las dependencias en un hilo separado"""
        if not self.python_path.get() or not self.requirements_path.get():
            messagebox.showerror("Error", "Debe configurar las rutas de Python y requirements.txt")
            return
            
        def instalar():
            self.install_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.progress_bar.start()
            self.progress_var.set("Instalando dependencias...")
            
            self.log_message("=== INICIANDO INSTALACIÓN DE DEPENDENCIAS ===")
            self.log_message(f"Python: {self.python_path.get()}")
            self.log_message(f"Requirements: {self.requirements_path.get()}")
            
            # Verificar Python
            if self.ejecutar_comando(f'"{self.python_path.get()}" --version'):
                self.log_message("✓ Python verificado correctamente")
            else:
                self.log_message("✗ Error verificando Python")
                self.finalizar_instalacion()
                return
                
            # Instalar dependencias
            cmd = f'"{self.python_path.get()}" -m pip install -r "{self.requirements_path.get()}"'
            if self.ejecutar_comando(cmd):
                self.log_message("✓ Dependencias instaladas correctamente")
                self.progress_var.set("Instalación completada exitosamente")
            else:
                self.log_message("✗ Error instalando dependencias")
                self.progress_var.set("Error en la instalación")
                
            self.log_message("=== INSTALACIÓN FINALIZADA ===")
            self.finalizar_instalacion()
            
        threading.Thread(target=instalar, daemon=True).start()
        
    def actualizar_pip(self):
        """Actualiza pip a la última versión"""
        if not self.python_path.get():
            messagebox.showerror("Error", "Debe configurar la ruta de Python")
            return
            
        def actualizar():
            self.upgrade_pip_btn.config(state=tk.DISABLED)
            self.progress_bar.start()
            self.progress_var.set("Actualizando pip...")
            
            self.log_message("=== ACTUALIZANDO PIP ===")
            cmd = f'"{self.python_path.get()}" -m pip install --upgrade pip'
            if self.ejecutar_comando(cmd):
                self.log_message("✓ pip actualizado correctamente")
            else:
                self.log_message("✗ Error actualizando pip")
                
            self.progress_bar.stop()
            self.upgrade_pip_btn.config(state=tk.NORMAL)
            self.progress_var.set("Actualización de pip finalizada")
            
        threading.Thread(target=actualizar, daemon=True).start()
        
    def finalizar_instalacion(self):
        """Finaliza el proceso de instalación"""
        self.progress_bar.stop()
        self.install_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def detener_proceso(self):
        """Detiene el proceso actual (implementación básica)"""
        self.finalizar_instalacion()
        self.progress_var.set("Proceso detenido")
        self.log_message("Proceso detenido por el usuario")
        
    def verificar_python_version(self):
        """Verifica la versión de Python"""
        if self.python_path.get():
            comando = f'"{self.python_path.get()}" --version'
        else:
            comando = "python --version"
        self.ejecutar_comando(comando, self.verify_log_text)
        
    def verificar_pip(self):
        """Verifica la versión de pip"""
        if self.python_path.get():
            comando = f'"{self.python_path.get()}" -m pip --version'
        else:
            comando = "pip --version"
        self.ejecutar_comando(comando, self.verify_log_text)
        
    def listar_paquetes(self):
        """Lista todos los paquetes instalados"""
        if self.python_path.get():
            comando = f'"{self.python_path.get()}" -m pip list'
        else:
            comando = "pip list"
        self.ejecutar_comando(comando, self.verify_log_text)
        
    def verificar_dependencias(self):
        """Verifica si todas las dependencias están instaladas"""
        if not self.requirements_path.get():
            messagebox.showerror("Error", "Debe configurar la ruta de requirements.txt")
            return
            
        self.log_message("=== VERIFICANDO DEPENDENCIAS ===", self.verify_log_text)
        
        try:
            with open(self.requirements_path.get(), 'r', encoding='utf-8') as f:
                requirements = f.read().strip().split('\n')
                
            for req in requirements:
                if req.strip() and not req.strip().startswith('#'):
                    package = req.split('==')[0].split('>=')[0].split('<=')[0].strip()
                    if self.python_path.get():
                        comando = f'"{self.python_path.get()}" -c "import {package}; print(f\\"✓ {package} está instalado\\")"'
                    else:
                        comando = f'python -c "import {package}; print(f\\"✓ {package} está instalado\\")"'
                    
                    if not self.ejecutar_comando(comando, self.verify_log_text, False):
                        self.log_message(f"✗ {package} NO está instalado", self.verify_log_text)
                        
        except Exception as e:
            self.log_message(f"Error verificando dependencias: {e}", self.verify_log_text)
            
    def info_sistema(self):
        """Muestra información del sistema"""
        self.log_message("=== INFORMACIÓN DEL SISTEMA ===", self.verify_log_text)
        
        comandos = [
            "python -c \"import sys; print(f'Python: {sys.version}')\"",
            "python -c \"import platform; print(f'Sistema: {platform.system()} {platform.release()}')\"",
            "python -c \"import sys; print(f'Arquitectura: {sys.maxsize > 2**32 and \\\"64-bit\\\" or \\\"32-bit\\\"}')\"",
            "python -c \"import sys; print(f'Executable: {sys.executable}')\"",
        ]
        
        for cmd in comandos:
            self.ejecutar_comando(cmd, self.verify_log_text)
            
    def test_importacion(self):
        """Hace un test de importación de los módulos principales"""
        self.log_message("=== TEST DE IMPORTACIÓN ===", self.verify_log_text)
        
        modulos = ['requests', 'pyzk', 'PIL', 'pystray', 'dotenv', 'pyinstaller']
        
        for modulo in modulos:
            if self.python_path.get():
                comando = f'"{self.python_path.get()}" -c "import {modulo}; print(f\\"✓ {modulo} importado correctamente\\")"'
            else:
                comando = f'python -c "import {modulo}; print(f\\"✓ {modulo} importado correctamente\\")"'
            
            if not self.ejecutar_comando(comando, self.verify_log_text, False):
                self.log_message(f"✗ Error importando {modulo}", self.verify_log_text)

def main():
    root = tk.Tk()
    app = InstaladorPythonGUI(root)
    
    # Centrar ventana
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Detectar automáticamente al inicio
    root.after(1000, app.detectar_automatico)
    
    root.mainloop()

if __name__ == "__main__":
    main()
