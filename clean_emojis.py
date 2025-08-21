#!/usr/bin/env python3
# Script para limpiar emojis de los mensajes de logging

import re

# Diccionario de reemplazos de emojis por texto
emoji_replacements = {
    "🚀": "INICIO:",
    "✅": "OK:",
    "❌": "ERROR:",
    "📝": "CONFIG:",
    "💾": "SAVE:",
    "🏓": "PING:",
    "🔌": "TCP:",
    "⚠️": "WARNING:",
    "🔄": "SYNC:",
    "📊": "INFO:",
    "🔥": "CRITICAL:",
    "💻": "SYSTEM:",
    "📈": "STATS:",
    "⏰": "TIME:",
    "📋": "DATA:",
    "🎯": "TARGET:",
    "🔍": "DEBUG:"
}

def clean_emojis_in_file(file_path):
    """Limpia emojis de un archivo Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Reemplazar emojis en mensajes de logging
        for emoji, replacement in emoji_replacements.items():
            # Buscar patrones como logging.info("🚀 mensaje")
            pattern = rf'(logging\.(info|warning|error|debug)\([^)]*"){emoji}([^"]*")'
            replacement_text = rf'\1{replacement}\3'
            content = re.sub(pattern, replacement_text, content)
        
        # Verificar si hubo cambios
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Archivo {file_path} actualizado")
            return True
        else:
            print(f"ℹ️ No se encontraron emojis para limpiar en {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {e}")
        return False

if __name__ == "__main__":
    file_path = "c:\\Users\\Entrecables y Redes\\Documents\\GitHub\\Sync_Bio\\sincronizador_biometrico_mejorado.py"
    clean_emojis_in_file(file_path)
