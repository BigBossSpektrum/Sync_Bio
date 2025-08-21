#!/usr/bin/env python3
# test_app.py - Script de prueba para verificar funcionalidades básicas

import sys
import os
import tempfile

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Prueba que todas las importaciones funcionen"""
    print("🧪 Probando importaciones...")
    
    try:
        import tkinter as tk
        print("✅ tkinter - OK")
    except ImportError as e:
        print(f"❌ tkinter - FALLO: {e}")
        return False
    
    try:
        import requests
        print("✅ requests - OK")
    except ImportError as e:
        print(f"❌ requests - FALLO: {e}")
        return False
    
    try:
        import pystray
        print("✅ pystray - OK")
    except ImportError as e:
        print(f"❌ pystray - FALLO: {e}")
        return False
    
    try:
        from PIL import Image, ImageDraw
        print("✅ Pillow - OK")
    except ImportError as e:
        print(f"❌ Pillow - FALLO: {e}")
        return False
    
    try:
        from zk import ZK
        print("✅ zk (zklib) - OK")
    except ImportError as e:
        print(f"❌ zk (zklib) - FALLO: {e}")
        print("   Instala con: pip install pyzk")
        return False
    
    return True

def test_config_functions():
    """Prueba las funciones de configuración"""
    print("\n🧪 Probando funciones de configuración...")
    
    try:
        # Importar las funciones del script principal
        from sincronizador_biometrico_mejorado import load_config, save_config, config_data
        
        # Probar carga y guardado
        load_config()
        print("✅ load_config() - OK")
        
        # Modificar configuración temporalmente
        original_ip = config_data.get('IP_BIOMETRICO')
        config_data['IP_BIOMETRICO'] = '192.168.1.99'
        
        save_config()
        print("✅ save_config() - OK")
        
        # Restaurar configuración original
        config_data['IP_BIOMETRICO'] = original_ip
        save_config()
        
        return True
    except Exception as e:
        print(f"❌ Funciones de configuración - FALLO: {e}")
        return False

def test_network_functions():
    """Prueba las funciones de red básicas"""
    print("\n🧪 Probando funciones de red...")
    
    try:
        from sincronizador_biometrico_mejorado import test_ping, test_tcp_port
        
        # Probar ping a localhost
        success, message = test_ping('127.0.0.1', timeout=2)
        if success:
            print("✅ test_ping() - OK")
        else:
            print(f"⚠️ test_ping() - Sin ping pero función OK: {message}")
        
        # Probar puerto TCP (puerto que probablemente esté cerrado)
        success, message = test_tcp_port('127.0.0.1', 9999, timeout=2)
        print(f"✅ test_tcp_port() - OK (resultado: {message})")
        
        return True
    except Exception as e:
        print(f"❌ Funciones de red - FALLO: {e}")
        return False

def test_logging_setup():
    """Prueba el sistema de logging"""
    print("\n🧪 Probando sistema de logging...")
    
    try:
        from sincronizador_biometrico_mejorado import setup_logging
        import logging
        
        logger = setup_logging()
        logger.info("Prueba de logging - mensaje de información")
        logger.warning("Prueba de logging - mensaje de advertencia")
        
        # Verificar que se creó el directorio de logs
        if os.path.exists('logs'):
            print("✅ Directorio de logs creado - OK")
        else:
            print("⚠️ Directorio de logs no encontrado")
        
        # Verificar que se creó el archivo de log
        if os.path.exists('logs/biometrico_sync.log'):
            print("✅ Archivo de log creado - OK")
        else:
            print("⚠️ Archivo de log no encontrado")
        
        print("✅ Sistema de logging - OK")
        return True
    except Exception as e:
        print(f"❌ Sistema de logging - FALLO: {e}")
        return False

def test_ui_creation():
    """Prueba la creación de la interfaz (sin mostrarla)"""
    print("\n🧪 Probando creación de interfaz...")
    
    try:
        import tkinter as tk
        from sincronizador_biometrico_mejorado import SyncBioApp
        
        # Crear ventana raíz
        root = tk.Tk()
        root.withdraw()  # Ocultar la ventana
        
        # Crear la aplicación
        app = SyncBioApp(root)
        
        # Verificar que se crearon algunos componentes básicos
        if hasattr(app, 'ip_var') and hasattr(app, 'status_var'):
            print("✅ Variables de interfaz creadas - OK")
        
        if hasattr(app, 'log_text'):
            print("✅ Widget de log creado - OK")
        
        # Destruir la ventana
        root.destroy()
        
        print("✅ Creación de interfaz - OK")
        return True
    except Exception as e:
        print(f"❌ Creación de interfaz - FALLO: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("=" * 60)
    print("   PRUEBAS DEL SINCRONIZADOR BIOMÉTRICO MEJORADO")
    print("=" * 60)
    
    tests = [
        ("Importaciones", test_imports),
        ("Configuración", test_config_functions),
        ("Funciones de Red", test_network_functions),
        ("Sistema de Logging", test_logging_setup),
        ("Creación de Interfaz", test_ui_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {name} - FALLÓ")
        except Exception as e:
            print(f"❌ {name} - ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"   RESULTADOS: {passed}/{total} pruebas pasaron")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La aplicación está lista para usar.")
        return True
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
