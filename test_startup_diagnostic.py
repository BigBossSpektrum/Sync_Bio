#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico específico para la funcionalidad de inicio automático con Windows
"""

import os
import sys
import subprocess
import winreg
import json
from datetime import datetime

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar funciones del módulo principal
try:
    from sincronizador_biometrico_mejorado import (
        is_startup_enabled, enable_startup, disable_startup,
        is_startup_enabled_registry, enable_startup_registry, disable_startup_registry
    )
    print("✅ Módulos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

def check_registry_startup():
    """Verificar estado del registro de Windows"""
    print("\n🔍 VERIFICANDO REGISTRO DE WINDOWS")
    print("-" * 50)
    
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SincronizadorBiometrico"
        
        print(f"📋 Clave del registro: HKEY_CURRENT_USER\\{key_path}")
        print(f"📋 Nombre de aplicación: {app_name}")
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            
            # Listar todas las entradas
            print("\n📝 Entradas existentes en el registro:")
            i = 0
            while True:
                try:
                    name, value, type_ = winreg.EnumValue(key, i)
                    print(f"  {i+1}. {name} = {value}")
                    i += 1
                except OSError:
                    break
            
            # Verificar entrada específica
            try:
                value, reg_type = winreg.QueryValueEx(key, app_name)
                print(f"\n✅ Entrada encontrada: {app_name} = {value}")
                return True
            except FileNotFoundError:
                print(f"\n❌ No se encontró entrada para: {app_name}")
                return False
            finally:
                winreg.CloseKey(key)
                
        except Exception as e:
            print(f"❌ Error accediendo al registro: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error general en registro: {e}")
        return False

def check_scheduled_task():
    """Verificar tareas programadas"""
    print("\n🔍 VERIFICANDO TAREAS PROGRAMADAS")
    print("-" * 50)
    
    task_name = "SincronizadorBiometrico"
    print(f"📋 Nombre de tarea: {task_name}")
    
    try:
        # Verificar si la tarea existe
        result = subprocess.run([
            'schtasks', '/query', '/tn', task_name
        ], capture_output=True, text=True, shell=True)
        
        print(f"📊 Código de salida: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Tarea programada encontrada")
            print(f"📝 Salida:\n{result.stdout}")
            
            # Obtener detalles en formato CSV
            result_csv = subprocess.run([
                'schtasks', '/query', '/tn', task_name, '/fo', 'csv'
            ], capture_output=True, text=True, shell=True)
            
            if result_csv.returncode == 0:
                print("\n📊 Detalles en formato CSV:")
                lines = result_csv.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    print(f"  Línea {i+1}: {line}")
                
                if len(lines) >= 2:
                    data = lines[1].split(',')
                    if len(data) >= 4:
                        status = data[3].strip('"')
                        print(f"\n📈 Estado de la tarea: {status}")
                        return status.lower() in ['ready', 'running']
            
            return True
        else:
            print("❌ Tarea programada no encontrada")
            if result.stderr:
                print(f"📝 Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando tarea programada: {e}")
        return False

def test_enable_disable_cycle():
    """Test completo de habilitar/deshabilitar"""
    print("\n🔍 TEST DE CICLO HABILITAR/DESHABILITAR")
    print("-" * 50)
    
    # Estado inicial
    initial_state = is_startup_enabled()
    print(f"📋 Estado inicial: {initial_state}")
    
    # Test 1: Habilitar
    print("\n🔄 Test 1: Habilitando inicio automático...")
    enable_result = enable_startup()
    print(f"📊 Resultado enable_startup(): {enable_result}")
    
    # Verificar después de habilitar
    after_enable_registry = is_startup_enabled_registry()
    after_enable_task = check_scheduled_task()
    after_enable_general = is_startup_enabled()
    
    print(f"📊 Estado después de habilitar:")
    print(f"  - Registro: {after_enable_registry}")
    print(f"  - Tarea programada: {after_enable_task}")
    print(f"  - General (is_startup_enabled): {after_enable_general}")
    
    # Test 2: Deshabilitar
    print("\n🔄 Test 2: Deshabilitando inicio automático...")
    disable_result = disable_startup()
    print(f"📊 Resultado disable_startup(): {disable_result}")
    
    # Verificar después de deshabilitar
    after_disable_registry = is_startup_enabled_registry()
    after_disable_task = check_scheduled_task()
    after_disable_general = is_startup_enabled()
    
    print(f"📊 Estado después de deshabilitar:")
    print(f"  - Registro: {after_disable_registry}")
    print(f"  - Tarea programada: {after_disable_task}")
    print(f"  - General (is_startup_enabled): {after_disable_general}")
    
    # Restaurar estado inicial
    print(f"\n🔄 Restaurando estado inicial ({initial_state})...")
    if initial_state:
        enable_startup()
    else:
        disable_startup()
    
    final_state = is_startup_enabled()
    print(f"📊 Estado final: {final_state}")
    print(f"✅ Restauración {'exitosa' if final_state == initial_state else 'falló'}")

def analyze_enable_function():
    """Analizar la función enable_startup paso a paso"""
    print("\n🔍 ANÁLISIS DE FUNCIÓN enable_startup()")
    print("-" * 50)
    
    try:
        # Simular los pasos de enable_startup sin ejecutarlos
        task_name = "SincronizadorBiometrico"
        working_dir = os.path.dirname(os.path.abspath(__file__))
        
        print(f"📋 Nombre de tarea: {task_name}")
        print(f"📋 Directorio de trabajo: {working_dir}")
        
        if getattr(sys, 'frozen', False):
            program = sys.executable
            arguments = '--autostart'
            print(f"📋 Modo: Ejecutable compilado")
        else:
            program = sys.executable
            script_path = os.path.abspath(__file__)
            arguments = f'"{script_path}" --autostart'
            print(f"📋 Modo: Script Python")
        
        print(f"📋 Programa: {program}")
        print(f"📋 Argumentos: {arguments}")
        
        # Verificar si el programa existe
        if os.path.exists(program):
            print(f"✅ Programa existe: {program}")
        else:
            print(f"❌ Programa NO existe: {program}")
        
        # Verificar si el directorio de trabajo existe
        if os.path.exists(working_dir):
            print(f"✅ Directorio de trabajo existe: {working_dir}")
        else:
            print(f"❌ Directorio de trabajo NO existe: {working_dir}")
            
    except Exception as e:
        print(f"❌ Error en análisis: {e}")

def main():
    """Función principal de diagnóstico"""
    print("🔍 DIAGNÓSTICO DE INICIO AUTOMÁTICO CON WINDOWS")
    print("=" * 60)
    print(f"⏰ Fecha y hora: {datetime.now()}")
    print(f"💻 Sistema: {os.name}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"📄 Script actual: {__file__}")
    print(f"🔧 Ejecutable Python: {sys.executable}")
    print(f"📦 Ejecutable compilado: {getattr(sys, 'frozen', False)}")
    
    # Realizar diagnósticos
    analyze_enable_function()
    registry_status = check_registry_startup()
    task_status = check_scheduled_task()
    
    print(f"\n📊 RESUMEN INICIAL:")
    print(f"  - Registro: {registry_status}")
    print(f"  - Tarea programada: {task_status}")
    print(f"  - is_startup_enabled(): {is_startup_enabled()}")
    
    # Test completo
    test_enable_disable_cycle()
    
    print("\n🏁 Diagnóstico completado!")

if __name__ == "__main__":
    main()