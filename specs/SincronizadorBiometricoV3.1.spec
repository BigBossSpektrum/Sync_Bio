# -*- mode: python ; coding: utf-8 -*-

# Configuración para SincronizadorBiometrico V3.1
# Versión 3.1 - UI mejorada con threading.Event para mejor responsividad

import sys
import os

# Agregar imports necesarios para el análisis estático
hiddenimports = [
    'pystray',
    'pystray._base',
    'pystray._util',
    'pystray._util.win32',
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
    'concurrent.futures',
    'multiprocessing'
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
        'PySide6',
        'tornado',
        'IPython'
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
    name='SincronizadorBiometricoV3.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # SIN CONSOLA - versión final
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icono.ico'],
    version_info={
        'version': '3.1.0.0',
        'description': 'Sincronizador Biométrico V3.1 - UI mejorada con threading.Event',
        'product_name': 'SincronizadorBiometricoV3.1',
        'file_description': 'Sincronizador Biométrico V3.1 - Threading mejorado',
        'company_name': 'Entrecables y Redes',
        'copyright': '© 2025 Entrecables y Redes',
        'internal_name': 'SincronizadorBiometricoV3.1'
    }
)