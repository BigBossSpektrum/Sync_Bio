# Sistema de Persistencia de Configuración - Sincronizador Biométrico

## Resumen de Mejoras Implementadas

El sistema de sincronización biométrica ahora conserva completamente la configuración tras reiniciar Windows, incluyendo:

### 🔧 Configuraciones Persistentes

1. **Sincronización Automática (`AUTO_START`)**: Mantiene habilitado/deshabilitado
2. **Inicio con Windows (`START_WITH_WINDOWS`)**: Conserva configuración de arranque automático
3. **Minimizar a Bandeja (`MINIMIZE_TO_TRAY`)**: Mantiene comportamiento de segundo plano
4. **Parámetros de Conexión**: IP, puerto, servidor, intervalo, etc.

### 📁 Ubicaciones de Configuración (En orden de prioridad)

1. **Directorio actual**: `./biometrico_config.json`
2. **Directorio de la aplicación**: `[ruta_app]/biometrico_config.json`
3. **AppData del usuario**: `%LOCALAPPDATA%\SyncBio\biometrico_config.json`

### ⚡ Guardado Automático

- **Al cambiar configuración**: Inmediato
- **Periódico**: Cada 5 minutos (automático)
- **Al cerrar aplicación**: Antes de salir
- **Al cerrar ventana**: Antes de minimizar/cerrar

### 🚀 Comportamiento de Inicio

Cuando se inicia con Windows (`--autostart`):
- ✅ Carga configuración automáticamente
- ✅ Inicia sincronización si `AUTO_START = true`
- ✅ Se minimiza a bandeja si `MINIMIZE_TO_TRAY = true`
- ✅ Funciona silenciosamente en segundo plano

### 📦 Archivos Ejecutables Generados

1. **SincronizadorBiometrico.exe** (22.6 MB)
   - Aplicación principal con interfaz gráfica
   - Gestión completa de configuración
   - Sistema de bandeja integrado

2. **StartupManager.exe** (22.6 MB)
   - Gestión de inicio automático con Windows
   - Comandos: `--enable`, `--disable`, `--status`, `--test`

### 🔄 Ciclo de Persistencia

```
INICIO → Cargar Config → Ejecutar App → Guardar Periódico → CIERRE → Guardar Final
```

### ✅ Pruebas de Persistencia

Para verificar que todo funciona:

1. **Configurar aplicación**:
   - Habilitar sincronización automática
   - Habilitar inicio con Windows
   - Configurar parámetros de conexión

2. **Reiniciar Windows**

3. **Verificar**:
   - Aplicación inicia automáticamente
   - Configuración se mantiene intacta
   - Sincronización arranca sola (si estaba habilitada)
   - Aplicación funciona en segundo plano

### 🛠️ Comandos Útiles

```bash
# Habilitar inicio con Windows
StartupManager.exe --enable

# Verificar estado de inicio
StartupManager.exe --status

# Deshabilitar inicio con Windows
StartupManager.exe --disable

# Ejecutar aplicación principal
SincronizadorBiometrico.exe
```

### 🔒 Robustez del Sistema

- **Múltiples ubicaciones de respaldo** para el archivo de configuración
- **Validación automática** del estado de inicio con Windows
- **Guardado redundante** (periódico + al cerrar)
- **Manejo de errores** sin pérdida de configuración
- **Detección automática** de rutas de ejecutables

## Resultado Final

✅ **La configuración se conserva completamente al reiniciar Windows**
✅ **La aplicación funciona en segundo plano como se configuró**
✅ **La sincronización automática se mantiene habilitada/deshabilitada**
✅ **Todo el comportamiento es persistente y robusto**
