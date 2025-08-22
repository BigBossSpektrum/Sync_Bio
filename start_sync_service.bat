@echo off
REM ==============================================================
REM Sincronizador Biométrico - Servicio Automático
REM ==============================================================
REM Este archivo .bat inicia el sincronizador biométrico en segundo plano
REM y lo configura para ejecutarse automáticamente con Windows.
REM 
REM Uso:
REM   start_sync_service.bat            - Inicia el servicio normalmente
REM   start_sync_service.bat --install  - Instala en startup de Windows
REM   start_sync_service.bat --startup  - Modo startup (silencioso)
REM ==============================================================

title Sincronizador Biometrico - Iniciando...

REM Obtener directorio del script
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%sync_service.py"
set "VENV_DIR=%SCRIPT_DIR%env"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "LOG_FILE=%SCRIPT_DIR%sync_service.log"

REM Verificar modo de ejecución
set "STARTUP_MODE=0"
set "INSTALL_MODE=0"

if "%1"=="--startup" set "STARTUP_MODE=1"
if "%1"=="--install" set "INSTALL_MODE=1"

REM Función para escribir al log
:write_log
echo [%date% %time%] %1 >> "%LOG_FILE%"
goto :eof

REM ============== MODO INSTALACIÓN ==============
if "%INSTALL_MODE%"=="1" (
    echo.
    echo ===============================================
    echo   INSTALANDO SINCRONIZADOR EN STARTUP
    echo ===============================================
    echo.
    
    call :write_log "Iniciando instalacion en startup de Windows"
    
    REM Crear acceso directo en Startup
    set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    set "SHORTCUT_PATH=%STARTUP_FOLDER%\SincronizadorBiometrico.bat"
    
    echo Creando acceso directo en startup...
    echo @echo off > "%SHORTCUT_PATH%"
    echo cd /d "%SCRIPT_DIR%" >> "%SHORTCUT_PATH%"
    echo "%~f0" --startup >> "%SHORTCUT_PATH%"
    
    if exist "%SHORTCUT_PATH%" (
        echo.
        echo ✅ INSTALACION COMPLETADA
        echo El sincronizador se iniciara automaticamente con Windows
        echo.
        call :write_log "Instalacion en startup completada exitosamente"
    ) else (
        echo.
        echo ❌ ERROR EN LA INSTALACION
        echo No se pudo crear el acceso directo
        echo.
        call :write_log "Error en instalacion: No se pudo crear acceso directo"
    )
    
    echo Presiona cualquier tecla para continuar...
    pause >nul
    goto :end
)

REM ============== VERIFICACIONES INICIALES ==============
if "%STARTUP_MODE%"=="1" (
    REM Modo silencioso para startup
    call :write_log "Iniciando en modo startup silencioso"
) else (
    REM Modo normal con interfaz
    echo.
    echo ===============================================
    echo    SINCRONIZADOR BIOMETRICO - SERVICIO
    echo ===============================================
    echo.
    echo Iniciando verificaciones del sistema...
    echo.
)

REM Verificar si existe el script Python
if not exist "%PYTHON_SCRIPT%" (
    echo ❌ ERROR: No se encuentra el archivo sync_service.py
    call :write_log "ERROR: sync_service.py no encontrado"
    if "%STARTUP_MODE%"=="0" pause
    goto :end
)

REM Verificar entorno virtual
if not exist "%PYTHON_EXE%" (
    if "%STARTUP_MODE%"=="0" (
        echo ⚠️  Entorno virtual no encontrado, usando Python del sistema...
    )
    call :write_log "Usando Python del sistema - entorno virtual no encontrado"
    set "PYTHON_EXE=python"
) else (
    if "%STARTUP_MODE%"=="0" (
        echo ✅ Entorno virtual encontrado
    )
    call :write_log "Usando entorno virtual Python"
)

REM Verificar configuración
set "CONFIG_FILE=%SCRIPT_DIR%biometrico_config.json"
if not exist "%CONFIG_FILE%" (
    if "%STARTUP_MODE%"=="0" (
        echo ⚠️  Archivo de configuracion no encontrado
        echo Se usara configuracion por defecto
    )
    call :write_log "Configuracion por defecto - archivo config no encontrado"
) else (
    if "%STARTUP_MODE%"=="0" (
        echo ✅ Archivo de configuracion encontrado
    )
    call :write_log "Configuracion cargada desde archivo"
)

REM ============== INSTALACIÓN DE DEPENDENCIAS ==============
if "%STARTUP_MODE%"=="0" (
    echo.
    echo Verificando dependencias de Python...
)

call :write_log "Verificando dependencias Python"

REM Verificar e instalar dependencias si es necesario
"%PYTHON_EXE%" -c "import requests, zk" 2>nul
if errorlevel 1 (
    if "%STARTUP_MODE%"=="0" (
        echo ⚠️  Instalando dependencias necesarias...
    )
    call :write_log "Instalando dependencias faltantes"
    
    "%PYTHON_EXE%" -m pip install requests pyzk pillow 2>nul
    if errorlevel 1 (
        echo ❌ Error instalando dependencias
        call :write_log "ERROR: Fallo instalacion de dependencias"
        if "%STARTUP_MODE%"=="0" pause
        goto :end
    )
) else (
    if "%STARTUP_MODE%"=="0" (
        echo ✅ Dependencias verificadas
    )
    call :write_log "Dependencias verificadas correctamente"
)

REM ============== INICIO DEL SERVICIO ==============
if "%STARTUP_MODE%"=="0" (
    echo.
    echo ===============================================
    echo      INICIANDO SERVICIO DE SINCRONIZACION
    echo ===============================================
    echo.
    echo 🚀 Iniciando sincronizador biometrico...
    echo 📁 Directorio: %SCRIPT_DIR%
    echo 📄 Log: %LOG_FILE%
    echo.
    echo Para detener el servicio, presiona Ctrl+C
    echo Para minimizar esta ventana, presiona Ctrl+Z
    echo.
)

call :write_log "Iniciando servicio de sincronizacion"

REM Cambiar al directorio del script
cd /d "%SCRIPT_DIR%"

REM Iniciar el servicio Python
if "%STARTUP_MODE%"=="1" (
    REM Modo startup - ejecutar en segundo plano sin ventana visible
    start /B /MIN "" "%PYTHON_EXE%" "%PYTHON_SCRIPT%" --startup
    call :write_log "Servicio iniciado en modo startup (segundo plano)"
) else (
    REM Modo normal - mostrar salida
    "%PYTHON_EXE%" "%PYTHON_SCRIPT%"
    
    echo.
    echo 🏁 Servicio finalizado
    call :write_log "Servicio finalizado normalmente"
    echo.
    echo Presiona cualquier tecla para cerrar...
    pause >nul
)

:end
exit /b 0
