# Sincronizador Biométrico - Ejecutables

## Archivos Incluidos

### SincronizadorBiometrico.exe
- **Propósito**: Aplicación principal con interfaz gráfica
- **Uso**: Doble clic para ejecutar
- **Características**: Interfaz completa, configuración, sincronización automática

### StartupManager.exe  
- **Propósito**: Gestor de inicio automático con Windows
- **Uso**: Desde línea de comandos
- **Comandos**:
  - `StartupManager.exe --enable` - Habilitar inicio automático
  - `StartupManager.exe --disable` - Deshabilitar inicio automático
  - `StartupManager.exe --status` - Ver estado actual
  - `StartupManager.exe --test` - Probar funcionalidad

### InstaladorSincronizadorBiometrico.exe
- **Propósito**: Instalador completo del sistema
- **Uso**: Para distribución e instalación en nuevos equipos
- **Características**: Instala dependencias, configura startup, crea accesos directos

## Instalación y Uso

1. **Uso directo**: Simplemente ejecutar `SincronizadorBiometrico.exe`
2. **Instalación completa**: Ejecutar `InstaladorSincronizadorBiometrico.exe`
3. **Configurar startup**: Usar `StartupManager.exe --enable`

## Notas Técnicas

- Los ejecutables son autocontenidos (no requieren Python instalado)
- Se recomienda crear una carpeta dedicada para todos los archivos
- Los logs se crean en la carpeta `logs/` relativa al ejecutable
- La configuración se guarda en archivos JSON en el mismo directorio

## Solución de Problemas

- Si hay problemas de permisos, ejecutar como administrador
- Para inicio automático, verificar que no esté bloqueado por antivirus
- Los logs contienen información detallada para diagnóstico
