@echo off
echo ====================================
echo  Compilando Instalador Biometrico
echo ====================================

REM Verificar si PyInstaller está instalado
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller no está instalado. Instalando...
    python -m pip install pyinstaller
)

REM Limpiar builds anteriores
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo Compilando instalador...
python -m PyInstaller instalador_completo.spec

REM Verificar si la compilación fue exitosa
if exist "dist\InstaladorSincronizadorBiometrico.exe" (
    echo.
    echo ====================================
    echo  Compilación exitosa!
    echo ====================================
    echo El archivo ejecutable está en: dist\InstaladorSincronizadorBiometrico.exe
    echo.
    echo Abriendo carpeta de destino...
    explorer dist
) else (
    echo.
    echo ====================================
    echo  Error en la compilación
    echo ====================================
    echo Revisa los mensajes de error arriba.
)

pause
