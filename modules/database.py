import json
import os
import pandas as pd
from datetime import datetime
from io import BytesIO

DB_FILE = "disys_db.json"

def cargar_db():
    """Carga toda la base de datos estructurada desde el archivo JSON local."""
    if not os.path.exists(DB_FILE):
        db_inicial = {
            "bodegas": {
                "bodega_principal": {
                    "id": "bodega_principal",
                    "nombre": "Bodega Principal Táchira",
                    "dueño": "Deibys Ibañes",
                    "telefono": "04242954794",
                    "gmail_respaldo": "disys25@gmail.com",
                    "activa": True,
                    "max_empleados": 10,
                    "modulos_carga": {"monto": True, "productos": True, "foto": False},
                    "tasas": {"usd_to_cop": 4100.0, "ves_factor": 3.0}
                }
            },
            "usuarios": [
                {
                    "username": "supermaster",
                    "password": "123",
                    "nombre": "Super Administrador",
                    "rol": "SUPER_MASTER",
                    "bodega_id": "",
                    "activo": True
                },
                {
                    "username": "deibys",
                    "password": "123",
                    "nombre": "Deibys Ibañes",
                    "rol": "MASTER",
                    "bodega_id": "bodega_principal",
                    "activo": True
                }
            ],
            "clientes": [],
            "movimientos": [],
            "solicitudes_sobregiro": []
        }
        guardar_db(db_inicial)
        return db_inicial
    
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "bodegas": {},
            "usuarios": [],
            "clientes": [],
            "movimientos": [],
            "solicitudes_sobregiro": []
        }

def guardar_db(db):
    """Guarda y sincroniza toda la base de datos en el archivo JSON local."""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error al guardar base de datos local: {e}")

def encolar_y_sincronizar(db, bodega_id, tipo_evento, detalle):
    """Función de compatibilidad para eventos."""
    guardar_db(db)

def fecha_actual_str():
    return datetime.now().strftime("%d/%m/%Y")

def solo_fecha_str():
    return datetime.now().strftime("%Y-%m-%d")

def autenticar_usuario(username, password):
    db = cargar_db()
    u_limpio = username.strip().lower()
    p_limpio = password.strip()

    for u in db.get("usuarios", []):
        if u.get("username", "").strip().lower() == u_limpio and str(u.get("password", "")).strip() == p_limpio:
            if not u.get("activo", True):
                return False, "⚠️ Tu cuenta o suscripción se encuentra suspendida. Contacta al administrador.", None
            
            bodega_id = u.get("bodega_id", "")
            if bodega_id and bodega_id in db.get("bodegas", {}):
                if not db["bodegas"][bodega_id].get("activa", True):
                    return False, "⚠️ La bodega asociada a este usuario se encuentra suspendida.", None

            return True, f"¡Bienvenido/a, {u.get('nombre', '')}!", {
                "username": u.get("username"),
                "nombre": u.get("nombre"),
                "rol": u.get("rol"),
                "bodega_id": bodega_id
            }
            
    return False, "❌ Usuario o clave incorrectos.", None

def generar_excel_respaldo(bodega_id=None):
    db = cargar_db()
    movs = db.get("movimientos", [])
    if bodega_id:
        movs = [m for m in movs if m.get("bodega_id") == bodega_id]
    
    df = pd.DataFrame(movs)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not df.empty:
            df.to_excel(writer, index=False, sheet_name='Movimientos')
        else:
            pd.DataFrame({"Mensaje": ["Sin movimientos"]}).to_excel(writer, index=False, sheet_name='Movimientos')
    output.seek(0)
    return output.getvalue()