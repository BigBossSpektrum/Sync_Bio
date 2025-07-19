# BioData Sync

> Sincronización de registros biométricos ZKTeco con servidor Django remoto.

---

## 📌 Descripción

Este proyecto permite:
- Conectarse a un dispositivo biométrico ZKTeco vía red.
- Extraer todos los registros de asistencia.
- Enviar los registros al servidor remoto vía HTTP en formato JSON.

No requiere conexión directa al ORM de Django. Diseñado para ejecutarse en cualquier máquina con Python instalado.

---

## ⚙️ Requisitos

- Python 3.8 o superior
- Conexión de red con el biométrico
- Conexión a internet hacia el servidor remoto

### 🔧 Dependencias

Instala los módulos necesarios con:

```bash
pip install -r requirements.txt
