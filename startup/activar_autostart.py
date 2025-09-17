#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Activar/Desactivar Autostart del Sincronizador Biométrico
=====================================================================

Script simple para configurar el inicio automático sin abrir la GUI.

Uso:
    python activar_autostart.py enable     # Habilitar autostart
    python activar_autostart.py disable    # Deshabilitar autostart
    python activar_autostart.py status     # Ver estado actual
"""

import sys
import os

def main():
    if len(sys.argv) != 2:
        print("Uso: python activar_autostart.py [enable|disable|status]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    try:
        # Importar funciones del módulo principal
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from sincronizador_biometrico_mejorado import (
            enable_startup, disable_startup, is_startup_enabled,
            load_config, save_config, config_data
        )
        
        # Cargar configuración
        load_config()
        
        if action == "enable":
            print("Habilitando inicio automático con Windows...")
            success = enable_startup()
            if success:
                config_data['START_WITH_WINDOWS'] = True
                save_config()
                print("✅ Inicio automático HABILITADO exitosamente")
                print("El sincronizador se iniciará automáticamente con Windows")
            else:
                print("❌ Error habilitando el inicio automático")
                sys.exit(1)
                
        elif action == "disable":
            print("Deshabilitando inicio automático con Windows...")
            success = disable_startup()
            if success:
                config_data['START_WITH_WINDOWS'] = False
                save_config()
                print("✅ Inicio automático DESHABILITADO exitosamente")
                print("El sincronizador ya no se iniciará automáticamente con Windows")
            else:
                print("❌ Error deshabilitando el inicio automático")
                sys.exit(1)
                
        elif action == "status":
            enabled = is_startup_enabled()
            config_enabled = config_data.get('START_WITH_WINDOWS', False)
            
            print("Estado del inicio automático:")
            print(f"  - Sistema: {'✅ HABILITADO' if enabled else '❌ DESHABILITADO'}")
            print(f"  - Configuración: {'✅ HABILITADO' if config_enabled else '❌ DESHABILITADO'}")
            
            if enabled != config_enabled:
                print("⚠️  ADVERTENCIA: Estado del sistema y configuración no coinciden")
                print("   Ejecuta 'enable' o 'disable' para sincronizar")
        else:
            print("Acción no válida. Usa: enable, disable, o status")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
