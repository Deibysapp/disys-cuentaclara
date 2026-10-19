import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import io

DB_LOCAL = "disys_db.json"

def inicializar_db_local():
    if not os.path.exists(DB_LOCAL):
        data_inicial = {
            "bodegas": {},
            "usuarios": [
                {
                    "username": "supermaster",
                    "password": "disys2026",
                    "nombre": "Super Administrador",
                    "rol": "SUPER_MASTER",
                    "bodega_id": "",
                    "activo": True
                }
            ],
            "clientes": [],
            "movimientos": [],
            "solicitudes_sobregiro": []
        }
        with open(DB_LOCAL, "w", encoding="utf-8") as f:
            json.dump(data_inicial, f, ensure_ascii=False, indent=4)

inicializar_db_local()

def cargar_db():
    try:
        with open(DB_LOCAL, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        inicializar_db_local()
        with open(DB_LOCAL, "r", encoding="utf-8") as f:
            return json.load(f)

def guardar_db(data):
    with open(DB_LOCAL, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def autenticar_usuario(username, password):
    db = cargar_db()
    for u in db.get("usuarios", []):
        if u["username"].strip() == username.strip() and u["password"].strip() == password.strip():
            if u.get("activo", True):
                datos_sesion = {
                    "nombre": u["nombre"],
                    "rol": u["rol"],
                    "bodega_id": u["bodega_id"],
                    "username": u["username"]
                }
                return True, "Ingreso exitoso", datos_sesion
            else:
                return False, "El usuario se encuentra inactivo.", None
    return False, "Usuario o contraseña incorrectos.", None

def fecha_actual_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def solo_fecha_str():
    return datetime.now().strftime("%Y-%m-%d")

def generar_excel_respaldo(bodega_id):
    db = cargar_db()
    movs = [m for m in db.get("movimientos", []) if m["bodega_id"] == bodega_id or bodega_id == "global"]
    clientes = [c for c in db.get("clientes", []) if c["bodega_id"] == bodega_id or bodega_id == "global"]
    
    df_movs = pd.DataFrame(movs) if movs else pd.DataFrame([{"Mensaje": "Sin movimientos registrados"}])
    df_cli = pd.DataFrame(clientes) if clientes else pd.DataFrame([{"Mensaje": "Sin clientes registrados"}])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_movs.to_excel(writer, sheet_name='Movimientos', index=False)
        df_cli.to_excel(writer, sheet_name='Clientes', index=False)
    return output.getvalue()