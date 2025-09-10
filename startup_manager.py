#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de Inicio Automático para Sincronizador Biométrico
=========================================================

Este script permite habilitar/deshabilitar fácilmente el inicio automático
del sincronizador biométrico con Windows.

Uso:
    python startup_manager.py --enable     # Habilitar inicio automático
    python startup_manager.py --disable    # Deshabilitar inicio automático  
    python startup_manager.py --status     # Ver estado actual
    python startup_manager.py --test       # Probar funcionalidad completa
"""

import sys
import os
import argparse

# Agregar el directorio actual al path para importar el módulo principal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(
        description='Gestor de Inicio Automático para Sincronizador Biométrico',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python startup_manager.py --enable     # Habilitar inicio automático
    python startup_manager.py --disable    # Deshabilitar inicio automático  
    python startup_manager.py --status     # Ver estado actual
    python startup_manager.py --test       # Probar funcionalidad completa
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--enable', action='store_true', 
                      help='Habilitar inicio automático con Windows')
    group.add_argument('--disable', action='store_true',
                      help='Deshabilitar inicio automático con Windows')
    group.add_argument('--status', action='store_true',
                      help='Mostrar estado actual del inicio automático')
    group.add_argument('--test', action='store_true',
                      help='Probar funcionalidad completa de startup')
    
    args = parser.parse_args()
    
    try:
        # Importar funciones del módulo principal
        from sincronizador_biometrico_mejorado import (
            enable_startup, disable_startup, is_startup_enabled, 
            test_startup_functionality, setup_logging
        )
        
        # Configurar logging
        setup_logging()
        
        print("🔧 GESTOR DE INICIO AUTOMÁTICO")
        print("=" * 50)
        
        if args.status:
            print("📋 Verificando estado actual...")
            status = is_startup_enabled()
            if status:
                print("✅ ESTADO: El inicio automático está HABILITADO")
                print("   El sincronizador se iniciará automáticamente con Windows")
            else:
                print("❌ ESTADO: El inicio automático está DESHABILITADO")
                print("   El sincronizador NO se iniciará automáticamente con Windows")
        
        elif args.enable:
            print("🚀 Habilitando inicio automático...")
            current_status = is_startup_enabled()
            
            if current_status:
                print("ℹ️  El inicio automático ya está habilitado")
            else:
                success = enable_startup()
                if success:
                    print("✅ ÉXITO: Inicio automático habilitado correctamente")
                    print("   El sincronizador se iniciará automáticamente con Windows")
                    print("   Nota: Se ejecutará en modo silencioso en segundo plano")
                else:
                    print("❌ ERROR: No se pudo habilitar el inicio automático")
                    print("   Verifique los logs para más detalles")
        
        elif args.disable:
            print("🛑 Deshabilitando inicio automático...")
            current_status = is_startup_enabled()
            
            if not current_status:
                print("ℹ️  El inicio automático ya está deshabilitado")
            else:
                success = disable_startup()
                if success:
                    print("✅ ÉXITO: Inicio automático deshabilitado correctamente")
                    print("   El sincronizador NO se iniciará automáticamente con Windows")
                else:
                    print("❌ ERROR: No se pudo deshabilitar el inicio automático")
                    print("   Verifique los logs para más detalles")
        
        elif args.test:
            print("🧪 Ejecutando pruebas de funcionalidad...")
            results = test_startup_functionality()
            
            print("\n📊 RESULTADOS DE LAS PRUEBAS:")
            print("-" * 30)
            for key, value in results.items():
                status_icon = "✅" if value else "❌"
                print(f"{status_icon} {key}: {value}")
            
            # Análisis de resultados
            print("\n📝 ANÁLISIS:")
            if results['enable_result'] and results['enabled_status']:
                print("✅ La funcionalidad de habilitación funciona correctamente")
            else:
                print("❌ Problema con la funcionalidad de habilitación")
            
            if results['disable_result'] and not results['disabled_status']:
                print("✅ La funcionalidad de deshabilitación funciona correctamente")
            else:
                print("❌ Problema con la funcionalidad de deshabilitación")
        
        print("\n" + "=" * 50)
        print("✅ Operación completada")
        
    except ImportError as e:
        print(f"❌ ERROR: No se pudo importar el módulo principal: {e}")
        print("   Asegúrese de ejecutar este script desde el directorio del proyecto")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
