# -*- mode: python ; coding: utf-8 -*-

# Configuración OPTIMIZADA para SincronizadorBiometrico V2.1
# Versión 2.1 - Sincronizador Biométrico Mejorado

import sys
import os

# Agregar imports necesarios para el análisis estático
hiddenimports = [
    'pystray',
    'pystray.darwin',
    'pystray.win32',
    'pystray._base',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'threading',
    'requests',
    'json',
    'logging',
    'logging.handlers',
    'zk',
    'datetime',
    'socket',
    'subprocess',
    'sys',
    'os',
    'time',
    'winreg',
    'tempfile',
    'traceback',
    'queue',
    'concurrent',
    'concurrent.futures'
]

a = Analysis(
    ['sincronizador_biometrico_mejorado.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icono.ico', '.'), 
        ('requirements.txt', '.'), 
        ('biometrico_config.json', '.'), 
        ('instalador_config.json', '.'),
        ('SOLUCION_BANDEJA_SISTEMA.md', '.'),
        ('test_tray_functionality.py', '.')
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'numpy.testing',
        'PIL.ImageQt',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6'
    ],
    noarchive=False,
    optimize=2,  # Optimización nivel 2 para mejor rendimiento
)

# Filtrar datos innecesarios para reducir tamaño
a.datas = [x for x in a.datas if not any(exclude in x[0].lower() for exclude in [
    'test', 'example', 'sample', 'demo', '__pycache__'
])]

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SincronizadorBiometricoV2.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sin consola para mejor experiencia
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icono.ico'],
    version_info={
        'version': '2.1.0.0',
        'description': 'Sincronizador Biométrico V2.1 - Versión mejorada y optimizada',
        'product_name': 'SincronizadorBiometricoV2.1',
        'file_description': 'Sincronizador Biométrico V2.1 Mejorado',
        'company_name': 'Entrecables y Redes',
        'copyright': '© 2025 Entrecables y Redes',
        'internal_name': 'SincronizadorBiometricoV2.1'
    }
)
