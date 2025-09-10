#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para funcionalidad de startup
"""

import os
import sys
import subprocess
import tempfile

def test_registry_method():
    """Prueba el método del registro"""
    print("=== PROBANDO MÉTODO DEL REGISTRO ===")
    
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SincronizadorBiometrico"
        
        # Obtener la ruta del ejecutable actual
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
        else:
            python_exe = sys.executable
            script_path = os.path.abspath(__file__)
            app_path = f'"{python_exe}" "{script_path}"'
        
        print(f"Ruta de aplicación: {app_path}")
        
        # Intentar leer el valor actual
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            print(f"Valor actual en registro: {value}")
            return True
        except FileNotFoundError:
            print("No hay entrada en el registro")
            return False
        except Exception as e:
            print(f"Error leyendo registro: {e}")
            return False
            
    except ImportError:
        print("ERROR: winreg no disponible")
        return False

def create_registry_entry():
    """Crea una entrada en el registro"""
    print("=== CREANDO ENTRADA EN EL REGISTRO ===")
    
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SincronizadorBiometrico"
        
        # Obtener la ruta del ejecutable actual
        if getattr(sys, 'frozen', False):
            app_path = f'"{sys.executable}" --autostart'
        else:
            python_exe = sys.executable
            script_path = os.path.abspath(__file__.replace('test_startup_simple.py', 'sincronizador_biometrico_mejorado.py'))
            app_path = f'"{python_exe}" "{script_path}" --autostart'
        
        print(f"Creando entrada: {app_name} = {app_path}")
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(key)
        
        print("✅ Entrada creada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando entrada: {e}")
        return False

def delete_registry_entry():
    """Elimina la entrada del registro"""
    print("=== ELIMINANDO ENTRADA DEL REGISTRO ===")
    
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SincronizadorBiometrico"
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        try:
            winreg.DeleteValue(key, app_name)
            print("✅ Entrada eliminada exitosamente")
            result = True
        except FileNotFoundError:
            print("ℹ️ La entrada ya no existía")
            result = True
        finally:
            winreg.CloseKey(key)
        return result
        
    except Exception as e:
        print(f"❌ Error eliminando entrada: {e}")
        return False

def test_schtasks_method():
    """Prueba el método de schtasks"""
    print("=== PROBANDO MÉTODO DE SCHTASKS ===")
    
    task_name = "SincronizadorBiometricoTest"
    
    # Eliminar tarea si existe
    result = subprocess.run([
        'schtasks', '/delete', '/tn', task_name, '/f'
    ], capture_output=True, text=True, shell=True)
    
    print(f"Eliminación previa: código {result.returncode}")
    
    # Crear tarea simple
    working_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.abspath(__file__.replace('test_startup_simple.py', 'sincronizador_biometrico_mejorado.py'))
    
    # Intentar crear tarea simple primero
    cmd = [
        'schtasks', '/create',
        '/tn', task_name,
        '/tr', f'"{sys.executable}" "{script_path}" --autostart',
        '/sc', 'onstart',
        '/f'
    ]
    
    print(f"Comando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    
    print(f"Código de salida: {result.returncode}")
    if result.stdout:
        print(f"Salida: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    
    if result.returncode == 0:
        print("✅ Tarea creada exitosamente")
        
        # Verificar que existe
        check_result = subprocess.run([
            'schtasks', '/query', '/tn', task_name
        ], capture_output=True, text=True, shell=True)
        
        if check_result.returncode == 0:
            print("✅ Tarea verificada exitosamente")
        else:
            print("❌ Tarea no se puede verificar")
        
        # Limpiar
        subprocess.run([
            'schtasks', '/delete', '/tn', task_name, '/f'
        ], capture_output=True, shell=True)
        
        return True
    else:
        print("❌ Error creando tarea")
        return False

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO DE FUNCIONALIDAD DE STARTUP")
    print("=" * 50)
    
    # Probar estado inicial
    initial_state = test_registry_method()
    print(f"Estado inicial del registro: {initial_state}")
    print()
    
    # Probar crear entrada
    create_success = create_registry_entry()
    print()
    
    # Verificar que se creó
    if create_success:
        verify_state = test_registry_method()
        print(f"Estado después de crear: {verify_state}")
        print()
    
    # Probar schtasks
    schtasks_success = test_schtasks_method()
    print()
    
    # Limpiar
    delete_success = delete_registry_entry()
    print()
    
    # Estado final
    final_state = test_registry_method()
    print(f"Estado final: {final_state}")
    
    print("\n" + "=" * 50)
    print("RESUMEN:")
    print(f"✅ Registro funciona: {create_success and delete_success}")
    print(f"✅ Schtasks funciona: {schtasks_success}")
