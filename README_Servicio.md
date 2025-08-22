# Sincronizador Biométrico - Servicio Automático

## 📋 Descripción

Este sistema permite sincronizar automáticamente los datos de un dispositivo biométrico con un servidor, funcionando como un servicio en segundo plano que se puede configurar para iniciarse automáticamente con Windows.

## 🚀 Archivos Principales

### 1. `sync_service.py`
- **Propósito**: Script principal del servicio de sincronización
- **Características**:
  - Ejecución continua en segundo plano
  - Sincronización automática cada N minutos (configurable)
  - Logging detallado con rotación de archivos
  - Manejo robusto de errores
  - Compatible con inicio automático

### 2. `start_sync_service.bat`
- **Propósito**: Archivo principal para iniciar el servicio
- **Usos**:
  ```bash
  start_sync_service.bat           # Inicia normalmente
  start_sync_service.bat --startup # Modo startup (silencioso)
  ```

### 3. `install_startup.bat`
- **Propósito**: Instala el sincronizador en el startup de Windows
- **Función**: Configura el inicio automático cuando Windows se inicia

### 4. `uninstall_startup.bat`
- **Propósito**: Desinstala el sincronizador del startup de Windows
- **Función**: Remueve la configuración de inicio automático

## ⚙️ Configuración

### Archivo de Configuración: `biometrico_config.json`

```json
{
    "SERVER_URL": "http://186.31.35.24:8000/api/recibir-datos-biometrico/",
    "TOKEN_API": null,
    "IP_BIOMETRICO": "192.168.1.88",
    "PUERTO_BIOMETRICO": 4370,
    "NOMBRE_ESTACION": "Centenario",
    "INTERVALO_MINUTOS": 5,
    "AUTO_START": true,
    "MINIMIZE_TO_TRAY": true
}
```

### Parámetros de Configuración:

- **SERVER_URL**: URL del servidor donde enviar los datos
- **TOKEN_API**: Token de autenticación (opcional)
- **IP_BIOMETRICO**: Dirección IP del dispositivo biométrico
- **PUERTO_BIOMETRICO**: Puerto del dispositivo (típicamente 4370)
- **NOMBRE_ESTACION**: Nombre identificador de la estación
- **INTERVALO_MINUTOS**: Frecuencia de sincronización en minutos
- **AUTO_START**: Si debe iniciarse automáticamente
- **MINIMIZE_TO_TRAY**: Si debe minimizarse al system tray

## 🔧 Instalación y Uso

### Instalación Rápida

1. **Instalar en Startup de Windows**:
   ```bash
   install_startup.bat
   ```
   - Configura el sincronizador para iniciarse automáticamente
   - Crea entradas en el registro de Windows
   - Añade script en la carpeta de Startup

2. **Verificar instalación**:
   - Ve a `Configuración > Aplicaciones > Inicio`
   - Busca "SincronizadorBiometricoStartup"

### Uso Manual

1. **Iniciar el servicio normalmente**:
   ```bash
   start_sync_service.bat
   ```

2. **Iniciar en modo silencioso**:
   ```bash
   start_sync_service.bat --startup
   ```

### Desinstalación

1. **Remover del startup**:
   ```bash
   uninstall_startup.bat
   ```

## 📊 Logging y Monitoreo

### Archivos de Log

- **`sync_service.log`**: Log principal del servicio con rotación automática
- **`startup_log.txt`**: Log específico de inicio desde Windows startup
- **`instalacion_startup.log`**: Log del proceso de instalación
- **`desinstalacion_startup.log`**: Log del proceso de desinstalación

### Formato de Log

```
2024-01-15 10:30:45 | INFO | 🚀 Iniciando Sincronizador Biométrico
2024-01-15 10:30:46 | INFO | ⚙️ Configuración cargada correctamente
2024-01-15 10:30:47 | INFO | 📡 IP Biométrico: 192.168.1.88:4370
2024-01-15 10:30:48 | INFO | 🔄 Iniciando bucle de sincronización (cada 5 minutos)
```

## 🔍 Solución de Problemas

### Problemas Comunes

1. **El servicio no se inicia automáticamente**:
   - Verificar que `install_startup.bat` se ejecutó correctamente
   - Revisar el archivo `startup_log.txt`
   - Verificar permisos de la carpeta

2. **Error de conexión al biométrico**:
   - Verificar IP y puerto en `biometrico_config.json`
   - Comprobar conectividad de red
   - Revisar el log para mensajes específicos

3. **Error enviando al servidor**:
   - Verificar URL del servidor
   - Comprobar conectividad a internet
   - Verificar token de API si es requerido

### Diagnóstico

Para diagnosticar problemas:

1. **Revisar logs**:
   ```bash
   type sync_service.log
   ```

2. **Probar conexión manual**:
   ```bash
   start_sync_service.bat
   ```

3. **Verificar configuración**:
   - Abrir `biometrico_config.json`
   - Verificar todos los parámetros

## 🛡️ Características de Seguridad

- **Manejo seguro de credenciales**: Los tokens no se muestran en logs
- **Validación de entrada**: Verificación de parámetros de configuración
- **Manejo de errores**: Recuperación automática ante fallos temporales
- **Logging seguro**: Rotación automática para evitar logs excesivos

## 📋 Dependencias

### Python Packages Required:
- `requests`: Para comunicación HTTP con el servidor
- `pyzk`: Para comunicación con dispositivos biométricos ZK
- `pillow`: Para manejo de iconos (si se usa system tray)

### Instalación automática:
El script `.bat` instala automáticamente las dependencias necesarias.

## 🔄 Flujo de Funcionamiento

1. **Inicio**: El servicio se inicia automáticamente o manualmente
2. **Carga de configuración**: Lee `biometrico_config.json`
3. **Conexión al biométrico**: Establece conexión con el dispositivo
4. **Bucle de sincronización**:
   - Obtiene registros de asistencia
   - Procesa y formatea los datos
   - Envía al servidor
   - Espera el intervalo configurado
   - Repite el proceso
5. **Logging**: Registra todas las operaciones y errores

## 📞 Soporte

Para problemas o dudas:
1. Revisar los archivos de log
2. Verificar la configuración
3. Probar la conectividad manualmente
4. Consultar este README

---

**Versión**: 1.0  
**Fecha**: 2024  
**Compatibilidad**: Windows 10/11, Python 3.6+
