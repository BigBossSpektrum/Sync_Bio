# Demo del Sincronizador Biométrico Mejorado
# Este script demuestra las principales funcionalidades

import os
import sys

# Configurar la codificación para Windows
if os.name == 'nt':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def print_header(title):
    """Imprime un encabezado con formato"""
    print("\n" + "=" * 60)
    print(f"   {title}")
    print("=" * 60)

def demo_config():
    """Demuestra las funciones de configuración"""
    print_header("DEMO: CONFIGURACIÓN")
    
    try:
        from sincronizador_biometrico_mejorado import config_data, save_config, load_config
        
        print("Configuración actual:")
        for key, value in config_data.items():
            if key != 'sync_running':
                print(f"  {key}: {value}")
        
        print("\nGuardando configuración...")
        save_config()
        print("Configuración guardada exitosamente!")
        
    except Exception as e:
        print(f"Error en demo de configuración: {e}")

def demo_network_tests():
    """Demuestra las pruebas de red"""
    print_header("DEMO: PRUEBAS DE RED")
    
    try:
        from sincronizador_biometrico_mejorado import test_ping, test_tcp_port
        
        # Probar ping a localhost
        print("Probando ping a localhost...")
        success, message = test_ping('127.0.0.1', timeout=3)
        print(f"Resultado: {'ÉXITO' if success else 'FALLO'} - {message}")
        
        # Probar ping a Google DNS
        print("\nProbando ping a Google DNS (8.8.8.8)...")
        success, message = test_ping('8.8.8.8', timeout=3)
        print(f"Resultado: {'ÉXITO' if success else 'FALLO'} - {message}")
        
        # Probar puerto cerrado
        print("\nProbando puerto TCP cerrado...")
        success, message = test_tcp_port('127.0.0.1', 9999, timeout=2)
        print(f"Resultado: {'ÉXITO' if success else 'FALLO'} - {message}")
        
    except Exception as e:
        print(f"Error en demo de red: {e}")

def demo_device_simulation():
    """Simula una prueba de dispositivo"""
    print_header("DEMO: SIMULACIÓN DE DISPOSITIVO")
    
    print("Esta demo simula la conexión a un dispositivo biométrico.")
    print("En un entorno real, necesitarías:")
    print("  - Un dispositivo ZKTeco conectado a la red")
    print("  - La IP correcta del dispositivo")
    print("  - Puerto 4370 abierto")
    print("  - Dispositivo encendido y accesible")
    
    # Mostrar cómo se vería una conexión real
    ip_ejemplo = "192.168.1.88"
    puerto_ejemplo = 4370
    
    print(f"\nEjemplo de configuración:")
    print(f"  IP del dispositivo: {ip_ejemplo}")
    print(f"  Puerto: {puerto_ejemplo}")
    print(f"  Nombre de estación: Oficina Principal")
    
    print(f"\nPara probar con un dispositivo real:")
    print(f"  1. Configurar la IP correcta en la aplicación")
    print(f"  2. Usar el botón 'Prueba Completa'")
    print(f"  3. Verificar conectividad antes de sincronizar")

def demo_logging():
    """Demuestra el sistema de logging"""
    print_header("DEMO: SISTEMA DE LOGGING")
    
    try:
        import logging
        
        # Mostrar archivos de log existentes
        log_dir = "logs"
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            print(f"Archivos de log encontrados en '{log_dir}':")
            for log_file in log_files:
                file_path = os.path.join(log_dir, log_file)
                file_size = os.path.getsize(file_path)
                print(f"  {log_file} ({file_size} bytes)")
        else:
            print("Directorio de logs no encontrado.")
            
        # Generar algunos logs de ejemplo
        print("\nGenerando logs de ejemplo...")
        logging.info("DEMO: Mensaje de información")
        logging.warning("DEMO: Mensaje de advertencia")
        logging.error("DEMO: Mensaje de error")
        
        print("Logs generados exitosamente!")
        
    except Exception as e:
        print(f"Error en demo de logging: {e}")

def show_features():
    """Muestra las características principales"""
    print_header("CARACTERÍSTICAS PRINCIPALES")
    
    features = [
        "✓ Interfaz gráfica intuitiva",
        "✓ Configuración persistente",
        "✓ Pruebas de conexión avanzadas",
        "✓ Sincronización automática cada X minutos",
        "✓ Ejecución en segundo plano",
        "✓ Bandeja del sistema",
        "✓ Sistema de logs robusto",
        "✓ Validación de entrada",
        "✓ Exportar/importar configuración",
        "✓ Prevención de múltiples instancias",
        "✓ Auto-inicio opcional",
        "✓ Manejo de errores avanzado"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print(f"\nTotal: {len(features)} características implementadas")

def show_usage_guide():
    """Muestra una guía de uso rápida"""
    print_header("GUÍA DE USO RÁPIDA")
    
    steps = [
        "1. Ejecutar 'ejecutar_mejorado.bat' o la aplicación",
        "2. Configurar IP, puerto y nombre de estación",
        "3. Hacer clic en 'Prueba Completa' para verificar conexión",
        "4. Ejecutar una sincronización manual para probar",
        "5. Iniciar sincronización automática",
        "6. Hacer clic en 'Ocultar en Segundo Plano'",
        "7. La aplicación quedará en la bandeja del sistema",
        "8. Usar clic derecho en la bandeja para controlar"
    ]
    
    for step in steps:
        print(f"  {step}")

def main():
    """Función principal del demo"""
    print_header("DEMO DEL SINCRONIZADOR BIOMÉTRICO MEJORADO")
    
    print("Este demo muestra las funcionalidades principales de la aplicación.")
    print("Para una demostración completa, ejecuta la aplicación gráfica.")
    
    # Ejecutar demos
    show_features()
    demo_config()
    demo_logging()
    demo_network_tests()
    demo_device_simulation()
    show_usage_guide()
    
    print_header("FIN DEL DEMO")
    print("Para usar la aplicación completa, ejecuta:")
    print("  ejecutar_mejorado.bat")
    print("o")
    print("  python sincronizador_biometrico_mejorado.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDemo interrumpido por el usuario.")
    except Exception as e:
        print(f"\nError en el demo: {e}")
    
    input("\nPresiona Enter para salir...")
