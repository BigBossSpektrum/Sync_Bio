#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Configurar Autostart del SincronizadorBiometricoV1.exe
=================================================================

Configura el inicio automático con Windows usando el ejecutable compilado.

Uso:
    python configurar_autostart_v1.py enable     # Habilitar autostart
    python configurar_autostart_v1.py disable    # Deshabilitar autostart
    python configurar_autostart_v1.py status     # Ver estado actual
"""

import sys
import os
import subprocess
import tempfile
import winreg
import logging

def setup_logging():
    """Configura logging básico"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def get_executable_path():
    """Obtiene la ruta del ejecutable V1"""
    # Buscar el ejecutable en varias ubicaciones posibles
    search_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "SincronizadorBiometricoV1.exe"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "SincronizadorBiometricoV1.exe"),
        os.path.join(os.getcwd(), "SincronizadorBiometricoV1.exe"),
        os.path.join(os.getcwd(), "dist", "SincronizadorBiometricoV1.exe")
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    raise FileNotFoundError("No se pudo encontrar SincronizadorBiometricoV1.exe")

def enable_startup_scheduled_task():
    """Habilita startup usando tareas programadas de Windows"""
    try:
        executable_path = get_executable_path()
        working_dir = os.path.dirname(executable_path)
        task_name = "SincronizadorBiometricoV1"
        
        logging.info(f"Configurando autostart para: {executable_path}")
        
        # Eliminar tarea existente si existe
        subprocess.run([
            'schtasks', '/delete', '/tn', task_name, '/f'
        ], capture_output=True, shell=True)
        
        # Crear XML para la tarea
        xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Sincronizador Biométrico V1 - Inicio automático</Description>
    <Author>{os.getenv('USERNAME', 'Usuario')}</Author>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT30S</Delay>
      <UserId>{os.getenv('USERDOMAIN', '')}\\{os.getenv('USERNAME', '')}</UserId>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{os.getenv('USERDOMAIN', '')}\\{os.getenv('USERNAME', '')}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{executable_path}</Command>
      <Arguments>--autostart</Arguments>
      <WorkingDirectory>{working_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
        
        # Escribir archivo XML temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-16') as f:
            f.write(xml_content)
            xml_file = f.name
        
        try:
            # Crear la tarea
            cmd = ['schtasks', '/create', '/tn', task_name, '/xml', xml_file, '/f']
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                logging.info("✅ Tarea programada creada exitosamente")
                return True
            else:
                logging.error(f"❌ Error creando tarea: {result.stderr}")
                return enable_startup_registry()
                
        finally:
            # Limpiar archivo XML temporal
            try:
                os.unlink(xml_file)
            except:
                pass
                
    except Exception as e:
        logging.error(f"❌ Error configurando tarea programada: {e}")
        return enable_startup_registry()

def enable_startup_registry():
    """Habilita startup usando el registro de Windows"""
    try:
        executable_path = get_executable_path()
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SincronizadorBiometricoV1"
        app_command = f'"{executable_path}" --autostart'
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_command)
        winreg.CloseKey(key)
        
        logging.info("✅ Entrada de registro creada exitosamente")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error configurando registro: {e}")
        return False

def disable_startup():
    """Deshabilita el startup de ambas maneras"""
    task_name = "SincronizadorBiometricoV1"
    app_name = "SincronizadorBiometricoV1"
    success = False
    
    # Eliminar tarea programada
    try:
        result = subprocess.run([
            'schtasks', '/delete', '/tn', task_name, '/f'
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            logging.info("✅ Tarea programada eliminada")
            success = True
    except Exception as e:
        logging.warning(f"⚠️  No se pudo eliminar tarea programada: {e}")
    
    # Eliminar entrada del registro
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        try:
            winreg.DeleteValue(key, app_name)
            logging.info("✅ Entrada de registro eliminada")
            success = True
        except FileNotFoundError:
            logging.info("ℹ️  No había entrada de registro")
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        logging.warning(f"⚠️  Error eliminando registro: {e}")
    
    return success

def check_startup_status():
    """Verifica el estado del startup"""
    task_name = "SincronizadorBiometricoV1"
    app_name = "SincronizadorBiometricoV1"
    
    # Verificar tarea programada
    task_exists = False
    try:
        result = subprocess.run([
            'schtasks', '/query', '/tn', task_name
        ], capture_output=True, text=True, shell=True)
        task_exists = result.returncode == 0
    except:
        pass
    
    # Verificar registro
    registry_exists = False
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, app_name)
            registry_exists = bool(value and len(value.strip()) > 0)
        except FileNotFoundError:
            pass
        finally:
            winreg.CloseKey(key)
    except:
        pass
    
    return task_exists, registry_exists

def main():
    setup_logging()
    
    if len(sys.argv) != 2:
        print("Uso: python configurar_autostart_v1.py [enable|disable|status]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    try:
        if action == "enable":
            print("🔧 Habilitando inicio automático para SincronizadorBiometricoV1...")
            executable_path = get_executable_path()
            print(f"📂 Ejecutable encontrado: {executable_path}")
            
            success = enable_startup_scheduled_task()
            if success:
                print("✅ Inicio automático HABILITADO exitosamente")
                print("🚀 SincronizadorBiometricoV1 se iniciará automáticamente con Windows")
            else:
                print("❌ Error habilitando el inicio automático")
                sys.exit(1)
                
        elif action == "disable":
            print("🔧 Deshabilitando inicio automático...")
            success = disable_startup()
            if success:
                print("✅ Inicio automático DESHABILITADO exitosamente")
            else:
                print("⚠️  Problema deshabilitando el inicio automático")
                sys.exit(1)
                
        elif action == "status":
            print("🔍 Verificando estado del inicio automático...")
            try:
                executable_path = get_executable_path()
                print(f"📂 Ejecutable: {executable_path}")
            except FileNotFoundError as e:
                print(f"❌ Error: {e}")
                sys.exit(1)
            
            task_exists, registry_exists = check_startup_status()
            
            print("\n📊 Estado del inicio automático:")
            print(f"  - Tarea programada: {'✅ ACTIVA' if task_exists else '❌ INACTIVA'}")
            print(f"  - Entrada de registro: {'✅ ACTIVA' if registry_exists else '❌ INACTIVA'}")
            
            if task_exists or registry_exists:
                print("\n🎉 El inicio automático está HABILITADO")
            else:
                print("\n⚠️  El inicio automático está DESHABILITADO")
        else:
            print("❌ Acción no válida. Usa: enable, disable, o status")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
