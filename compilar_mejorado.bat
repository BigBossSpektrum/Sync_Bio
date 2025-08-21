@echo off
echo ================================================
echo   Compilador del Sincronizador Biometrico Mejorado
echo ================================================
echo.

REM Verificar si existe el entorno virtual
if not exist "env\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual 'env'
    echo Ejecuta primero 'ejecutar_mejorado.bat' para crear el entorno
    pause
    exit /b 1
)

REM Activar entorno virtual
echo [INFO] Activando entorno virtual...
call env\Scripts\activate.bat

REM Instalar PyInstaller si no está instalado
echo [INFO] Verificando PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] No se pudo instalar PyInstaller
    pause
    exit /b 1
)

REM Limpiar compilaciones anteriores
echo [INFO] Limpiando compilaciones anteriores...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo [INFO] Compilando aplicacion...
echo.
echo ================================================

REM Compilar con PyInstaller
pyinstaller sincronizador_mejorado.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Error durante la compilacion
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Compilacion completada exitosamente!
echo ================================================
echo.
echo El ejecutable se encuentra en: dist\SincronizadorBiometricoMejorado.exe
echo.

REM Copiar archivos necesarios al directorio de distribución
echo [INFO] Copiando archivos adicionales...
if not exist "dist\logs" mkdir "dist\logs"
copy "biometrico_config_ejemplo.json" "dist\" >nul 2>&1
copy "README.md" "dist\" >nul 2>&1
copy "icono.ico" "dist\" >nul 2>&1

echo [INFO] Archivos copiados al directorio de distribucion
echo.
echo ================================================
echo   LISTO PARA DISTRIBUIR
echo ================================================

pause
