# Instrucciones para Configurar Sincronización Automática cada 5 minutos

## Paso 1: Compilar el archivo EXE

1. Abre una terminal como **Administrador** en la carpeta del proyecto
2. Ejecuta el archivo de compilación:
   ```
   compilar_exe.bat
   ```
3. Espera a que termine la compilación
4. Verifica que se creó el archivo: `dist\SincronizacionBiometrica.exe`

## Paso 2: Probar el ejecutable manualmente

1. Ejecuta el archivo `dist\SincronizacionBiometrica.exe`
2. Configura los datos:
   - **IP del Dispositivo**: (ej: 192.168.1.88)
   - **Puerto**: 4370 (por defecto)
   - **Nombre de la Estación**: (ej: Centenario)
3. Usa **"Probar Conexión"** para verificar que funciona
4. Usa **"Ejecutar Ahora"** para probar una sincronización manual
5. Si todo funciona bien, continúa al paso 3

## Paso 3: Crear la tarea programada (AUTOMÁTICO)

### Opción A: Script automático (Recomendado)

1. **IMPORTANTE**: Cierra la aplicación si está abierta
2. Ejecuta como **Administrador** el archivo:
   ```
   crear_tarea_programada.bat
   ```
3. El script creará automáticamente la tarea para ejecutarse cada 5 minutos
4. La sincronización comenzará inmediatamente en segundo plano

### Opción B: Configuración manual

Si el script automático no funciona, sigue estos pasos:

1. Abre **Programador de tareas** (taskschd.msc)
2. Clic derecho en "Biblioteca del Programador de tareas" → "Crear tarea..."

#### Pestaña General:
- **Nombre**: SincronizacionBiometrica_5min
- **Descripción**: Sincronización automática del dispositivo biométrico cada 5 minutos
- Marcar: "Ejecutar tanto si el usuario ha iniciado sesión como si no"
- Marcar: "Ejecutar con los privilegios más altos"
- **Configurar para**: Windows 10/11

#### Pestaña Desencadenadores:
- Clic "Nuevo..."
- **Iniciar la tarea**: Al programar
- **Configuración**: Diariamente
- **Repetir la tarea cada**: 5 minutos
- **Durante**: Indefinidamente
- **Habilitar**: ✓

#### Pestaña Acciones:
- Clic "Nuevo..."
- **Acción**: Iniciar un programa
- **Programa**: Buscar y seleccionar `dist\SincronizacionBiometrica.exe`
- **Iniciar en**: Carpeta donde está el EXE

#### Pestaña Condiciones:
- Desmarcar: "Iniciar la tarea solo si el equipo está conectado a la corriente alterna"
- Desmarcar: "Detener si el equipo deja de estar conectado a la corriente alterna"

#### Pestaña Configuración:
- Marcar: "Permitir que la tarea se ejecute a petición"
- Marcar: "Si la tarea con error, reiniciar cada": 1 minuto
- **Intentar reiniciar hasta**: 3 veces

## Paso 4: Verificar que funciona

### Verificar la tarea:
```cmd
schtasks /query /tn "SincronizacionBiometrica_5min"
```

### Ver el estado:
```cmd
schtasks /query /tn "SincronizacionBiometrica_5min" /fo list /v
```

### Ejecutar manualmente la tarea:
```cmd
schtasks /run /tn "SincronizacionBiometrica_5min"
```

### Ver los logs:
- Revisar el archivo: `biometrico_sync.log`
- En el Programador de tareas: Biblioteca → SincronizacionBiometrica_5min → Historial

## Gestión de la tarea

### Detener temporalmente:
```cmd
schtasks /change /tn "SincronizacionBiometrica_5min" /disable
```

### Reactivar:
```cmd
schtasks /change /tn "SincronizacionBiometrica_5min" /enable
```

### Eliminar completamente:
```cmd
schtasks /delete /tn "SincronizacionBiometrica_5min" /f
```

## Solución de problemas

### Si la tarea no se ejecuta:
1. Verificar que el archivo EXE existe en la ruta configurada
2. Ejecutar el EXE manualmente para verificar que funciona
3. Revisar el historial de la tarea en el Programador de tareas
4. Verificar que la tarea tenga permisos de administrador

### Si la sincronización falla:
1. Revisar el archivo `biometrico_sync.log`
2. Verificar la conectividad de red al dispositivo
3. Verificar que la IP y puerto del dispositivo sean correctos
4. Verificar que el dispositivo biométrico esté encendido

### Logs importantes:
- `biometrico_sync.log`: Logs de la aplicación
- Visor de eventos de Windows: Logs del sistema
- Programador de tareas → Historial: Logs de ejecución de la tarea

## Configuración recomendada

- **Frecuencia**: Cada 5 minutos (300 segundos)
- **Usuario**: SYSTEM (para ejecución en segundo plano)
- **Privilegios**: Más altos (para acceso completo al dispositivo)
- **Reintentos**: 3 intentos con 1 minuto de espera
- **Duración**: Indefinida (24/7)

La sincronización funcionará completamente en segundo plano sin interrumpir las actividades de los usuarios.
