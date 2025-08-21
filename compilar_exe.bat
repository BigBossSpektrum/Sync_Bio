@echo off
echo ================================
echo Compilando Sincronizacion Biometrica
echo ================================
echo.

REM Activar el entorno virtual si existe
if exist "env\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call env\Scripts\activate.bat
)

REM Limpiar archivos de compilacion anterior
if exist "build" (
    echo Limpiando archivos de compilacion anterior...
    rmdir /s /q build
)
if exist "dist" (
    echo Limpiando ejecutables anteriores...
    rmdir /s /q dist
)

REM Compilar con PyInstaller
echo Compilando aplicacion...
pyinstaller --onefile --windowed --name "SincronizacionBiometrica" --icon icono.ico syncronizar_bio.py

REM Verificar si la compilacion fue exitosa
if exist "dist\SincronizacionBiometrica.exe" (
    echo.
    echo ================================
    echo COMPILACION EXITOSA!
    echo ================================
    echo Ejecutable creado en: dist\SincronizacionBiometrica.exe
    echo Tamano del archivo:
    for %%I in ("dist\SincronizacionBiometrica.exe") do echo %%~zI bytes
    echo.
    echo Presiona cualquier tecla para salir...
    pause >nul
) else (
    echo.
    echo ================================
    echo ERROR EN LA COMPILACION
    echo ================================
    echo Revisa los mensajes de error arriba.
    echo.
    echo Presiona cualquier tecla para salir...
    pause >nul
)
