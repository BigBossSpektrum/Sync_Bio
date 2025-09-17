#!/usr/bin/env python3
"""
Script para compilar el instalador biométrico como ejecutable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def ejecutar_comando(comando, descripcion):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n{descripcion}...")
    print(f"Ejecutando: {comando}")
    
    try:
        result = subprocess.run(comando, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✓ {descripcion} completado exitosamente")
        if result.stdout:
            print(f"Salida: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error en {descripcion}")
        print(f"Código de error: {e.returncode}")
        if e.stdout:
            print(f"Salida: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    print("=" * 50)
    print("  COMPILADOR INSTALADOR BIOMÉTRICO")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("src/instalador_completo.py"):
        print("✗ Error: src/instalador_completo.py no encontrado")
        print("Asegúrate de ejecutar este script desde el directorio del proyecto")
        return False
    
    # Verificar Python
    print(f"Python: {sys.version}")
    
    # Instalar PyInstaller si no está disponible
    print("\n1. Verificando PyInstaller...")
    try:
        import PyInstaller
        print(f"✓ PyInstaller ya está instalado: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller no está instalado. Instalando...")
        if not ejecutar_comando("pip install pyinstaller", "Instalación de PyInstaller"):
            return False
    
    # Limpiar builds anteriores
    print("\n2. Limpiando builds anteriores...")
    dirs_to_clean = ["dist", "build"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Eliminado directorio: {dir_name}")
    
    # Compilar usando PyInstaller
    print("\n3. Compilando aplicación...")
    comando_pyinstaller = "pyinstaller instalador_completo.spec"
    
    if not ejecutar_comando(comando_pyinstaller, "Compilación con PyInstaller"):
        return False
    
    # Verificar resultado
    exe_path = Path("dist/InstaladorSincronizadorBiometrico.exe")
    if exe_path.exists():
        print("\n" + "=" * 50)
        print("  ✓ COMPILACIÓN EXITOSA!")
        print("=" * 50)
        print(f"Archivo ejecutable: {exe_path.absolute()}")
        print(f"Tamaño: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        
        # Mostrar archivos en dist
        print("\nArchivos en dist/:")
        for file in Path("dist").iterdir():
            if file.is_file():
                size_mb = file.stat().st_size / (1024*1024)
                print(f"  - {file.name} ({size_mb:.1f} MB)")
        
        return True
    else:
        print("\n" + "=" * 50)
        print("  ✗ ERROR EN LA COMPILACIÓN")
        print("=" * 50)
        print("El archivo ejecutable no fue creado.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 ¡Listo para distribuir!")
        else:
            print("\n❌ Compilación falló")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nCompilación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
