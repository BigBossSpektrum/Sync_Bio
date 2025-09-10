# SincronizadorBiometricoV1.exe

## 📋 Descripción

`SincronizadorBiometricoV1.exe` es la versión compilada del sincronizador biométrico con todas las correcciones y mejoras implementadas. Este ejecutable incluye:

- ✅ **Persistencia mejorada**: Guarda automáticamente todos los cambios de configuración
- ✅ **Inicio automático**: Se ejecuta automáticamente al iniciar Windows
- ✅ **Funcionamiento en segundo plano**: Se minimiza a la bandeja del sistema
- ✅ **Logging detallado**: Registra todas las operaciones para facilitar el diagnóstico
- ✅ **Sincronización automática**: Se conecta al dispositivo biométrico y sincroniza los datos automáticamente

## 📂 Ubicación

El ejecutable se encuentra en:
```
C:\Users\Entrecables y Redes\Documents\GitHub\Sync_Bio\dist\SincronizadorBiometricoV1.exe
```

## 🚀 Uso

### Ejecutar manualmente
Para ejecutar el sincronizador manualmente:
```bash
# Desde la carpeta dist
cd "C:\Users\Entrecables y Redes\Documents\GitHub\Sync_Bio\dist"
./SincronizadorBiometricoV1.exe
```

### Ejecutar en modo autostart (silencioso)
Para probar el modo autostart:
```bash
./SincronizadorBiometricoV1.exe --autostart
```

## ⚙️ Configuración del Inicio Automático

### Usando el script de configuración:

#### Habilitar autostart:
```bash
cd "C:\Users\Entrecables y Redes\Documents\GitHub\Sync_Bio"
python configurar_autostart_v1.py enable
```

#### Verificar estado:
```bash
python configurar_autostart_v1.py status
```

#### Deshabilitar autostart:
```bash
python configurar_autostart_v1.py disable
```

## 📁 Archivos de Configuración y Logs

### Configuración
El ejecutable crea su propia configuración en:
```
C:\Users\Entrecables y Redes\Documents\GitHub\Sync_Bio\dist\biometrico_config.json
```

### Logs
Los logs se guardan en:
```
C:\Users\Entrecables y Redes\Documents\GitHub\Sync_Bio\dist\logs\biometrico_sync.log
```

## 🔧 Configuración Predeterminada

```json
{
  "SERVER_URL": "http://186.31.35.24:8000/api/recibir-datos-biometrico/",
  "TOKEN_API": null,
  "IP_BIOMETRICO": "192.168.1.88",
  "PUERTO_BIOMETRICO": 4370,
  "NOMBRE_ESTACION": "Centenario",
  "INTERVALO_MINUTOS": 5,
  "AUTO_START": true,
  "MINIMIZE_TO_TRAY": true,
  "START_WITH_WINDOWS": false
}
```

## 🎯 Comportamiento en Modo Autostart

Cuando se ejecuta con `--autostart`:

1. **Carga la configuración** automáticamente
2. **Inicia la sincronización** después de 3 segundos (si `AUTO_START` está habilitado)
3. **Se minimiza a la bandeja** después de 5 segundos (si `MINIMIZE_TO_TRAY` está habilitado)
4. **Guarda la configuración** automáticamente cada 5 minutos
5. **Registra todo** en los logs para facilitar el diagnóstico

## 📊 Información del Ejecutable

- **Tamaño**: ~20 MB
- **Versión**: 1.0.0.0
- **Descripción**: Sincronizador Biométrico V1
- **Compañía**: Entrecables y Redes
- **Incluye**: Todas las dependencias necesarias (pystray, PIL, pyzk, requests, tkinter)

## 🛡️ Características de Seguridad

- **Ejecutable auto-contenido**: No requiere instalación de Python ni dependencias
- **Configuración local**: Los datos se guardan en el directorio local
- **Logs detallados**: Facilita la auditoría y el diagnóstico
- **Inicio seguro**: Utiliza LogonTrigger en lugar de BootTrigger para mayor seguridad

## 📝 Notas Importantes

1. **Primera ejecución**: Al ejecutar por primera vez, creará la configuración y logs en su directorio
2. **Autostart configurado**: Ya está configurado para iniciarse automáticamente con Windows
3. **Persistencia**: Todos los cambios de configuración se guardan automáticamente
4. **Bandeja del sistema**: Busca el icono en la bandeja del sistema cuando esté ejecutándose

## 🔍 Diagnóstico

Para verificar que el ejecutable funciona correctamente:

1. **Ejecutar manualmente** y verificar que aparece la interfaz
2. **Revisar los logs** en `dist/logs/biometrico_sync.log`
3. **Verificar la configuración** en `dist/biometrico_config.json`
4. **Probar el autostart** con `./SincronizadorBiometricoV1.exe --autostart`

## 📞 Soporte

Si hay problemas:
1. Revisar los logs para errores específicos
2. Verificar la conectividad de red al dispositivo biométrico
3. Confirmar que la configuración es correcta
4. Ejecutar las pruebas de diagnóstico si están disponibles

---

**© 2025 Entrecables y Redes - SincronizadorBiometricoV1**
