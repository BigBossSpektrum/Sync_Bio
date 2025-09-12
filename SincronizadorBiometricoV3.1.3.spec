# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['sincronizador_biometrico_mejorado.py'],
    pathex=[],
    binaries=[],
    datas=[('biometrico_config.json', '.'), ('icono.ico', '.')],
    hiddenimports=['PIL', 'PIL.Image', 'PIL._tkinter_finder', 'tkinter', 'tkinter.messagebox', 'tkinter.simpledialog', 'tkinter.ttk', 'pystray', 'threading', 'queue', 'json', 'datetime', 'logging', 'logging.handlers', 'os', 'sys', 'subprocess', 'time', 'requests', 'winreg', 'pathlib'],
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
    name='SincronizadorBiometricoV3.1.3',
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
)
