#!/usr/bin/env python3
# Script para limpiar emojis de logging - versión simple

# Mapeo de emojis a texto
replacements = [
    ("🚀", "INICIO:"),
    ("✅", "OK:"),
    ("❌", "ERROR:"),
    ("📝", "CONFIG:"),
    ("💾", "SAVE:"),
    ("🏓", "PING:"),
    ("🔌", "DEVICE:"),
    ("⚠️", "WARNING:"),
    ("🔄", "SYNC:"),
    ("📊", "INFO:"),
    ("🔥", "CRITICAL:"),
    ("💻", "SYSTEM:"),
    ("📈", "STATS:"),
    ("⏰", "TIME:"),
    ("📋", "DATA:"),
    ("🎯", "TARGET:"),
    ("🔍", "DEBUG:"),
    ("⏳", "WAIT:"),
    ("🧪", "TEST:"),
    ("📱", "DEVICE:"),
    ("🔧", "CONFIG:"),
    ("🆔", "ID:"),
    ("👥", "USERS:"),
    ("📄", "RECORDS:"),
    ("📥", "GET:"),
    ("🔒", "LOCK:"),
    ("📤", "SEND:"),
    ("🎉", "SUCCESS:"),
    ("🚨", "ALERT:"),
    ("💡", "INFO:"),
]

file_path = r"c:\Users\Entrecables y Redes\Documents\GitHub\Sync_Bio\src\sincronizador_biometrico_mejorado.py"

try:
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aplicar todos los reemplazos
    for emoji, replacement in replacements:
        content = content.replace(emoji, replacement)
    
    # Escribir el archivo corregido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Archivo actualizado exitosamente - emojis reemplazados")
    
except Exception as e:
    print(f"❌ Error: {e}")
