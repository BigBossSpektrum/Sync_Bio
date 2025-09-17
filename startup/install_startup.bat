@echo off
REM ==============================================================
REM Instalador de Startup - Sincronizador Biométrico
REM ==============================================================
REM Este archivo configura el sincronizador para iniciarse
REM automáticamente con Windows.
REM ==============================================================

title Instalador de Startup - Sincronizador Biometrico

echo.
echo ===============================================
echo    INSTALADOR DE STARTUP AUTOMATICO
echo    Sincronizador Biometrico
echo ===============================================
echo.

REM Obtener directorio actual
set "CURRENT_DIR=%~dp0"
set "MAIN_BAT=%CURRENT_DIR%start_sync_service.bat"
set "LOG_FILE=%CURRENT_DIR%instalacion_startup.log"

REM Función para escribir al log
:write_log
echo [%date% %time%] %1 >> "%LOG_FILE%"
goto :eof

call :write_log "=== Iniciando instalacion de startup ==="

echo Verificando archivos necesarios...

REM Verificar que existe el archivo principal
if not exist "%MAIN_BAT%" (
    echo.
    echo ❌ ERROR: No se encuentra start_sync_service.bat
    echo Asegurate de ejecutar este archivo desde la carpeta correcta
    echo.
    call :write_log "ERROR: start_sync_service.bat no encontrado"
    pause
    exit /b 1
)

echo ✅ Archivos verificados correctamente
call :write_log "Archivos verificados - start_sync_service.bat encontrado"

echo.
echo Configurando inicio automatico con Windows...

REM Método 1: Crear acceso directo en carpeta Startup
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_BAT=%STARTUP_FOLDER%\SincronizadorBiometricoStartup.bat"

echo Creando script de inicio en: %STARTUP_FOLDER%
call :write_log "Creando script en carpeta Startup"

REM Crear el archivo .bat en la carpeta de startup
(
echo @echo off
echo REM Auto-generado por el instalador del Sincronizador Biometrico
echo REM Fecha: %date% %time%
echo.
echo REM Esperar 30 segundos para que Windows termine de cargar
echo timeout /t 30 /nobreak ^>nul 2^>^&1
echo.
echo REM Cambiar al directorio del sincronizador
echo cd /d "%CURRENT_DIR%"
echo.
echo REM Ejecutar el sincronizador en modo startup
echo start /B /MIN "" "%MAIN_BAT%" --startup
echo.
echo REM Log de inicio
echo echo [%%date%% %%time%%] Sincronizador iniciado desde startup ^>^> "%CURRENT_DIR%startup_log.txt"
) > "%SHORTCUT_BAT%"

REM Verificar que se creó correctamente
if exist "%SHORTCUT_BAT%" (
    echo ✅ Script de startup creado exitosamente
    call :write_log "Script de startup creado en: %SHORTCUT_BAT%"
) else (
    echo ❌ Error creando script de startup
    call :write_log "ERROR: No se pudo crear script de startup"
    goto :error_cleanup
)

REM Método 2: Registro de Windows (alternativo)
echo.
echo Configurando entrada en el Registro de Windows...
call :write_log "Configurando entrada en registro de Windows"

REM Crear script temporal para el registro
set "TEMP_REG=%TEMP%\sync_startup.reg"
(
echo Windows Registry Editor Version 5.00
echo.
echo [HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run]
echo "SincronizadorBiometrico"="%SHORTCUT_BAT:\=\\%"
) > "%TEMP_REG%"

REM Importar al registro
reg import "%TEMP_REG%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Entrada del registro configurada
    call :write_log "Entrada de registro creada exitosamente"
) else (
    echo ⚠️  Advertencia: No se pudo configurar el registro
    call :write_log "ADVERTENCIA: Fallo configuracion de registro"
)

REM Limpiar archivo temporal
if exist "%TEMP_REG%" del "%TEMP_REG%" >nul 2>&1

echo.
echo ===============================================
echo           INSTALACION COMPLETADA
echo ===============================================
echo.
echo ✅ El Sincronizador Biometrico se iniciara automaticamente
echo    cuando Windows se inicie.
echo.
echo 📁 Ubicacion del servicio: %CURRENT_DIR%
echo 📄 Log de instalacion: %LOG_FILE%
echo 📄 Log de startup: %CURRENT_DIR%startup_log.txt
echo.
echo ⚙️  Para verificar la instalacion:
echo    - Ve a Configuracion ^> Aplicaciones ^> Inicio
echo    - Busca "SincronizadorBiometricoStartup"
echo.
echo 🧪 Para probar ahora:
echo    - Ejecuta: start_sync_service.bat
echo.
echo ❌ Para desinstalar:
echo    - Elimina el archivo: %SHORTCUT_BAT%
echo    - O ejecuta: uninstall_startup.bat
echo.

call :write_log "=== Instalacion completada exitosamente ==="

REM Preguntar si quiere probar ahora
echo.
set /p "test_now=¿Quieres probar el sincronizador ahora? (s/n): "
if /i "%test_now%"=="s" (
    echo.
    echo Iniciando sincronizador...
    call :write_log "Usuario eligio probar sincronizador inmediatamente"
    start "" "%MAIN_BAT%"
) else (
    call :write_log "Usuario eligio no probar ahora"
)

echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
exit /b 0

:error_cleanup
echo.
echo ===============================================
echo              ERROR EN INSTALACION
echo ===============================================
echo.
echo ❌ No se pudo completar la instalacion del startup automatico
echo.
echo Posibles causas:
echo - Permisos insuficientes
echo - Antivirus bloqueando la operacion
echo - Carpeta de startup no accesible
echo.
echo Intenta:
echo 1. Ejecutar como Administrador
echo 2. Desactivar temporalmente el antivirus
echo 3. Verificar permisos de la carpeta
echo.
call :write_log "ERROR: Instalacion fallida"
echo Presiona cualquier tecla para salir...
pause >nul
exit /b 1
