import streamlit as st
import json
import pandas as pd
from datetime import datetime
from io import BytesIO
from supabase import create_client, Client

# Inicializar cliente de Supabase usando los Secrets de Streamlit Cloud o variables locales
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets.get("https://ptsvpbuyjvczhxeicqjw.supabase.co", "")
    key = st.secrets.get("sb_publishable_-BYUl_TCRZZWkdC-9R6NiA_wt7uMOBe", "")
    if not url or not key:
        # Valores por defecto de respaldo si estás probando en local sin secrets.toml
        url = "https://ptsvpbuyjvczhxeicqjw.supabase.co"
        key = "sb_publishable_-BYUl_TCRZZWkdC-9R6NiA_wt7uMOBe"
    return create_client(url, key)

SUPABASE_REGISTRO_ID = "base_datos_global"

def cargar_db():
    """Carga toda la base de datos estructurada desde Supabase."""
    try:
        supabase = init_supabase()
        response = supabase.table("disys_storage").select("data").eq("id", SUPABASE_REGISTRO_ID).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["data"]
        else:
            # Estructura inicial por defecto si la tabla está vacía
            db_inicial = {
                "bodegas": {},
                "usuarios": [],
                "clientes": [],
                "movimientos": [],
                "solicitudes_sobregiro": []
            }
            guardar_db(db_inicial)
            return db_inicial
    except Exception as e:
        st.error(f"Error al conectar con la base de datos en la nube: {e}")
        return {
            "bodegas": {},
            "usuarios": [],
            "clientes": [],
            "movimientos": [],
            "solicitudes_sobregiro": []
        }

def guardar_db(db):
    """Guarda y sincroniza toda la base de datos en tiempo real en Supabase."""
    try:
        supabase = init_supabase()
        payload = {
            "id": SUPABASE_REGISTRO_ID,
            "data": db,
            "updated_at": datetime.now().isoformat()
        }
        # Upsert: Inserta o actualiza el registro global en la nube
        supabase.table("disys_storage").upsert(payload).execute()
    except Exception as e:
        st.error(f"Error al guardar datos en la nube: {e}")

def encolar_y_sincronizar(db, bodega_id, tipo_evento, detalle):
    """Función de compatibilidad para eventos en tiempo real."""
    guardar_db(db)

def fecha_actual_str():
    return datetime.now().strftime("%d/%m/%Y")

def solo_fecha_str():
    return datetime.now().strftime("%Y-%m-%d")

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