import json
import os
from datetime import datetime

print("Cargando configuraci√≥n actual...")
with open('biometrico_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

print("Haciendo cambios simulados...")
config['IP_BIOMETRICO'] = '192.168.1.100'
config['PUERTO_BIOMETRICO'] = 4371
config['NOMBRE_ESTACION'] = 'EstacionPrueba'
config['INTERVALO_MINUTOS'] = 10
config['AUTO_START'] = True
config['test_change'] = 'Cambio de prueba para verificar persistencia'
config['last_updated'] = datetime.now().isoformat()

print("Guardando cambios...")
with open('biometrico_config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("‚úÖ Cambios guardados exitosamente")
print("Ì≥ã Nuevos valores:")
print(f"   IP: {config['IP_BIOMETRICO']}")
print(f"   Puerto: {config['PUERTO_BIOMETRICO']}")
print(f"   Estaci√≥n: {config['NOMBRE_ESTACION']}")
print(f"   Autostart: {config['AUTO_START']}")
