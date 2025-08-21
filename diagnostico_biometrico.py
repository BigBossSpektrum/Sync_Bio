#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Diagnóstico para Dispositivos Biométricos ZKTeco
Este script ayuda a diagnosticar problemas de conexión con dispositivos biométricos
"""

import socket
import subprocess
import time
import sys
from zk import ZK

def test_ping(ip):
    """Prueba la conectividad básica con ping"""
    print(f"🔍 Probando ping a {ip}...")
    try:
        result = subprocess.run(['ping', '-n', '4', ip], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Ping exitoso")
            # Extraer tiempo de respuesta
            lines = result.stdout.split('\n')
            for line in lines:
                if 'tiempo=' in line or 'time=' in line:
                    print(f"   📊 {line.strip()}")
            return True
        else:
            print("❌ Ping falló")
            print(f"   📋 Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error ejecutando ping: {e}")
        return False

def test_port(ip, port):
    """Prueba la conectividad TCP a un puerto específico"""
    print(f"🔍 Probando conectividad TCP a {ip}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        start_time = time.time()
        result = sock.connect_ex((ip, port))
        end_time = time.time()
        sock.close()
        
        if result == 0:
            print(f"✅ Puerto TCP {port} accesible")
            print(f"   📊 Tiempo de conexión: {(end_time - start_time)*1000:.2f}ms")
            return True
        else:
            print(f"❌ Puerto TCP {port} inaccesible (código: {result})")
            return False
    except Exception as e:
        print(f"❌ Error probando puerto TCP: {e}")
        return False

def test_zk_connection(ip, port):
    """Prueba la conexión específica con el protocolo ZKTeco"""
    print(f"🔍 Probando conexión ZKTeco a {ip}:{port}...")
    
    configurations = [
        {'force_udp': False, 'ommit_ping': False, 'name': 'TCP con ping'},
        {'force_udp': True, 'ommit_ping': False, 'name': 'UDP con ping'},
        {'force_udp': False, 'ommit_ping': True, 'name': 'TCP sin ping'},
        {'force_udp': True, 'ommit_ping': True, 'name': 'UDP sin ping'}
    ]
    
    for i, config in enumerate(configurations, 1):
        print(f"   🔄 Intento {i}/4: {config['name']}")
        try:
            zk = ZK(ip, port=port, timeout=15, 
                   force_udp=config['force_udp'], 
                   ommit_ping=config['ommit_ping'])
            
            start_time = time.time()
            conn = zk.connect()
            end_time = time.time()
            
            print(f"   ✅ Conexión exitosa en {(end_time - start_time)*1000:.2f}ms")
            
            # Obtener información del dispositivo
            try:
                device_name = conn.get_device_name()
                print(f"   📱 Dispositivo: {device_name}")
            except:
                print("   ⚠️ No se pudo obtener nombre del dispositivo")
            
            try:
                firmware = conn.get_firmware_version()
                print(f"   🔧 Firmware: {firmware}")
            except:
                print("   ⚠️ No se pudo obtener versión de firmware")
            
            try:
                users = conn.get_users()
                print(f"   👥 Usuarios: {len(users) if users else 0}")
            except:
                print("   ⚠️ No se pudo obtener usuarios")
            
            try:
                attendance = conn.get_attendance()
                print(f"   📄 Registros: {len(attendance) if attendance else 0}")
            except:
                print("   ⚠️ No se pudo obtener registros")
            
            try:
                conn.disconnect()
                print("   🔌 Desconectado correctamente")
            except:
                pass
            
            return True, config['name']
            
        except Exception as e:
            print(f"   ❌ Falló: {e}")
            continue
    
    print("❌ Todos los intentos de conexión ZKTeco fallaron")
    return False, None

def main():
    print("=" * 60)
    print("🧪 DIAGNÓSTICO DE DISPOSITIVO BIOMÉTRICO ZKTECO")
    print("=" * 60)
    
    # Solicitar datos al usuario
    ip = input("📍 Ingresa la IP del dispositivo (ej: 192.168.1.88): ").strip()
    if not ip:
        print("❌ IP requerida")
        return
    
    port_input = input("🔌 Ingresa el puerto (presiona Enter para 4370): ").strip()
    port = int(port_input) if port_input else 4370
    
    print(f"\n🎯 Diagnóstico para {ip}:{port}")
    print("-" * 40)
    
    # Pruebas de diagnóstico
    ping_ok = test_ping(ip)
    print()
    
    tcp_ok = test_port(ip, port)
    print()
    
    zk_ok, zk_method = test_zk_connection(ip, port)
    print()
    
    # Resumen
    print("=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    print(f"🌐 Ping: {'✅ OK' if ping_ok else '❌ FALLO'}")
    print(f"🔌 Puerto TCP: {'✅ OK' if tcp_ok else '❌ FALLO'}")
    print(f"📱 Conexión ZKTeco: {'✅ OK' if zk_ok else '❌ FALLO'}")
    if zk_ok:
        print(f"   🔧 Método exitoso: {zk_method}")
    
    print("\n💡 RECOMENDACIONES:")
    if not ping_ok:
        print("• Verifica que el dispositivo esté encendido")
        print("• Confirma que la IP sea correcta")
        print("• Revisa la configuración de red")
    elif not tcp_ok:
        print("• Verifica que el puerto sea correcto (usualmente 4370)")
        print("• Revisa si hay firewall bloqueando")
        print("• Confirma que el servicio del dispositivo esté activo")
    elif not zk_ok:
        print("• El dispositivo responde pero no con protocolo ZKTeco")
        print("• Podría ser un modelo incompatible")
        print("• Verifica la configuración del dispositivo")
    else:
        print("• ✅ Todo funciona correctamente!")
        print("• El problema podría estar en la aplicación principal")
        print("• Revisa los logs de la aplicación para más detalles")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚡ Diagnóstico interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    
    input("\nPresiona Enter para salir...")
