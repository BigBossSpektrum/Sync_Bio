@echo off
REM ============================================================
REM Script de Compilación para Sincronizador Biométrico
REM ============================================================
REM Este archivo .bat facilita la compilación del proyecto
REM
REM Uso:
REM   compilar.bat              - Compilar todo
REM   compilar.bat main         - Solo sincronizador principal
REM   compilar.bat startup      - Solo gestor de startup
REM   compilar.bat installer    - Solo instalador
REM   compilar.bat debug        - Compilar con debug
REM ============================================================

title Compilador Sincronizador Biometrico

REM Obtener directorio del script
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%~dp0.."
set "PYTHON_EXE=%PROJECT_DIR%\env\Scripts\python.exe"
set "COMPILER_SCRIPT=%SCRIPT_DIR%compilar_sincronizador.py"

echo.
echo ============================================================
echo   COMPILADOR SINCRONIZADOR BIOMETRICO
echo ============================================================
echo.

REM Verificar que existe el entorno virtual
if not exist "%PYTHON_EXE%" (
    echo ❌ ERROR: No se encuentra el entorno virtual de Python
    echo Expected: %PYTHON_EXE%
    echo.
    echo Solucion:
    echo 1. Asegurate de que el entorno virtual este creado
    echo 2. O ejecuta: python -m venv env
    echo 3. Y luego: %SCRIPT_DIR%env\Scripts\activate
    echo 4. Y finalmente: pip install -r config/requirements.txt
    echo.
    pause
    exit /b 1
)

REM Verificar que existe el script compilador
if not exist "%COMPILER_SCRIPT%" (
    echo ❌ ERROR: No se encuentra el script compilador
    echo Expected: %COMPILER_SCRIPT%
    echo.
    pause
    exit /b 1
)

echo ✅ Entorno Python encontrado: %PYTHON_EXE%
echo ✅ Script compilador encontrado
echo.

REM Determinar argumentos según parámetro
set "ARGS="

if "%1"=="main" (
    set "ARGS=--main-only"
    echo 🔨 Modo: Compilar solo sincronizador principal
) else if "%1"=="startup" (
    set "ARGS=--startup-only"
    echo 🔨 Modo: Compilar solo gestor de startup
) else if "%1"=="installer" (
    set "ARGS=--installer-only"
    echo 🔨 Modo: Compilar solo instalador
) else if "%1"=="debug" (
    set "ARGS=--debug"
    echo 🔨 Modo: Compilar todo con debug
) else (
    echo 🔨 Modo: Compilar todo (completo)
)

echo.
echo Iniciando compilación...
echo Esto puede tomar varios minutos...
echo.

REM Ejecutar compilador
"%PYTHON_EXE%" "%COMPILER_SCRIPT%" %ARGS%

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE% equ 0 (
    echo ============================================================
    echo ✅ COMPILACIÓN COMPLETADA EXITOSAMENTE
    echo ============================================================
    echo.
    echo Los ejecutables se encuentran en: %SCRIPT_DIR%dist\
    echo.
    echo Archivos generados:
    if exist "%SCRIPT_DIR%dist\SincronizadorBiometrico.exe" (
        echo   ✅ SincronizadorBiometrico.exe
    )
    if exist "%SCRIPT_DIR%dist\StartupManager.exe" (
        echo   ✅ StartupManager.exe
    )
    if exist "%SCRIPT_DIR%dist\InstaladorSincronizadorBiometrico.exe" (
        echo   ✅ InstaladorSincronizadorBiometrico.exe
    )
    echo.
    echo Para usar:
    echo   • Ejecutar SincronizadorBiometrico.exe
    echo   • Para inicio automático: StartupManager.exe --enable
    echo.
) else (
    echo ============================================================
    echo ❌ ERROR EN LA COMPILACIÓN
    echo ============================================================
    echo.
    echo Código de error: %EXIT_CODE%
    echo Revisa los mensajes de error arriba
    echo.
)

echo Presiona cualquier tecla para continuar...
pause >nul

exit /b %EXIT_CODE%
