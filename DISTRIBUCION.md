# Instrucciones de Distribución - Sincronización Biométrica

## Archivo Ejecutable Creado
- **Nombre**: `SincronizacionBiometrica.exe`
- **Ubicación**: `dist/SincronizacionBiometrica.exe`
- **Tamaño**: ~15 MB
- **Tipo**: Ejecutable independiente (no requiere Python instalado)

## Características del Ejecutable
- ✅ **Interfaz gráfica** con tkinter
- ✅ **Autocontenido** - incluye todas las dependencias
- ✅ **Icono personalizado** incluido
- ✅ **Compatible con Windows** (compilado en Windows)
- ✅ **No requiere instalación** - ejecutable portable

## Archivos Necesarios para Distribución
Para distribuir la aplicación, solo necesitas:

1. **SincronizacionBiometrica.exe** (archivo principal)
2. **Opcional**: Crear una carpeta con documentación

## Uso del Ejecutable
1. Hacer doble clic en `SincronizacionBiometrica.exe`
2. Configurar los parámetros en la interfaz:
   - IP del dispositivo biométrico
   - Puerto (por defecto 4370)
   - Nombre de la estación
3. Hacer clic en "Iniciar Sincronización"
4. Monitorear el proceso en el log de actividades

## Archivos de Log
La aplicación creará automáticamente:
- `biometrico_sync.log` - Log detallado de todas las operaciones

## Recomendaciones para Distribución
1. **Crear una carpeta** con el nombre descriptivo (ej: "SincronizacionBiometrica_v1.0")
2. **Incluir el ejecutable** y este archivo de instrucciones
3. **Opcional**: Incluir el icono.ico para referencias futuras
4. **Comprimir en ZIP** para facilitar la distribución

## Recompilación
Si necesitas recompilar el ejecutable:
1. Ejecutar `compilar_exe.bat` 
2. O usar manualmente: `pyinstaller SincronizacionBiometrica.spec`

## Requisitos del Sistema de Destino
- **Sistema Operativo**: Windows 7 o superior
- **Arquitectura**: 64-bit
- **Red**: Acceso a la red para conectar con el dispositivo biométrico y servidor
- **Permisos**: Permisos para escribir archivos de log en la carpeta de la aplicación

## Configuración del Servidor
La aplicación está configurada para enviar datos a:
- **URL**: http://186.31.35.24:8000/api/recibir-datos-biometrico/
- **Método**: POST
- **Formato**: JSON
- **Token**: Configurable en el código fuente si es necesario

## Resolución de Problemas
Si el ejecutable no inicia:
1. Verificar que no esté bloqueado por antivirus
2. Ejecutar como administrador si es necesario
3. Verificar que el sistema sea compatible (Windows 64-bit)

Si hay problemas de conexión:
1. Verificar la IP y puerto del dispositivo biométrico
2. Comprobar conectividad de red
3. Revisar el archivo de log para detalles específicos
