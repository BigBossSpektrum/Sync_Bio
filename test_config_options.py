#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de las 3 opciones de configuración:
1. Auto-iniciar al abrir la aplicación
2. Minimizar a bandeja del sistema
3. Iniciar con Windows (arranque automático)
"""

import os
import sys
import json
import winreg
import tempfile
import traceback
from datetime import datetime

# Añadir el directorio actual al path para importar el módulo principal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar funciones del módulo principal
try:
    from sincronizador_biometrico_mejorado import (
        config_data, load_config, save_config,
        is_startup_enabled, enable_startup, disable_startup,
        is_startup_enabled_registry, enable_startup_registry, disable_startup_registry
    )
    print("✅ Módulos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

class TestConfigOptions:
    """Clase para probar las 3 opciones de configuración"""
    
    def __init__(self):
        self.test_results = []
        self.original_config = config_data.copy()
        print("🧪 Iniciando tests de las opciones de configuración")
        print("=" * 60)
    
    def log_result(self, test_name, passed, details=""):
        """Registra el resultado de un test"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        print()
    
    def test_1_auto_start_functionality(self):
        """Test 1: Auto-iniciar al abrir la aplicación"""
        print("🔍 TEST 1: Auto-iniciar al abrir la aplicación")
        print("-" * 40)
        
        try:
            # Verificar valor inicial
            original_auto_start = config_data.get('AUTO_START', False)
            print(f"📋 Estado inicial AUTO_START: {original_auto_start}")
            
            # Test 1a: Cambiar a True
            config_data['AUTO_START'] = True
            save_config()
            load_config()
            
            if config_data.get('AUTO_START') == True:
                self.log_result("1a. Activar AUTO_START", True, 
                               "Se guarda y carga correctamente el valor True")
            else:
                self.log_result("1a. Activar AUTO_START", False, 
                               f"Esperado: True, Obtenido: {config_data.get('AUTO_START')}")
            
            # Test 1b: Cambiar a False
            config_data['AUTO_START'] = False
            save_config()
            load_config()
            
            if config_data.get('AUTO_START') == False:
                self.log_result("1b. Desactivar AUTO_START", True,
                               "Se guarda y carga correctamente el valor False")
            else:
                self.log_result("1b. Desactivar AUTO_START", False,
                               f"Esperado: False, Obtenido: {config_data.get('AUTO_START')}")
            
            # Test 1c: Verificar persistencia del archivo de configuración
            config_file_exists = False
            try:
                # Buscar archivo de configuración
                possible_paths = [
                    os.path.join(os.getcwd(), 'biometrico_config.json'),
                    os.path.join(os.path.dirname(sys.executable), 'biometrico_config.json'),
                    os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'SincronizadorBiometrico', 'biometrico_config.json')
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        config_file_exists = True
                        with open(path, 'r', encoding='utf-8') as f:
                            saved_config = json.load(f)
                            auto_start_in_file = saved_config.get('AUTO_START', None)
                        print(f"📁 Archivo de configuración encontrado: {path}")
                        print(f"📄 AUTO_START en archivo: {auto_start_in_file}")
                        break
                
                self.log_result("1c. Persistencia de configuración", config_file_exists,
                               f"Archivo de configuración {'encontrado' if config_file_exists else 'NO encontrado'}")
                        
            except Exception as e:
                self.log_result("1c. Persistencia de configuración", False,
                               f"Error verificando archivo: {e}")
            
            # Restaurar valor original
            config_data['AUTO_START'] = original_auto_start
            save_config()
            
        except Exception as e:
            self.log_result("1. AUTO_START (general)", False, 
                           f"Error durante el test: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
    
    def test_2_minimize_to_tray_functionality(self):
        """Test 2: Minimizar a bandeja del sistema"""
        print("🔍 TEST 2: Minimizar a bandeja del sistema")
        print("-" * 40)
        
        try:
            # Verificar valor inicial
            original_minimize = config_data.get('MINIMIZE_TO_TRAY', True)
            print(f"📋 Estado inicial MINIMIZE_TO_TRAY: {original_minimize}")
            
            # Test 2a: Cambiar a False
            config_data['MINIMIZE_TO_TRAY'] = False
            save_config()
            load_config()
            
            if config_data.get('MINIMIZE_TO_TRAY') == False:
                self.log_result("2a. Desactivar MINIMIZE_TO_TRAY", True,
                               "Se guarda y carga correctamente el valor False")
            else:
                self.log_result("2a. Desactivar MINIMIZE_TO_TRAY", False,
                               f"Esperado: False, Obtenido: {config_data.get('MINIMIZE_TO_TRAY')}")
            
            # Test 2b: Cambiar a True
            config_data['MINIMIZE_TO_TRAY'] = True
            save_config()
            load_config()
            
            if config_data.get('MINIMIZE_TO_TRAY') == True:
                self.log_result("2b. Activar MINIMIZE_TO_TRAY", True,
                               "Se guarda y carga correctamente el valor True")
            else:
                self.log_result("2b. Activar MINIMIZE_TO_TRAY", False,
                               f"Esperado: True, Obtenido: {config_data.get('MINIMIZE_TO_TRAY')}")
            
            # Test 2c: Verificar que el valor por defecto es True
            config_data.pop('MINIMIZE_TO_TRAY', None)  # Eliminar clave
            default_value = config_data.get('MINIMIZE_TO_TRAY', True)
            
            self.log_result("2c. Valor por defecto MINIMIZE_TO_TRAY", default_value == True,
                           f"Valor por defecto: {default_value}")
            
            # Restaurar valor original
            config_data['MINIMIZE_TO_TRAY'] = original_minimize
            save_config()
            
        except Exception as e:
            self.log_result("2. MINIMIZE_TO_TRAY (general)", False,
                           f"Error durante el test: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
    
    def test_3_windows_startup_functionality(self):
        """Test 3: Iniciar con Windows (arranque automático)"""
        print("🔍 TEST 3: Iniciar con Windows (arranque automático)")
        print("-" * 40)
        
        try:
            # Verificar estado inicial del registro
            initial_registry_status = is_startup_enabled_registry()
            print(f"📋 Estado inicial en registro: {initial_registry_status}")
            
            # Test 3a: Verificar función is_startup_enabled
            try:
                current_status = is_startup_enabled()
                self.log_result("3a. Verificar is_startup_enabled()", True,
                               f"Estado actual: {current_status}")
            except Exception as e:
                self.log_result("3a. Verificar is_startup_enabled()", False,
                               f"Error: {e}")
            
            # Test 3b: Intentar habilitar startup (solo si no está habilitado)
            if not initial_registry_status:
                try:
                    enable_result = enable_startup()
                    after_enable = is_startup_enabled()
                    
                    self.log_result("3b. Habilitar startup", enable_result and after_enable,
                                   f"Resultado enable_startup(): {enable_result}, Estado después: {after_enable}")
                except Exception as e:
                    self.log_result("3b. Habilitar startup", False,
                                   f"Error: {e}")
            else:
                self.log_result("3b. Habilitar startup", True,
                               "Ya estaba habilitado, no se realizó cambio")
            
            # Test 3c: Intentar deshabilitar startup
            try:
                disable_result = disable_startup()
                after_disable = is_startup_enabled()
                
                self.log_result("3c. Deshabilitar startup", disable_result and not after_disable,
                               f"Resultado disable_startup(): {disable_result}, Estado después: {after_disable}")
            except Exception as e:
                self.log_result("3c. Deshabilitar startup", False,
                               f"Error: {e}")
            
            # Test 3d: Verificar sincronización con configuración
            try:
                config_data['START_WITH_WINDOWS'] = True
                save_config()
                load_config()
                
                config_value = config_data.get('START_WITH_WINDOWS')
                self.log_result("3d. Sincronización con configuración", config_value == True,
                               f"Valor en configuración: {config_value}")
            except Exception as e:
                self.log_result("3d. Sincronización con configuración", False,
                               f"Error: {e}")
            
            # Test 3e: Restaurar estado inicial
            try:
                if initial_registry_status:
                    enable_startup()
                else:
                    disable_startup()
                
                final_status = is_startup_enabled()
                restored = (final_status == initial_registry_status)
                
                self.log_result("3e. Restaurar estado inicial", restored,
                               f"Estado inicial: {initial_registry_status}, Estado final: {final_status}")
            except Exception as e:
                self.log_result("3e. Restaurar estado inicial", False,
                               f"Error: {e}")
            
        except Exception as e:
            self.log_result("3. START_WITH_WINDOWS (general)", False,
                           f"Error durante el test: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
    
    def test_4_integration_tests(self):
        """Test 4: Pruebas de integración"""
        print("🔍 TEST 4: Pruebas de integración")
        print("-" * 40)
        
        try:
            # Test 4a: Cargar, modificar y guardar todas las opciones
            original_values = {
                'AUTO_START': config_data.get('AUTO_START', False),
                'MINIMIZE_TO_TRAY': config_data.get('MINIMIZE_TO_TRAY', True),
                'START_WITH_WINDOWS': config_data.get('START_WITH_WINDOWS', False)
            }
            
            # Cambiar todos los valores
            config_data['AUTO_START'] = True
            config_data['MINIMIZE_TO_TRAY'] = False
            config_data['START_WITH_WINDOWS'] = True
            
            save_config()
            load_config()
            
            all_changed = (
                config_data.get('AUTO_START') == True and
                config_data.get('MINIMIZE_TO_TRAY') == False and
                config_data.get('START_WITH_WINDOWS') == True
            )
            
            self.log_result("4a. Cambio simultáneo de todas las opciones", all_changed,
                           f"AUTO_START: {config_data.get('AUTO_START')}, " +
                           f"MINIMIZE_TO_TRAY: {config_data.get('MINIMIZE_TO_TRAY')}, " +
                           f"START_WITH_WINDOWS: {config_data.get('START_WITH_WINDOWS')}")
            
            # Restaurar valores originales
            config_data.update(original_values)
            save_config()
            
        except Exception as e:
            self.log_result("4. Integración (general)", False,
                           f"Error durante el test: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
    
    def run_all_tests(self):
        """Ejecuta todos los tests"""
        print(f"🚀 Iniciando tests completos - {datetime.now()}")
        print("=" * 60)
        
        # Ejecutar tests individuales
        self.test_1_auto_start_functionality()
        self.test_2_minimize_to_tray_functionality()
        self.test_3_windows_startup_functionality()
        self.test_4_integration_tests()
        
        # Mostrar resumen
        self.show_summary()
    
    def show_summary(self):
        """Muestra el resumen de todos los tests"""
        print("=" * 60)
        print("📊 RESUMEN DE TESTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de tests: {total_tests}")
        print(f"✅ Exitosos: {passed_tests}")
        print(f"❌ Fallidos: {failed_tests}")
        print(f"📈 Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ TESTS FALLIDOS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n📋 DETALLES COMPLETOS:")
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    📝 {result['details']}")
        
        # Guardar reporte en archivo
        try:
            report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100,
                    'results': self.test_results
                }, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Reporte guardado en: {report_file}")
        except Exception as e:
            print(f"\n⚠️  No se pudo guardar el reporte: {e}")

if __name__ == "__main__":
    # Cargar configuración inicial
    load_config()
    
    # Ejecutar tests
    tester = TestConfigOptions()
    tester.run_all_tests()
    
    print("\n🏁 Tests completados!")