import streamlit as st
import json
import pandas as pd
import io
from datetime import datetime
from supabase import create_client, Client

# ==============================================================================
# CONFIGURACIÓN DE CONEXIÓN CON SUPABASE
# ==============================================================================
def obtener_cliente_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return None

# ==============================================================================
# GESTIÓN DE DATOS (CARGAR Y GUARDAR DESDE SUPABASE)
# ==============================================================================
def cargar_db():
    """Carga la base de datos general desde Supabase. Si no existe, crea una inicial."""
    supabase = obtener_cliente_supabase()
    if not supabase:
        return _db_inicial_por_defecto()
    
    try:
        response = supabase.table("disys_config").select("data").eq("id", "db_principal").execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["data"]
        else:
            # Si la tabla está vacía, insertamos la estructura inicial
            db_inicial = _db_inicial_por_defecto()
            guardar_db(db_inicial)
            return db_inicial
    except Exception as e:
        # Fallback de emergencia si hay problema de red
        st.warning(f"Aviso de conexión con la nube: {e}. Usando estructura temporal.")
        return _db_inicial_por_defecto()

def guardar_db(db):
    """Guarda y sincroniza toda la base de datos en tiempo real en Supabase."""
    supabase = obtener_cliente_supabase()
    if not supabase:
        return False
    
    try:
        # Hacemos un upsert para actualizar o insertar el documento JSON principal
        supabase.table("disys_config").upsert({
            "id": "db_principal",
            "data": db,
            "updated_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar los datos en Supabase: {e}")
        return False

def _db_inicial_por_defecto():
    """Estructura inicial por defecto para el primer arranque."""
    return {
        "bodegas": {
            "bodega_demo": {
                "id": "bodega_demo",
                "nombre": "Bodega Demostración",
                "dueño": "Deibys Ibañes",
                "telefono": "04242954794",
                "gmail_respaldo": "ventasgeo389@gmail.com",
                "activa": True,
                "max_empleados": 5,
                "modulos_carga": {"monto": True, "productos": True, "foto": False},
                "tasas": {"usd_to_cop": 4100.0, "ves_factor": 3.0}
            }
        },
        "usuarios": [
            {
                "username": "supermaster",
                "password": "disys2026",
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
                "bodega_id": "bodega_demo",
                "activo": True
            },
            {
                "username": "empleado1",
                "password": "123",
                "nombre": "Cajero Mostrador",
                "rol": "EMPLEADO",
                "bodega_id": "bodega_demo",
                "activo": True
            }
        ],
        "clientes": [],
        "movimientos": [],
        "solicitudes_sobregiro": []
    }

# ==============================================================================
# FUNCIONES AUXILIARES Y AUTENTICACIÓN
# ==============================================================================
def autenticar_usuario(username, password):
    db = cargar_db()
    u_limpio = username.strip().lower()
    p_limpio = password.strip()

    for usr in db.get("usuarios", []):
        if usr["username"].lower() == u_limpio and usr["password"] == p_limpio:
            if not usr.get("activo", True):
                return False, "⚠️ Tu cuenta o bodega se encuentra suspendida. Contacta al administrador.", None
            
            # Verificar si la bodega asociada está activa (si es máster o empleado)
            if usr["rol"] in ["MASTER", "EMPLEADO"]:
                b_id = usr.get("bodega_id")
                bodega_info = db["bodegas"].get(b_id, {})
                if not bodega_info.get("activa", True):
                    return False, "⚠️ La bodega a la que perteneces está suspendida temporalmente.", None

            sesion_data = {
                "username": usr["username"],
                "nombre": usr["nombre"],
                "rol": usr["rol"],
                "bodega_id": usr.get("bodega_id", "")
            }
            return True, f"¡Bienvenido/a, {usr['nombre']}!", sesion_data

    return False, "❌ Usuario o clave incorrectos.", None

def solo_fecha_str():
    return datetime.now().strftime("%Y-%m-%d")

def fecha_actual_str():
    return datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

def encolar_y_sincronizar(db, bodega_id, tipo_op, payload):
    """Función de compatibilidad para webhooks y respaldos."""
    pass

def generar_excel_respaldo(bodega_id=None):
    db = cargar_db()
    movs = db.get("movimientos", [])
    if bodega_id:
        movs = [m for m in movs if m.get("bodega_id") == bodega_id]
    
    if not movs:
        df = pd.DataFrame(columns=["Fecha", "Hora", "Tipo", "Cliente", "Monto (COP)", "Registrado Por", "Detalle"])
    else:
        df = pd.DataFrame(movs)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte_Movimientos')
    return output.getvalue()