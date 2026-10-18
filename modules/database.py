import json
import os
import io
import uuid
from datetime import datetime
import pandas as pd
import requests

DB_FILE = "disys_data_store.json"

def fecha_actual_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def solo_fecha_str():
    return datetime.now().strftime("%Y-%m-%d")

def estructura_inicial():
    """Estructura base del sistema con tu usuario Super Máster preconfigurado."""
    return {
        "super_master": {
            "username": "supermaster",
            "password": "disys2026",
            "email_central": "ventasgeo389@gmail.com",
            "webhook_central_url": ""
        },
        "bodegas": {},
        "usuarios": [],
        "clientes": [],
        "movimientos": [],
        "solicitudes_sobregiro": [],
        "solicitudes_cupos": [],
        "cierres_diarios": [],
        "cola_offline": []
    }

def cargar_db():
    """Carga la base de datos persistente o la inicializa si es la primera vez."""
    if not os.path.exists(DB_FILE):
        db = estructura_inicial()
        guardar_db(db)
        return db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return estructura_inicial()

def guardar_db(db):
    """Guarda los cambios inmediatamente en disco para no perder nada ante cortes de luz."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# ==============================================================================
# MOTOR DE SINCRONIZACIÓN CON GOOGLE DRIVE (APPS SCRIPT WEBHOOK) + COLA OFFLINE
# ==============================================================================
def encolar_y_sincronizar(db, bodega_id, tipo_evento, payload):
    """
    Intenta enviar el registro al Excel de Google Drive de la bodega y del Super Máster.
    Si falla el internet, lo conserva en 'cola_offline' sin perder datos.
    """
    evento = {
        "id_evento": str(uuid.uuid4())[:8],
        "fecha": fecha_actual_str(),
        "bodega_id": bodega_id,
        "tipo": tipo_evento,
        "datos": payload
    }
    db["cola_offline"].append(evento)
    guardar_db(db)
    return procesar_cola_sincronizacion(db)

def procesar_cola_sincronizacion(db):
    """Vacía la cola pendiente enviándola a Google Drive cuando hay conexión."""
    if not db.get("cola_offline"):
        return True

    bodegas = db.get("bodegas", {})
    webhook_central = db.get("super_master", {}).get("webhook_central_url", "").strip()
    pendientes = []

    for item in db["cola_offline"]:
        b_id = item.get("bodega_id")
        bodega_info = bodegas.get(b_id, {})
        webhook_bodega = bodega_info.get("drive_webhook_url", "").strip()

        # Si aún no han configurado URL de webhook en Drive, se valida localmente como exitoso
        if not webhook_bodega and not webhook_central:
            continue

        enviado = False
        paquete = {
            "bodega_id": b_id,
            "bodega_nombre": bodega_info.get("nombre", "General"),
            "gmail_bodega": bodega_info.get("gmail_respaldo", ""),
            "tipo": item["tipo"],
            "fecha": item["fecha"],
            "datos": item["datos"]
        }

        try:
            if webhook_bodega:
                r = requests.post(webhook_bodega, json=paquete, timeout=4)
                if r.status_code == 200:
                    enviado = True
            if webhook_central:
                r2 = requests.post(webhook_central, json=paquete, timeout=4)
                if r2.status_code == 200:
                    enviado = True
        except Exception:
            enviado = False

        if not enviado:
            pendientes.append(item)

    db["cola_offline"] = pendientes
    guardar_db(db)
    return len(pendientes) == 0

# ==============================================================================
# AUTENTICACIÓN Y VALIDACIÓN DE SUSCRIPCIÓN (ACTIVO / INACTIVO)
# ==============================================================================
def autenticar_usuario(username, password):
    """
    Retorna: (exito, mensaje, datos_sesion)
    Valida jerarquía: Super Máster -> Máster -> Empleado y bloqueo por falta de pago.
    """
    db = cargar_db()
    user_clean = username.strip()
    pass_clean = password.strip()

    # 1. Verificar si es Super Máster
    sm = db["super_master"]
    if user_clean.lower() == sm["username"].lower() and pass_clean == sm["password"]:
        return True, "Bienvenido Super Máster", {
            "rol": "SUPER_MASTER",
            "username": sm["username"],
            "nombre": "Administrador General DiSys",
            "bodega_id": None
        }

    # 2. Buscar en usuarios (Máster o Empleados)
    for u in db["usuarios"]:
        if u["username"].lower() == user_clean.lower() and u["password"] == pass_clean:
            bodega_id = u["bodega_id"]
            bodega = db["bodegas"].get(bodega_id)

            if not bodega:
                return False, "Error: Bodega no encontrada.", None

            # Candado de Suscripción (Inactivación desde Super Máster)
            if not bodega.get("activa", True):
                return False, (
                    f"⛔ SERVICIO SUSPENDIDO TEMPORALMENTE PARA '{bodega['nombre'].upper()}'. "
                    "Por favor contacte al Administrador de DiSys CuentaClara para renovar su mensualidad."
                ), None

            if not u.get("activo", True):
                return False, "⛔ Este usuario de empleado se encuentra desactivado por el dueño.", None

            return True, "Acceso concedido", {
                "rol": u["rol"],  # "MASTER" o "EMPLEADO"
                "username": u["username"],
                "nombre": u["nombre"],
                "bodega_id": bodega_id
            }

    return False, "Usuario o clave incorrectos. Verifique e intente de nuevo.", None

# ==============================================================================
# GENERADOR DE RESPALDO EN EXCEL (.XLSX) PARA BODEGA Y SUPER MÁSTER
# ==============================================================================
def generar_excel_respaldo(bodega_id=None):
    """
    Genera un archivo Excel (.xlsx) en memoria con 4 hojas detalladas:
    1. Cartera_Clientes
    2. Historial_Deudas
    3. Historial_Pagos
    4. Cierres_Diarios
    Si bodega_id es None, exporta absolutamente todas las bodegas (Modo Super Máster).
    """
    db = cargar_db()
    bodegas = db.get("bodegas", {})

    # Filtrar clientes
    clientes_raw = [c for c in db["clientes"] if (bodega_id is None or c["bodega_id"] == bodega_id)]
    filas_clientes = []
    for c in clientes_raw:
        b_nom = bodegas.get(c["bodega_id"], {}).get("nombre", "")
        filas_clientes.append({
            "Bodega": b_nom,
            "ID Cliente": c["id"],
            "Nombre Cliente": c["nombre"],
            "Cédula": c["cedula"],
            "Teléfono WhatsApp": c["telefono"],
            "Tipo Crédito": "VIP (Sin Límite)" if c.get("es_vip") else "Con Límite",
            "Límite Crédito (COP)": 0 if c.get("es_vip") else c.get("limite_cop", 0),
            "Saldo Deuda Actual (COP)": c.get("saldo_cop", 0),
            "Fecha Inicio Deuda Activa": c.get("fecha_deuda_activa", "")
        })

    # Filtrar movimientos (Deudas vs Pagos)
    movs_raw = [m for m in db["movimientos"] if (bodega_id is None or m["bodega_id"] == bodega_id)]
    filas_deudas = []
    filas_pagos = []

    for m in movs_raw:
        b_nom = bodegas.get(m["bodega_id"], {}).get("nombre", "")
        if m["tipo"] in ["DEUDA", "SALDO_INICIAL"]:
            filas_deudas.append({
                "Fecha y Hora": m["fecha"],
                "Bodega": b_nom,
                "Cliente": m["cliente_nombre"],
                "Cédula": m.get("cliente_cedula", ""),
                "Categoría": "Vaciado de Cuaderno" if m["tipo"] == "SALDO_INICIAL" else "Compra a Crédito",
                "Monto Cargado (COP)": m["monto_cop"],
                "Detalle / Productos": m.get("detalle", ""),
                "Registrado Por": m["usuario_registro"],
                "Saldo Resultante (COP)": m.get("saldo_resultante_cop", 0)
            })
        elif m["tipo"] == "PAGO":
            filas_pagos.append({
                "Fecha y Hora": m["fecha"],
                "Bodega": b_nom,
                "Cliente": m["cliente_nombre"],
                "Descuento en Deuda (COP)": m["monto_cop"],
                "Moneda Recibida": m.get("moneda_pago", "COP"),
                "Monto Físico/Banco Recibido": m.get("monto_moneda_original", m["monto_cop"]),
                "Tasa Aplicada": m.get("tasa_aplicada", 1),
                "Método / Nota": m.get("detalle", ""),
                "Procesado Por (Máster)": m["usuario_registro"],
                "Saldo Restante (COP)": m.get("saldo_resultante_cop", 0)
            })

    # Filtrar cierres diarios
    cierres_raw = [ci for ci in db.get("cierres_diarios", []) if (bodega_id is None or ci["bodega_id"] == bodega_id)]
    filas_cierres = []
    for ci in cierres_raw:
        b_nom = bodegas.get(ci["bodega_id"], {}).get("nombre", "")
        filas_cierres.append({
            "Fecha Cierre": ci["fecha"],
            "Bodega": b_nom,
            "Total Cartera en la Calle (COP)": ci["cartera_total_cop"],
            "Nuevos Créditos Hoy (COP)": ci["fiados_hoy_cop"],
            "Total Recuperado Hoy (COP)": ci["recuperado_hoy_cop"],
            "Recibido en Efectivo Pesos (COP)": ci["recibido_cop"],
            "Recibido en Dólares (USD)": ci["recibido_usd"],
            "Recibido en Bolívares (VES)": ci["recibido_ves"],
            "Ejecutado Por": ci["usuario"]
        })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(filas_clientes or [{"Aviso": "Sin registros"}]).to_excel(writer, index=False, sheet_name="Cartera_Clientes")
        pd.DataFrame(filas_deudas or [{"Aviso": "Sin registros"}]).to_excel(writer, index=False, sheet_name="Historial_Deudas")
        pd.DataFrame(filas_pagos or [{"Aviso": "Sin registros"}]).to_excel(writer, index=False, sheet_name="Historial_Pagos")
        pd.DataFrame(filas_cierres or [{"Aviso": "Sin registros"}]).to_excel(writer, index=False, sheet_name="Cierres_Diarios")

    return output.getvalue()