#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compilador Integrado para Sincronizador Biométrico
==================================================

Este script compila el proyecto completo en ejecutables (.exe) incluyendo:
- Sincronizador Biométrico Principal
- Gestor de Startup  
- Instalador Completo

Uso:
    python compilar_sincronizador.py [opciones]

Opciones:
    --main-only      Compilar solo el sincronizador principal
    --startup-only   Compilar solo el gestor de startup
    --installer-only Compilar solo el instalador
    --debug         Compilar con información de depuración
    --onedir        Crear directorio con archivos (en lugar de un solo exe)
    --console       Mostrar consola en el ejecutable principal
"""

import os
import sys
import subprocess
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime

class CompiladorSincronizador:
    def __init__(self):
        self.directorio_proyecto = Path.cwd()
        self.directorio_dist = self.directorio_proyecto / "dist"
        self.directorio_build = self.directorio_proyecto / "build"
        self.icono = self.directorio_proyecto / "icono.ico"
        
        # Detectar rutas del entorno virtual
        self.env_dir = self.directorio_proyecto / "env"
        if self.env_dir.exists():
            self.python_exe = str(self.env_dir / "Scripts" / "python.exe")
            self.pyinstaller_exe = str(self.env_dir / "Scripts" / "pyinstaller.exe")
        else:
            self.python_exe = sys.executable
            self.pyinstaller_exe = "pyinstaller"
        
    def log(self, mensaje, tipo="INFO"):
        """Mostrar mensaje con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {tipo}: {mensaje}")
    
    def ejecutar_comando(self, comando, descripcion):
        """Ejecutar comando y mostrar resultado"""
        self.log(f"Ejecutando: {descripcion}")
        self.log(f"Comando: {comando}", "DEBUG")
        
        try:
            result = subprocess.run(comando, shell=True, check=True, 
                                  capture_output=True, text=True, cwd=self.directorio_proyecto)
            self.log(f"✅ {descripcion} completado exitosamente")
            if result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:  # Mostrar solo las últimas 10 líneas
                    self.log(f"   {line}", "DEBUG")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Error en {descripcion}", "ERROR")
            self.log(f"Código de error: {e.returncode}", "ERROR")
            if e.stdout:
                self.log(f"Salida: {e.stdout}", "ERROR")
            if e.stderr:
                self.log(f"Error: {e.stderr}", "ERROR")
            return False
    
    def verificar_dependencias(self):
        """Verificar que todas las dependencias estén instaladas"""
        self.log("Verificando dependencias...")
        
        # Verificar PyInstaller
        try:
            cmd = f'"{self.python_exe}" -c "import PyInstaller; print(PyInstaller.__version__)"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log(f"PyInstaller encontrado: {version}")
            else:
                raise ImportError("PyInstaller no encontrado")
        except:
            self.log("PyInstaller no encontrado, instalando...")
            cmd = f'"{self.python_exe}" -m pip install pyinstaller'
            if not self.ejecutar_comando(cmd, "Instalación de PyInstaller"):
                return False
        
        # Verificar archivos necesarios
        archivos_requeridos = [
            "sincronizador_biometrico_mejorado.py",
            "startup_manager.py",
            "icono.ico",
            "requirements.txt"
        ]
        
        for archivo in archivos_requeridos:
            if not (self.directorio_proyecto / archivo).exists():
                self.log(f"❌ Archivo requerido no encontrado: {archivo}", "ERROR")
                return False
            else:
                self.log(f"✅ Encontrado: {archivo}")
        
        return True
    
    def limpiar_directorios(self):
        """Limpiar directorios de compilación anteriores"""
        self.log("Limpiando directorios de compilación anteriores...")
        
        for directorio in [self.directorio_dist, self.directorio_build]:
            if directorio.exists():
                shutil.rmtree(directorio)
                self.log(f"Eliminado: {directorio}")
        
        # Eliminar archivos .spec antiguos
        specs_antiguos = list(self.directorio_proyecto.glob("*.spec"))
        for spec in specs_antiguos:
            if spec.name not in ["instalador_completo.spec"]:  # Preservar el spec del instalador
                spec.unlink()
                self.log(f"Eliminado: {spec}")
    
    def compilar_sincronizador(self, onefile=True, windowed=True, debug=False):
        """Compilar el sincronizador principal"""
        self.log("=" * 50)
        self.log("COMPILANDO SINCRONIZADOR BIOMÉTRICO PRINCIPAL")
        self.log("=" * 50)
        
        cmd = f'"{self.pyinstaller_exe}" --name=SincronizadorBiometrico --clean'
        
        if onefile:
            cmd += ' --onefile'
        
        if windowed:
            cmd += ' --windowed'
        
        if debug:
            cmd += ' --debug=all'
        
        if self.icono.exists():
            cmd += f' --icon="{self.icono}"'
        
        # Agregar archivos de datos
        cmd += ' --add-data="icono.ico;."'
        cmd += ' --add-data="requirements.txt;."'
        
        configs = ['biometrico_config.json', 'instalador_config.json']
        for config in configs:
            if (self.directorio_proyecto / config).exists():
                cmd += f' --add-data="{config};."'
        
        # Importaciones ocultas críticas
        hidden_imports = [
            'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 
            'tkinter.scrolledtext', 'requests', 'zk', 'dotenv', 'threading', 
            'logging', 'subprocess', 'winreg', 'tempfile', 'json', 'datetime',
            'pathlib', 'collections', 'queue', 'signal', 'traceback'
        ]
        
        for imp in hidden_imports:
            cmd += f' --hidden-import={imp}'
        
        # Excluir módulos innecesarios para reducir tamaño
        exclude_modules = ['matplotlib', 'numpy', 'scipy', 'pandas', 'PIL']
        for mod in exclude_modules:
            cmd += f' --exclude-module={mod}'
        
        cmd += ' sincronizador_biometrico_mejorado.py'
        
        success = self.ejecutar_comando(cmd, "Compilación del sincronizador principal")
        
        if success:
            exe_path = self.directorio_dist / "SincronizadorBiometrico.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                self.log(f"✅ Ejecutable creado: {exe_path}")
                self.log(f"📦 Tamaño: {size_mb:.1f} MB")
            else:
                self.log("❌ No se encontró el ejecutable generado", "ERROR")
                success = False
        
        return success
    
    def compilar_startup_manager(self, onefile=True, debug=False):
        """Compilar el gestor de startup"""
        self.log("=" * 50)
        self.log("COMPILANDO GESTOR DE STARTUP")
        self.log("=" * 50)
        
        cmd = f'"{self.pyinstaller_exe}" --name=StartupManager --clean --console'
        
        if onefile:
            cmd += ' --onefile'
        
        if debug:
            cmd += ' --debug=all'
        
        if self.icono.exists():
            cmd += f' --icon="{self.icono}"'
        
        # Importaciones mínimas para el gestor
        hidden_imports = ['argparse', 'sys', 'os', 'logging', 'winreg', 'subprocess']
        for imp in hidden_imports:
            cmd += f' --hidden-import={imp}'
        
        # Excluir todo lo que no necesita
        exclude_modules = ['tkinter', 'requests', 'zk', 'matplotlib', 'numpy', 'scipy', 'pandas']
        for mod in exclude_modules:
            cmd += f' --exclude-module={mod}'
        
        cmd += ' startup_manager.py'
        
        success = self.ejecutar_comando(cmd, "Compilación del gestor de startup")
        
        if success:
            exe_path = self.directorio_dist / "StartupManager.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                self.log(f"✅ Ejecutable creado: {exe_path}")
                self.log(f"📦 Tamaño: {size_mb:.1f} MB")
            else:
                self.log("❌ No se encontró el ejecutable generado", "ERROR")
                success = False
        
        return success
    
    def compilar_instalador(self):
        """Compilar el instalador usando el spec existente"""
        self.log("=" * 50)
        self.log("COMPILANDO INSTALADOR COMPLETO")
        self.log("=" * 50)
        
        if not (self.directorio_proyecto / "instalador_completo.py").exists():
            self.log("❌ instalador_completo.py no encontrado", "ERROR")
            return False
        
        if not (self.directorio_proyecto / "instalador_completo.spec").exists():
            self.log("❌ instalador_completo.spec no encontrado", "ERROR")
            return False
        
        cmd = f'"{self.pyinstaller_exe}" instalador_completo.spec --clean'
        success = self.ejecutar_comando(cmd, "Compilación del instalador completo")
        
        if success:
            exe_path = self.directorio_dist / "InstaladorSincronizadorBiometrico.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                self.log(f"✅ Instalador creado: {exe_path}")
                self.log(f"📦 Tamaño: {size_mb:.1f} MB")
            else:
                self.log("❌ No se encontró el instalador generado", "ERROR")
                success = False
        
        return success
    
    def crear_informacion_compilacion(self):
        """Crear archivo con información de la compilación"""
        if not self.directorio_dist.exists():
            return
        
        info = {
            "compilacion": {
                "fecha": datetime.now().isoformat(),
                "sistema": os.name,
                "python_version": sys.version.split()[0],
                "directorio": str(self.directorio_proyecto),
            },
            "ejecutables": [],
            "instrucciones": {
                "SincronizadorBiometrico.exe": "Aplicación principal con interfaz gráfica",
                "StartupManager.exe": "Herramienta de línea de comandos para gestionar inicio automático",
                "InstaladorSincronizadorBiometrico.exe": "Instalador completo para distribución"
            },
            "comandos_utiles": {
                "habilitar_startup": "StartupManager.exe --enable",
                "deshabilitar_startup": "StartupManager.exe --disable",
                "ver_estado_startup": "StartupManager.exe --status",
                "probar_startup": "StartupManager.exe --test"
            }
        }
        
        # Agregar información de ejecutables existentes
        ejecutables_esperados = [
            "SincronizadorBiometrico.exe", 
            "StartupManager.exe", 
            "InstaladorSincronizadorBiometrico.exe"
        ]
        
        for exe_name in ejecutables_esperados:
            exe_path = self.directorio_dist / exe_name
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                info["ejecutables"].append({
                    "nombre": exe_name,
                    "ruta": str(exe_path),
                    "tamaño_mb": round(size_mb, 1),
                    "fecha_creacion": datetime.fromtimestamp(exe_path.stat().st_mtime).isoformat()
                })
        
        info_file = self.directorio_dist / "info_compilacion.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        self.log(f"Información de compilación guardada: {info_file}")
        
        # Crear archivo README para el directorio dist
        readme_content = """# Sincronizador Biométrico - Ejecutables

## Archivos Incluidos

### SincronizadorBiometrico.exe
- **Propósito**: Aplicación principal con interfaz gráfica
- **Uso**: Doble clic para ejecutar
- **Características**: Interfaz completa, configuración, sincronización automática

### StartupManager.exe  
- **Propósito**: Gestor de inicio automático con Windows
- **Uso**: Desde línea de comandos
- **Comandos**:
  - `StartupManager.exe --enable` - Habilitar inicio automático
  - `StartupManager.exe --disable` - Deshabilitar inicio automático
  - `StartupManager.exe --status` - Ver estado actual
  - `StartupManager.exe --test` - Probar funcionalidad

### InstaladorSincronizadorBiometrico.exe
- **Propósito**: Instalador completo del sistema
- **Uso**: Para distribución e instalación en nuevos equipos
- **Características**: Instala dependencias, configura startup, crea accesos directos

## Instalación y Uso

1. **Uso directo**: Simplemente ejecutar `SincronizadorBiometrico.exe`
2. **Instalación completa**: Ejecutar `InstaladorSincronizadorBiometrico.exe`
3. **Configurar startup**: Usar `StartupManager.exe --enable`

## Notas Técnicas

- Los ejecutables son autocontenidos (no requieren Python instalado)
- Se recomienda crear una carpeta dedicada para todos los archivos
- Los logs se crean en la carpeta `logs/` relativa al ejecutable
- La configuración se guarda en archivos JSON en el mismo directorio

## Solución de Problemas

- Si hay problemas de permisos, ejecutar como administrador
- Para inicio automático, verificar que no esté bloqueado por antivirus
- Los logs contienen información detallada para diagnóstico
"""
        
        readme_file = self.directorio_dist / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.log(f"README creado: {readme_file}")
    
    def mostrar_resumen(self):
        """Mostrar resumen de la compilación"""
        self.log("=" * 60)
        self.log("RESUMEN DE COMPILACIÓN")
        self.log("=" * 60)
        
        if not self.directorio_dist.exists():
            self.log("❌ No se encontró directorio de distribución", "ERROR")
            return
        
        ejecutables = list(self.directorio_dist.glob("*.exe"))
        
        if ejecutables:
            self.log(f"✅ Compilación completada. Ejecutables generados: {len(ejecutables)}")
            self.log("")
            
            total_size = 0
            for exe in ejecutables:
                size_mb = exe.stat().st_size / (1024 * 1024)
                total_size += size_mb
                self.log(f"📦 {exe.name} - {size_mb:.1f} MB")
            
            self.log("")
            self.log(f"📊 Tamaño total: {total_size:.1f} MB")
            self.log(f"📁 Ubicación: {self.directorio_dist}")
            
            self.log("")
            self.log("🚀 INSTRUCCIONES DE USO:")
            self.log("   1. Para usar: Ejecutar SincronizadorBiometrico.exe")
            self.log("   2. Para startup automático: StartupManager.exe --enable")
            self.log("   3. Para distribución: Usar InstaladorSincronizadorBiometrico.exe")
            self.log("")
            self.log("📋 Los archivos están listos para distribución")
        else:
            self.log("❌ No se generaron ejecutables", "ERROR")

def main():
    parser = argparse.ArgumentParser(
        description='Compilador Integrado para Sincronizador Biométrico',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python compilar_sincronizador.py                    # Compilar todo
  python compilar_sincronizador.py --main-only        # Solo sincronizador
  python compilar_sincronizador.py --startup-only     # Solo gestor startup
  python compilar_sincronizador.py --installer-only   # Solo instalador
  python compilar_sincronizador.py --debug            # Con información debug
        """
    )
    
    parser.add_argument('--main-only', action='store_true',
                       help='Compilar solo el sincronizador principal')
    parser.add_argument('--startup-only', action='store_true',
                       help='Compilar solo el gestor de startup')
    parser.add_argument('--installer-only', action='store_true',
                       help='Compilar solo el instalador')
    parser.add_argument('--debug', action='store_true',
                       help='Compilar con información de depuración')
    parser.add_argument('--onedir', action='store_true',
                       help='Crear directorio con archivos (en lugar de un solo exe)')
    parser.add_argument('--console', action='store_true',
                       help='Mostrar consola en el ejecutable principal')
    
    args = parser.parse_args()
    
    compilador = CompiladorSincronizador()
    
    print("🔨 COMPILADOR INTEGRADO SINCRONIZADOR BIOMÉTRICO")
    print("=" * 60)
    
    # Verificar dependencias
    if not compilador.verificar_dependencias():
        print("❌ Error en verificación de dependencias")
        return 1
    
    # Limpiar directorios anteriores
    compilador.limpiar_directorios()
    
    # Determinar qué compilar
    if args.main_only:
        compilar_main, compilar_startup, compilar_installer = True, False, False
    elif args.startup_only:
        compilar_main, compilar_startup, compilar_installer = False, True, False
    elif args.installer_only:
        compilar_main, compilar_startup, compilar_installer = False, False, True
    else:
        # Por defecto compilar todo
        compilar_main, compilar_startup, compilar_installer = True, True, True
    
    onefile = not args.onedir
    windowed = not args.console
    
    exito_total = True
    
    # Compilar componentes en orden
    if compilar_main:
        if not compilador.compilar_sincronizador(onefile, windowed, args.debug):
            exito_total = False
    
    if compilar_startup and exito_total:
        if not compilador.compilar_startup_manager(onefile, args.debug):
            exito_total = False
    
    if compilar_installer and exito_total:
        if not compilador.compilar_instalador():
            exito_total = False
    
    # Crear documentación
    if exito_total:
        compilador.crear_informacion_compilacion()
    
    # Mostrar resumen final
    compilador.mostrar_resumen()
    
    return 0 if exito_total else 1

if __name__ == "__main__":
    sys.exit(main())
