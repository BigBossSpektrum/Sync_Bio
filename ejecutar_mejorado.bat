@echo off
echo ================================================
echo   Sincronizador Biometrico Mejorado
echo ================================================
echo.

REM Verificar si existe el entorno virtual
if not exist "env\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual 'env'
    echo.
    echo Creando entorno virtual...
    python -m venv env
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual
        echo Verifica que Python este instalado correctamente
        pause
        exit /b 1
    )
)

REM Activar entorno virtual
echo [INFO] Activando entorno virtual...
call env\Scripts\activate.bat

REM Verificar e instalar dependencias
echo [INFO] Verificando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias
    pause
    exit /b 1
)

REM Crear directorio de logs si no existe
if not exist "logs" mkdir logs

echo.
echo [INFO] Iniciando aplicacion...
echo.
echo ================================================

REM Ejecutar la aplicación
python sincronizador_biometrico_mejorado.py

echo.
echo ================================================
echo   Aplicacion finalizada
echo ================================================
pause
