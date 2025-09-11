# -*- mode: python ; coding: utf-8 -*-

# Configuración para SincronizadorBiometrico V2
# Incluye todas las mejoras de bandeja del sistema y funcionalidades nuevas

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
    hiddenimports=[
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
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
        'winreg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SincronizadorBiometricoV2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icono.ico'],
    version_info={
        'version': '2.0.0.0',
        'description': 'Sincronizador Biométrico V2 - Versión mejorada con bandeja del sistema',
        'product_name': 'SincronizadorBiometricoV2',
        'file_description': 'Sincronizador Biométrico V2',
        'company_name': 'Entrecables y Redes',
        'copyright': '© 2025 Entrecables y Redes',
        'internal_name': 'SincronizadorBiometricoV2'
    }
)
