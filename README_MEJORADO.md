# Sincronizador Biométrico Mejorado

Una aplicación de escritorio avanzada para sincronizar datos de dispositivos biométricos con servidores remotos, con capacidad de ejecución en segundo plano y pruebas de conexión exhaustivas.

## 🚀 Características Principales

### ✅ Mejoras Implementadas

- **Interfaz gráfica mejorada** con configuración completa
- **Pruebas de conexión avanzadas** (ping, TCP, dispositivo completo)
- **Ejecución automática cada 5 minutos** (configurable)
- **Minimización a bandeja del sistema** para ejecución en segundo plano
- **Sistema de logs robusto** con rotación automática
- **Configuración persistente** con import/export
- **Validación de conexión** antes de cada sincronización
- **Prevención de múltiples instancias**
- **Auto-inicio opcional** al abrir la aplicación

### 🔧 Funcionalidades de Pruebas

1. **Prueba de Ping**: Verifica conectividad básica de red
2. **Prueba de Puerto TCP**: Confirma que el puerto del dispositivo está accesible
3. **Prueba Completa**: Conecta al dispositivo y obtiene información detallada
4. **Ejecución Manual**: Ejecuta un ciclo completo de sincronización
5. **Sincronización Automática**: Ejecuta cada X minutos en segundo plano

### 🖥️ Interfaz de Usuario

- **Configuración**: IP, puerto, nombre de estación, intervalo, URL del servidor
- **Opciones**: Auto-inicio, minimizar a bandeja
- **Botones de Prueba**: Ping, TCP, prueba completa
- **Control**: Ejecutar ahora, iniciar/detener automático, ocultar
- **Log en Tiempo Real**: Visualización de todas las operaciones
- **Exportar/Importar**: Configuración y logs

## 📋 Requisitos del Sistema

- **Sistema Operativo**: Windows 10/11
- **Python**: 3.8 o superior
- **Bibliotecas**: Ver `requirements.txt`
- **Hardware**: Mínimo 4GB RAM, 100MB espacio en disco

## 🛠️ Instalación y Configuración

### Opción 1: Ejecutar desde Código Fuente

1. **Clonar o descargar** el repositorio
2. **Ejecutar** `ejecutar_mejorado.bat`
   - Creará automáticamente el entorno virtual
   - Instalará todas las dependencias
   - Iniciará la aplicación

### Opción 2: Compilar Ejecutable

1. **Ejecutar** `compilar_mejorado.bat`
   - Compilará la aplicación en un ejecutable único
   - Creará el directorio `dist/` con todos los archivos necesarios
2. **Ejecutar** `dist/SincronizadorBiometricoMejorado.exe`

### Configuración Inicial

1. **Abrir la aplicación**
2. **Configurar los parámetros**:
   - IP del dispositivo biométrico
   - Puerto (por defecto 4370)
   - Nombre de la estación
   - Intervalo de sincronización (minutos)
   - URL del servidor de destino
3. **Probar la conexión** usando los botones de prueba
4. **Guardar la configuración**

## 🔍 Guía de Uso

### Configuración de Parámetros

#### Parámetros Básicos
- **IP del Dispositivo**: Dirección IP del dispositivo biométrico (ej: 192.168.1.88)
- **Puerto**: Puerto de comunicación (típicamente 4370)
- **Nombre de la Estación**: Identificador único para los registros
- **Intervalo**: Tiempo entre sincronizaciones automáticas (en minutos)

#### Parámetros Avanzados
- **URL del Servidor**: Endpoint donde se envían los datos sincronizados
- **Auto-inicio**: Iniciar sincronización automáticamente al abrir la app
- **Minimizar a Bandeja**: Permitir ocultar la aplicación en la bandeja del sistema

### Flujo de Trabajo Recomendado

1. **Configurar parámetros** de conexión
2. **Ejecutar "Prueba Completa"** para verificar conectividad
3. **Hacer una "Ejecución Manual"** para probar el ciclo completo
4. **Iniciar "Sincronización Automática"**
5. **"Ocultar en Segundo Plano"** para ejecución continua

### Pruebas de Conexión

#### 🏓 Prueba de Ping
- Verifica conectividad básica de red
- Muestra tiempo de respuesta
- Útil para diagnosticar problemas de red

#### 🔌 Prueba de Puerto TCP
- Confirma que el puerto del dispositivo está abierto
- Verifica que no hay firewalls bloqueando
- Muestra tiempo de conexión

#### 📱 Prueba Completa
- Conecta al dispositivo biométrico
- Obtiene información del firmware
- Cuenta usuarios y registros disponibles
- Prueba más completa antes de sincronización

### Ejecución en Segundo Plano

1. **Configurar** todos los parámetros necesarios
2. **Iniciar sincronización automática**
3. **Hacer clic en "Ocultar en Segundo Plano"**
4. La aplicación se minimizará a la **bandeja del sistema**
5. **Hacer clic derecho** en el icono de la bandeja para acceder al menú

#### Menú de Bandeja del Sistema
- **Mostrar**: Restaurar la ventana principal
- **Ocultar**: Minimizar a la bandeja
- **Iniciar Sync**: Iniciar sincronización automática
- **Detener Sync**: Detener sincronización automática
- **Salir**: Cerrar completamente la aplicación

## 📊 Sistema de Logs

### Ubicación de Logs
- **Interfaz**: Log en tiempo real en la aplicación
- **Archivos**: Carpeta `logs/biometrico_sync.log`
- **Rotación**: Automática cuando el archivo supera 5MB
- **Historial**: Se mantienen 5 archivos de backup

### Niveles de Log
- **INFO**: Operaciones normales y estado
- **WARNING**: Situaciones que no impiden la operación
- **ERROR**: Errores que impiden la sincronización
- **DEBUG**: Información detallada para diagnóstico

### Funciones de Log
- **Limpiar Log**: Borra el log de la interfaz
- **Exportar Log**: Guarda el log actual en un archivo
- **Abrir Carpeta Logs**: Abre la carpeta con todos los archivos de log

## ⚙️ Configuración Avanzada

### Archivo de Configuración

La configuración se guarda en `biometrico_config.json`:

```json
{
  "SERVER_URL": "http://186.31.35.24:8000/api/recibir-datos-biometrico/",
  "TOKEN_API": null,
  "IP_BIOMETRICO": "192.168.1.88",
  "PUERTO_BIOMETRICO": 4370,
  "NOMBRE_ESTACION": "Centenario",
  "INTERVALO_MINUTOS": 5,
  "AUTO_START": false,
  "MINIMIZE_TO_TRAY": true
}
```

### Import/Export de Configuración
- **Exportar**: Guarda la configuración actual en un archivo JSON
- **Importar**: Carga configuración desde un archivo JSON
- Útil para **distribuir configuraciones** o **hacer respaldos**

### Parámetros de Red
- **Timeout de Conexión**: 30 segundos por defecto
- **Reintentos**: 4 configuraciones diferentes de conexión
- **Timeout de Envío**: 30 segundos para envío al servidor

## 🚨 Solución de Problemas

### Problemas Comunes

#### "No se pudo conectar al dispositivo"
1. Verificar que la **IP es correcta**
2. Verificar que el **dispositivo está encendido**
3. Ejecutar **"Prueba de Ping"**
4. Ejecutar **"Prueba de Puerto TCP"**
5. Verificar configuración de **firewall**

#### "Timeout obteniendo registros"
1. El dispositivo puede estar **ocupado**
2. **Reiniciar el dispositivo** biométrico
3. Verificar **estabilidad de la red**
4. Aumentar el timeout en el código si es necesario

#### "Error al enviar datos al servidor"
1. Verificar **conectividad a Internet**
2. Verificar que la **URL del servidor es correcta**
3. Verificar **configuración del firewall corporativo**
4. Revisar **logs del servidor** si es posible

#### "Aplicación ya ejecutándose"
1. Buscar el **icono en la bandeja del sistema**
2. **Terminar el proceso** desde el Administrador de Tareas
3. **Reiniciar la aplicación**

### Logs de Diagnóstico

Para obtener información detallada:
1. **Ejecutar "Prueba Completa"**
2. **Revisar logs** en la interfaz
3. **Exportar logs** para enviar a soporte
4. **Abrir carpeta de logs** para ver archivos históricos

### Configuración de Red

#### Firewall de Windows
- Permitir la aplicación en el **Firewall de Windows**
- Abrir el **puerto del dispositivo** (típicamente 4370)

#### Red Corporativa
- Verificar que no hay **proxy bloqueando**
- Configurar **excepciones de firewall corporativo**
- Verificar **políticas de seguridad de red**

## 📈 Monitoreo y Mantenimiento

### Monitoreo Continuo
- **Revisar logs periódicamente** para detectar errores
- **Verificar que la sincronización** está ejecutándose
- **Comprobar espacio en disco** para logs

### Mantenimiento
- **Limpiar logs antiguos** si es necesario
- **Actualizar configuración** cuando cambien IPs
- **Respaldar configuración** antes de cambios importantes

### Indicadores de Estado
- **Estado en la interfaz**: Muestra si está ejecutándose
- **Logs en tiempo real**: Muestran progreso de operaciones
- **Icono de bandeja**: Permite control rápido

## 🔄 Actualizaciones y Mejoras

### Versión Actual: v2.0 Mejorada

#### Nuevas Características
- Interfaz gráfica rediseñada
- Sistema de pruebas de conexión
- Bandeja del sistema
- Configuración persistente
- Logs mejorados
- Validación de entrada

#### Mejoras de Rendimiento
- Mejor manejo de timeouts
- Reconexión automática
- Gestión de memoria optimizada
- Prevención de múltiples instancias

### Roadmap Futuro
- [ ] Notificaciones push
- [ ] Dashboard web
- [ ] Múltiples dispositivos
- [ ] Configuración remota
- [ ] Estadísticas avanzadas

---

## 📞 Soporte

Para soporte técnico:
1. **Revisar** esta documentación
2. **Exportar logs** de la aplicación
3. **Documentar** el problema específico
4. **Incluir** configuración utilizada
5. **Contactar** al equipo de desarrollo

---

*Sincronizador Biométrico Mejorado v2.0 - Desarrollado para entornos corporativos con alta disponibilidad*
