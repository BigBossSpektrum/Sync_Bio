#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Reorganización del Proyecto Sync_Bio
=============================================
Organiza automáticamente todos los archivos en una estructura más limpia.
"""
import os
import shutil
from pathlib import Path

def reorganizar_proyecto():
    """Reorganiza los archivos del proyecto en una estructura más limpia"""
    
    # Directorio base del proyecto
    base_dir = Path.cwd()
    
    # Definir estructura de directorios
    directorios = {
        'src': [
            'sincronizador_biometrico_mejorado.py',
            'startup_manager.py', 
            'instalador_gui.py',
            'demo_app.py',
            'demo_persistencia.py',
            'diagnostico_biometrico.py',
            'calculos.py',
            'registros.py',
            'utils.py',
            'sync_service.py',
            'syncronizar_bio.py',
            'sincronizar_biometrico.py',
            'launcher.py',
            'instalador_completo.py'
        ],
        'scripts': [
            'compilar_sincronizador.py',
            'compilar_sincronizador_nuevo.py',
            'compilar_instalador.py',
            'compilar_todo.bat',
            'compilar.bat',
            'compilar_instalador.bat',
            'clean_emojis.py',
            'fix_emojis.py'
        ],
        'config': [
            'biometrico_config.json',
            'requirements.txt',
            'instalador_config_default.json',
            'instalador_config.json'
        ],
        'startup': [
            'install_startup.bat',
            'start_sync_service.bat',
            'activar_autostart.py',
            'configurar_autostart_v1.py'
        ],
        'docs': [
            'README_Servicio.md',
            'README_SincronizadorV1.md',
            'CHANGELOG_V3.1.1.md'
        ],
        'logs': [
            'biometrico_sync.log',
            'desinstalacion_startup.log',
            'instalacion_startup.log',
            'sync_service.log'
        ],
        'assets': [
            'icono.ico'
        ],
        'build_info': [
            'info_compilacion_v1.json',
            'info_compilacion_v3.1.5.json',
            'info_compilacion_v3.2.json'
        ],
        'specs': [
            'instalador_completo.spec',
            'SincronizadorBiometrico.spec',
            'SincronizadorBiometricoV1.spec',
            'SincronizadorBiometricoV2_Fixed.spec',
            'SincronizadorBiometricoV2.1_Final.spec',
            'SincronizadorBiometricoV2.1_Fixed.spec',
            'SincronizadorBiometricoV2.1_NoTray.spec',
            'SincronizadorBiometricoV2.1.spec',
            'SincronizadorBiometricoV2.spec',
            'SincronizadorBiometricoV3.1.1.spec',
            'SincronizadorBiometricoV3.1.2.spec',
            'SincronizadorBiometricoV3.1.3.spec',
            'SincronizadorBiometricoV3.1.4.spec',
            'SincronizadorBiometricoV3.1.5.spec',
            'SincronizadorBiometricoV3.1.spec',
            'SincronizadorBiometricoV3.2.spec',
            'SincronizadorBiometricoV3.spec',
            'StartupManager.spec'
        ]
    }
    
    print("🔄 Iniciando reorganización del proyecto...")
    print("=" * 50)
    
    # Crear directorios
    for directorio in directorios.keys():
        dir_path = base_dir / directorio
        dir_path.mkdir(exist_ok=True)
        print(f"📁 Creado directorio: {directorio}")
    
    # Mover archivos
    archivos_movidos = 0
    archivos_no_encontrados = []
    
    for directorio, archivos in directorios.items():
        print(f"\n📂 Procesando directorio: {directorio}")
        for archivo in archivos:
            archivo_origen = base_dir / archivo
            archivo_destino = base_dir / directorio / archivo
            
            if archivo_origen.exists():
                try:
                    # Verificar si el archivo ya está en el destino
                    if archivo_destino.exists():
                        print(f"⚠️ Ya existe en destino: {archivo}")
                        continue
                        
                    shutil.move(str(archivo_origen), str(archivo_destino))
                    print(f"✅ Movido: {archivo} → {directorio}/")
                    archivos_movidos += 1
                except Exception as e:
                    print(f"❌ Error moviendo {archivo}: {e}")
            else:
                archivos_no_encontrados.append(archivo)
    
    # Crear README.md principal si no existe
    readme_principal = base_dir / "README.md"
    if not readme_principal.exists():
        crear_readme_principal(readme_principal)
        print("✅ Creado README.md principal")
    
    # Crear .gitignore si no existe
    gitignore_file = base_dir / ".gitignore"
    if not gitignore_file.exists():
        crear_gitignore(gitignore_file)
        print("✅ Creado .gitignore")
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE REORGANIZACIÓN")
    print("=" * 50)
    print(f"✅ Archivos movidos: {archivos_movidos}")
    print(f"📁 Directorios creados: {len(directorios)}")
    
    if archivos_no_encontrados:
        print(f"\n⚠️ Archivos no encontrados ({len(archivos_no_encontrados)}):")
        for archivo in archivos_no_encontrados:
            print(f"  - {archivo}")
    
    print("\n🎉 Reorganización completada!")
    print("\n📝 Próximos pasos recomendados:")
    print("1. Actualizar rutas en archivos .bat")
    print("2. Verificar imports en archivos Python")
    print("3. Probar compilación con nueva estructura")
    print("4. Actualizar documentación")

def crear_readme_principal(archivo_path):
    """Crea un README.md principal para el proyecto"""
    contenido = """# Sync_Bio - Sincronizador Biométrico

Sistema de sincronización biométrica desarrollado para automatizar procesos de autenticación y registro.

## 📁 Estructura del Proyecto

```
Sync_Bio/
├── 📁 src/          # Código fuente principal
├── 📁 scripts/      # Scripts de compilación y utilidades  
├── 📁 config/       # Archivos de configuración
├── 📁 startup/      # Scripts de inicio automático
├── 📁 docs/         # Documentación
├── 📁 logs/         # Archivos de log
├── 📁 assets/       # Recursos (iconos, imágenes)
├── 📁 build_info/   # Información de compilación
├── 📁 specs/        # Archivos .spec de PyInstaller
├── 📁 build/        # Archivos temporales de compilación
└── 📁 dist/         # Ejecutables compilados
```

## 🚀 Inicio Rápido

1. Instalar dependencias: `pip install -r config/requirements.txt`
2. Configurar parámetros en `config/biometrico_config.json`
3. Ejecutar: `python src/sincronizador_biometrico_mejorado.py`

## 📚 Documentación

- [Servicio de Sincronización](docs/README_Servicio.md)
- [Sincronizador V1](docs/README_SincronizadorV1.md)
- [Changelog](docs/CHANGELOG_V3.1.1.md)

## 🛠️ Compilación

Ejecutar scripts de compilación desde el directorio `scripts/`:
- `python compilar_sincronizador.py`
- `compilar_todo.bat`

## 📝 Licencia

Proyecto privado - Entrecables y Redes
"""
    
    with open(archivo_path, 'w', encoding='utf-8') as f:
        f.write(contenido)

def crear_gitignore(archivo_path):
    """Crea un archivo .gitignore apropiado"""
    contenido = """# Directorios de compilación
dist/
build/
__pycache__/
*.pyc
*.pyo

# Logs
logs/*.log
!logs/.gitkeep

# Configuración local
config/.env
config/biometrico_config_local.json

# Archivos temporales
*.tmp
*.temp
*.bak

# Archivos de Windows
Thumbs.db
ehthumbs.db
Desktop.ini

# Archivos del sistema
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes

# PyInstaller
*.spec.bak

# Entornos virtuales
env/
venv/
ENV/
env.bak/
venv.bak/
"""
    
    with open(archivo_path, 'w', encoding='utf-8') as f:
        f.write(contenido)

if __name__ == "__main__":
    reorganizar_proyecto()