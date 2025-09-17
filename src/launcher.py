import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

def main():
    """Launcher simple que verifica dependencias antes de ejecutar la aplicación principal"""
    
    # Verificar si tkinter está disponible
    try:
        import tkinter.ttk
    except ImportError:
        print("Error: tkinter no está disponible. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tk"])
    
    # Verificar si la aplicación principal existe
    if not os.path.exists("instalador_gui.py"):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", 
                           "No se encontró instalador_gui.py\n"
                           "Asegúrate de que todos los archivos estén en el mismo directorio.")
        return
    
    # Ejecutar la aplicación principal
    try:
        import instalador_gui
        instalador_gui.main()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Error ejecutando la aplicación:\n{e}")

if __name__ == "__main__":
    main()
