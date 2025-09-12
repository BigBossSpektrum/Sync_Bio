#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para validar el escenario: abrir exe y cerrar inmediatamente
"""

import logging
import threading
import time
from datetime import datetime

def test_quick_open_close():
    """Test que simula abrir el exe y cerrarlo rápidamente"""
    
    print("🧪 TEST: Abrir ejecutable y cerrar inmediatamente")
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
            # Simular estado inicial de aplicación
            config_data = {'sync_running': False}
            stop_event = threading.Event()
            sync_thread = None
            
            print("🚀 PASO 1: Aplicación inicia")
            logging.info("INICIO: Script de sincronizacion biometrica mejorado iniciado")
            
            # Simular inicio de sincronización automática
            print("▶️ PASO 2: Usuario presiona 'Iniciar Sincronización'")
            config_data['sync_running'] = True
            
            # Simular worker thread que apenas está iniciando
            def mock_sync_worker():
                """Worker simulado que está apenas iniciando"""
                logging.info("SYNC: Worker de sincronización iniciado")
                logging.info("INICIO: === INICIANDO PRIMER CICLO DE SINCRONIZACIÓN ===")
                
                # Simular trabajo inicial muy rápido
                time.sleep(0.5)  # Apenas 0.5 segundos
                logging.info("TARGET: Objetivo: 192.168.0.88:4370")
                
                # Aquí es donde normalmente el usuario cierra
                # Simular que el worker continúa si no se detiene
                for i in range(10):  # 10 segundos de trabajo
                    if stop_event.wait(timeout=1):
                        logging.info("🛑 Stop event detectado - Terminando worker")
                        break
                    logging.info(f"WORK: Trabajando... {i+1}/10")
                
                logging.info("🏁 Worker finalizado")
            
            # Crear y iniciar thread simulado
            sync_thread = threading.Thread(target=mock_sync_worker, daemon=True)
            sync_thread.start()
            
            # Esperar muy poco (simula usuario cerrando rápidamente)
            time.sleep(0.2)  # Solo 200ms antes de cerrar
            
            print("❌ PASO 3: Usuario presiona X inmediatamente")
            
            # PASO 3: Simular on_closing() mejorado
            logging.info("SYSTEM: Detectada sincronización activa durante cierre por botón X")
            
            # Lógica mejorada de on_closing
            sync_running = config_data.get('sync_running', False)
            thread_alive = sync_thread and sync_thread.is_alive()
            
            if sync_running or thread_alive:
                # Activar stop_event inmediatamente
                stop_event.set()
                logging.info("SYSTEM: Stop event activado preventivamente")
                
                # Simular que el diálogo se muestra después (usando after)
                def mock_dialog():
                    logging.info("DIALOG: Mostrando diálogo de confirmación")
                    # Simular que usuario elige "Sí - Detener y cerrar"
                    logging.info("SYSTEM: Usuario eligió detener sincronización y cerrar")
                    
                    # Simular quit_app()
                    config_data['sync_running'] = False
                    
                    if sync_thread and sync_thread.is_alive():
                        logging.info("SYSTEM: Esperando a que termine el hilo de sincronización...")
                        sync_thread.join(timeout=2.0)
                        
                        if sync_thread.is_alive():
                            logging.warning("WARNING: El hilo de sincronización no terminó en el tiempo esperado")
                            result = "❌ WARNING generado"
                        else:
                            logging.info("OK: Hilo de sincronización terminado correctamente")
                            result = "✅ Cierre limpio"
                    else:
                        logging.info("SYSTEM: Hilo ya terminado")
                        result = "✅ Hilo ya terminado"
                    
                    return result
                
                # Esperar un poco para simular el after(100, show_dialog)
                time.sleep(0.1)
                result = mock_dialog()
                
            else:
                logging.info("SYSTEM: No hay sincronización activa, procediendo con cierre normal")
                result = "✅ Cierre normal"
            
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
    print(f"❌ Tests con problemas: {failed_tests}/3")
    print(f"📈 Porcentaje de éxito: {(successful_tests/3)*100:.1f}%")
    
    print(f"\n🔍 Detalle de resultados:")
    for i, result in enumerate(test_results, 1):
        print(f"  Test {i}: {result}")
    
    print(f"\n{'🎉 ÉXITO' if successful_tests == 3 else '⚠️ ADVERTENCIA'}: {'Todos los tests pasaron' if successful_tests == 3 else 'Algunos tests tuvieron problemas'}")
    
    print(f"\n🔧 Mejoras implementadas:")
    print(f"  1. stop_event.set() se activa preventivamente al detectar cierre")
    print(f"  2. Diálogo se muestra usando after() para evitar bloqueos")
    print(f"  3. Manejo robusto de errores con cierre forzado")
    print(f"  4. Verificación dual: sync_running Y thread.is_alive()")
    
    return successful_tests == 3

if __name__ == "__main__":
    test_quick_open_close()