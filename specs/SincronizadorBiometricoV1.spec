# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# Configuración del archivo spec para SincronizadorBiometricoV1
block_cipher = None

# Datos adicionales que deben incluirse
added_files = [
    ('icono.ico', '.'),  # Incluir icono si existe
]

# Verificar si existe el icono
if not os.path.exists('icono.ico'):
    added_files = []

# Módulos ocultos necesarios
hiddenimports = [
    'tkinter',
    'tkinter.ttk', 
    'tkinter.messagebox',
    'tkinter.filedialog',
    'threading',
    'json',
    'requests',
    'logging',
    'logging.handlers',
    'time',
    'datetime',
    'socket',
    'subprocess',
    'pystray',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'sys',
    'os',
    'zk',
    'winreg',
    'tempfile',
    'fcntl'
]

a = Analysis(
    ['sincronizador_biometrico_mejorado.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas'],  # Excluir librerías grandes innecesarias
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SincronizadorBiometricoV1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Ventana sin consola para aplicación GUI
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icono.ico' if os.path.exists('icono.ico') else None,
    version_info={
        'version': (1, 0, 0, 0),
        'file_description': 'Sincronizador Biométrico V1',
        'product_name': 'Sincronizador Biométrico',
        'company_name': 'Entrecables y Redes',
        'copyright': '© 2025 Entrecables y Redes',
        'internal_name': 'SincronizadorBiometricoV1',
        'original_filename': 'SincronizadorBiometricoV1.exe'
    }
)
