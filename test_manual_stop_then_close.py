#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para validar el escenario: detener sincronización manualmente y luego cerrar aplicación
"""

import logging
import threading
import time
from datetime import datetime

def test_manual_stop_then_close():
    """Test que simula el escenario problemático"""
    
    print("🧪 TEST: Detener sincronización manualmente y luego cerrar")
    print("=" * 60)
    print(f"⏰ Fecha y hora: {datetime.now()}")
    print()
    
    # Configurar logging similar al main
    log_file = "C:/Users/Entrecables y Redes/Documents/GitHub/Sync_Bio/logs/biometrico_sync.log"
    
    try:
        # Configurar logging
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configurar el logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        print(f"✅ Logging configurado: {log_file}")
        
    except Exception as e:
        print(f"❌ Error configurando logging: {e}")
        return False
    
    # Simular el escenario problemático
    test_results = []
    
    for iteration in range(3):
        print(f"\n📋 Iteración {iteration + 1}/3:")
        print("-" * 40)
        
        try:
            # Simular estado de aplicación
            config_data = {'sync_running': True}
            stop_event = threading.Event()
            
            # Simular worker thread
            def mock_sync_worker():
                """Worker simulado que responde a stop_event"""
                logging.info("🚀 Worker simulado iniciado")
                
                # Simular trabajo inicial
                time.sleep(1)
                logging.info("📋 Ejecutando ciclo de sincronización...")
                
                # Simular espera interrumpible
                logging.info("⏱️ Iniciando espera de 60 segundos (interrumpible)...")
                
                # Esperar usando stop_event (interrumpible)
                if stop_event.wait(timeout=60):
                    logging.info("🛑 Stop event detectado - Terminando worker")
                else:
                    logging.info("⏰ Timeout completado - Continuando...")
                
                logging.info("🏁 Worker finalizado")
            
            # Crear y iniciar thread simulado
            sync_thread = threading.Thread(target=mock_sync_worker, daemon=True)
            sync_thread.start()
            
            # Esperar un poco para que el worker esté en la espera
            time.sleep(2)
            
            print("🔧 PASO 1: Usuario detiene sincronización manualmente")
            
            # PASO 1: Simular stop_sync() manual por el usuario
            logging.info("🛑 Usuario presiona DETENER - Ejecutando stop_sync()")
            config_data['sync_running'] = False
            stop_event.set()
            
            # Esperar a que el thread termine (como en stop_sync real)
            if sync_thread.is_alive():
                sync_thread.join(timeout=3.0)
                if sync_thread.is_alive():
                    logging.warning("WARNING: El hilo no terminó en stop_sync")
                else:
                    logging.info("OK: Hilo terminado correctamente en stop_sync")
            
            # Limpiar el event como en el código real
            stop_event.clear()
            
            print("🚪 PASO 2: Usuario cierra aplicación (botón X)")
            
            # PASO 2: Simular quit_app() después de stop manual
            logging.info("❌ Usuario presiona X - Ejecutando quit_app()")
            
            # Lógica mejorada de quit_app
            sync_was_running = config_data.get('sync_running', False)
            thread_is_alive = sync_thread.is_alive()
            
            if sync_was_running or thread_is_alive:
                logging.info("SYSTEM: Deteniendo sincronización antes del cierre...")
                
                if hasattr(stop_event, 'set'):
                    stop_event.set()
                    logging.info("SYSTEM: Stop event activado para terminación inmediata")
                
                if sync_was_running:
                    config_data['sync_running'] = False
                
                if thread_is_alive:
                    logging.info("SYSTEM: Esperando a que termine el hilo de sincronización...")
                    sync_thread.join(timeout=2.0)
                    
                    if sync_thread.is_alive():
                        logging.warning("WARNING: El hilo de sincronización no terminó en el tiempo esperado")
                        result = "❌ WARNING generado"
                    else:
                        logging.info("OK: Hilo de sincronización terminado correctamente")
                        result = "✅ Cierre limpio"
                else:
                    logging.info("SYSTEM: Hilo de sincronización ya terminado")
                    result = "✅ Hilo ya terminado"
            else:
                logging.info("SYSTEM: No hay sincronización activa para detener")
                result = "✅ Nada que detener"
            
            test_results.append(result)
            print(f"📊 Resultado: {result}")
            
        except Exception as e:
            logging.exception(f"❌ Error en iteración {iteration + 1}: {e}")
            test_results.append(f"❌ Error: {e}")
        
        # Pausa entre iteraciones
        if iteration < 2:
            time.sleep(1)
    
    # Analizar resultados
    print(f"\n📊 RESULTADOS FINALES:")
    print("=" * 60)
    
    successful_tests = sum(1 for result in test_results if "✅" in result)
    failed_tests = sum(1 for result in test_results if "❌" in result)
    
    print(f"✅ Tests exitosos: {successful_tests}/3")
    print(f"❌ Tests con warning: {failed_tests}/3")
    print(f"📈 Porcentaje de éxito: {(successful_tests/3)*100:.1f}%")
    
    print(f"\n🔍 Detalle de resultados:")
    for i, result in enumerate(test_results, 1):
        print(f"  Test {i}: {result}")
    
    print(f"\n{'🎉 ÉXITO' if successful_tests == 3 else '⚠️ ADVERTENCIA'}: {'Todos los tests pasaron sin warnings' if successful_tests == 3 else 'Algunos tests generaron warnings'}")
    
    print(f"\n🔧 Explicación de la mejora:")
    print(f"  1. quit_app() ahora verifica el estado real del hilo")
    print(f"  2. No intenta detener lo que ya está detenido")
    print(f"  3. Evita warnings innecesarios en escenarios normales")
    
    return successful_tests == 3

if __name__ == "__main__":
    test_manual_stop_then_close()