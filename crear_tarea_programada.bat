@echo off
echo ========================================
echo Configurador de Tarea Programada
echo Sincronizacion Biometrica cada 5 minutos
echo ========================================
echo.

set EXE_PATH=%~dp0dist\SincronizacionBiometricaService.exe
set TASK_NAME=SincronizacionBiometrica_5min

echo Verificando si el archivo EXE existe...
if not exist "%EXE_PATH%" (
    echo ERROR: No se encuentra el archivo EXE en:
    echo %EXE_PATH%
    echo.
    echo Por favor, compila primero el script usando:
    echo pyinstaller --onefile --console sincronizar_biometrico_service.py --name SincronizacionBiometricaService
    echo.
    pause
    exit /b 1
)

echo Archivo EXE encontrado: %EXE_PATH%
echo.

echo Verificando archivo de configuracion...
if not exist "%~dp0biometrico_config.json" (
    echo ADVERTENCIA: No se encuentra el archivo de configuracion biometrico_config.json
    echo Se creara uno con valores por defecto.
    echo Recuerda editarlo con la IP correcta de tu dispositivo.
    echo.
)

echo Eliminando tarea existente si existe...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

echo Creando nueva tarea programada...
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%EXE_PATH%\"" ^
    /sc minute ^
    /mo 5 ^
    /st 00:00 ^
    /ru "SYSTEM" ^
    /rl HIGHEST ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo TAREA CREADA EXITOSAMENTE
    echo ========================================
    echo.
    echo Nombre de la tarea: %TASK_NAME%
    echo Frecuencia: Cada 5 minutos
    echo Usuario: SYSTEM ^(en segundo plano^)
    echo Archivo: %EXE_PATH%
    echo.
    echo ARCHIVOS DE LOG:
    echo - biometrico_sync_service.log: Logs del servicio
    echo - biometrico_config.json: Archivo de configuracion
    echo.
    echo La tarea ya esta activa y se ejecutara automaticamente.
    echo.
    echo Para gestionar la tarea:
    echo - Abrir: taskschd.msc
    echo - O usar: schtasks /query /tn "%TASK_NAME%"
    echo.
    echo Para detener la tarea:
    echo - schtasks /end /tn "%TASK_NAME%"
    echo.
    echo Para eliminar la tarea:
    echo - schtasks /delete /tn "%TASK_NAME%" /f
    echo.
    echo IMPORTANTE: Edita biometrico_config.json con la IP correcta de tu dispositivo
    echo.
) else (
    echo.
    echo ERROR: No se pudo crear la tarea programada.
    echo Asegurate de ejecutar este script como Administrador.
    echo.
)

pause
