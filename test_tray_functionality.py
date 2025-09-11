#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de la bandeja del sistema
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
import logging
import sys
import os

# Agregar el directorio actual al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pystray
    from PIL import Image, ImageDraw
    print("✅ pystray y PIL importados correctamente")
except ImportError as e:
    print(f"❌ Error importando dependencias: {e}")
    sys.exit(1)

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_icon():
    """Crea un icono de prueba para la bandeja"""
    try:
        width = height = 64
        image = Image.new('RGB', (width, height), (255, 0, 0))  # Rojo para prueba
        draw = ImageDraw.Draw(image)
        
        # Dibujar un círculo blanco
        margin = 8
        draw.ellipse([margin, margin, width-margin, height-margin], fill=(255, 255, 255))
        
        # Dibujar texto "T" de Test
        text = "T"
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2
        draw.text((text_x, text_y), text, fill=(255, 0, 0))
        
        print("✅ Icono de prueba creado correctamente")
        return image
        
    except Exception as e:
        print(f"❌ Error creando icono: {e}")
        # Crear icono simple de respaldo
        image = Image.new('RGB', (32, 32), (255, 0, 0))
        return image

class TrayTestApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Prueba de Bandeja del Sistema")
        self.root.geometry("400x300")
        
        self.tray_icon = None
        self.tray_thread = None
        self.hidden = False
        
        self.setup_ui()
        self.setup_tray()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = tk.Label(main_frame, text="Prueba de Bandeja del Sistema", 
                              font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Estado
        self.status_var = tk.StringVar(value="Ventana visible")
        status_label = tk.Label(main_frame, textvariable=self.status_var, 
                               font=("Arial", 10))
        status_label.pack(pady=(0, 20))
        
        # Botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(button_frame, text="Ocultar a Bandeja", 
                 command=self.hide_window, bg="lightblue").pack(pady=5, fill=tk.X)
        
        tk.Button(button_frame, text="Mostrar Ventana", 
                 command=self.show_window, bg="lightgreen").pack(pady=5, fill=tk.X)
        
        tk.Button(button_frame, text="Probar Notificación", 
                 command=self.test_notification, bg="lightyellow").pack(pady=5, fill=tk.X)
        
        tk.Button(button_frame, text="Salir Completamente", 
                 command=self.quit_app, bg="lightcoral").pack(pady=5, fill=tk.X)
        
        # Información
        info_text = """
Instrucciones:
1. Haz clic en "Ocultar a Bandeja" para ocultar la ventana
2. Busca el icono rojo en la bandeja del sistema
3. Haz clic derecho en el icono para ver el menú
4. Usa "Mostrar" para volver a mostrar la ventana
        """
        info_label = tk.Label(main_frame, text=info_text, justify=tk.LEFT, 
                             font=("Arial", 9), fg="gray")
        info_label.pack(pady=20)
        
        # Configurar el comportamiento de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_tray(self):
        """Configura el icono de la bandeja del sistema"""
        try:
            print("🔧 Configurando icono de bandeja...")
            
            # Crear menú para la bandeja
            menu = pystray.Menu(
                pystray.MenuItem("Mostrar Ventana", self.show_window),
                pystray.MenuItem("Ocultar Ventana", self.hide_window),
                pystray.MenuItem("Prueba de Notificación", self.test_notification),
                pystray.MenuItem("Salir", self.quit_app)
            )
            
            # Crear icono de bandeja
            self.tray_icon = pystray.Icon(
                "tray_test",
                create_test_icon(),
                "Prueba de Bandeja - SyncBio",
                menu
            )
            
            # Ejecutar el icono de bandeja en un hilo separado
            self.tray_thread = threading.Thread(target=self.run_tray_icon, daemon=True)
            self.tray_thread.start()
            
            print("✅ Icono de bandeja configurado y iniciado")
            
        except Exception as e:
            print(f"❌ Error configurando bandeja: {e}")
            messagebox.showerror("Error", f"No se pudo configurar la bandeja del sistema:\n{e}")
            self.tray_icon = None
    
    def run_tray_icon(self):
        """Ejecuta el icono de bandeja en un hilo separado"""
        try:
            if self.tray_icon:
                print("🚀 Ejecutando icono de bandeja...")
                self.tray_icon.run()
        except Exception as e:
            print(f"❌ Error ejecutando icono de bandeja: {e}")
            self.tray_icon = None
    
    def show_window(self, icon=None, item=None):
        """Muestra la ventana principal"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.hidden = False
            self.status_var.set("Ventana visible")
            print("👁️  Ventana mostrada")
        except Exception as e:
            print(f"❌ Error mostrando ventana: {e}")
    
    def hide_window(self, icon=None, item=None):
        """Oculta la ventana principal"""
        try:
            self.root.withdraw()
            self.hidden = True
            self.status_var.set("Ventana oculta en bandeja")
            print("👻 Ventana ocultada a bandeja")
        except Exception as e:
            print(f"❌ Error ocultando ventana: {e}")
    
    def test_notification(self, icon=None, item=None):
        """Prueba una notificación desde la bandeja"""
        try:
            if self.tray_icon:
                self.tray_icon.notify("¡Prueba exitosa!", "La bandeja del sistema funciona correctamente")
                print("📢 Notificación enviada")
            else:
                messagebox.showinfo("Info", "El icono de bandeja no está disponible")
        except Exception as e:
            print(f"❌ Error en notificación: {e}")
            messagebox.showerror("Error", f"Error en notificación: {e}")
    
    def on_closing(self):
        """Maneja el cierre de la ventana principal"""
        if self.tray_icon:
            print("🔄 Ventana cerrada, minimizando a bandeja...")
            self.hide_window()
        else:
            print("❌ No hay bandeja disponible, cerrando completamente...")
            self.quit_app()
    
    def quit_app(self, icon=None, item=None):
        """Cierra completamente la aplicación"""
        try:
            print("🛑 Cerrando aplicación...")
            
            # Cerrar icono de bandeja
            if self.tray_icon:
                print("🗑️  Cerrando icono de bandeja...")
                self.tray_icon.stop()
                self.tray_icon = None
            
            # Cerrar ventana principal
            self.root.quit()
            self.root.destroy()
            
            print("✅ Aplicación cerrada completamente")
            
        except Exception as e:
            print(f"❌ Error durante el cierre: {e}")
    
    def run(self):
        """Ejecuta la aplicación"""
        print("🚀 Iniciando aplicación de prueba...")
        print("📱 Busca el icono ROJO en la bandeja del sistema")
        print("🖱️  Haz clic derecho en el icono para ver el menú")
        print("-" * 50)
        self.root.mainloop()

def main():
    """Función principal"""
    print("="*60)
    print("🧪 PRUEBA DE FUNCIONALIDAD DE BANDEJA DEL SISTEMA")
    print("="*60)
    
    try:
        app = TrayTestApp()
        app.run()
    except KeyboardInterrupt:
        print("\n⚡ Aplicación interrumpida por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    print("🏁 Prueba finalizada")

if __name__ == "__main__":
    main()
