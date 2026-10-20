import streamlit as st
from modules.shield import aplicar_blindaje_y_estilos, mostrar_cabecera_corporativa, obtener_logo_base64
from modules.database import autenticar_usuario, cargar_db
from modules.view_supermaster import render_super_master_view
from modules.view_master import render_master_view
from modules.view_empleado import render_empleado_view

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA Y BLINDAJE DE SEGURIDAD
# ==============================================================================
st.set_page_config(
    page_title="DiSys CuentaClara | Gestión de Créditos",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

aplicar_blindaje_y_estilos()

# Inicializar estado de sesión si no existe
if "sesion" not in st.session_state:
    st.session_state["sesion"] = None

# ==============================================================================
# PANTALLA DE LOGIN (Solo se muestra si no hay sesión activa)
# ==============================================================================
if st.session_state["sesion"] is None:
    logo_b64 = obtener_logo_base64()
    img_login_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height: 60px; object-fit: contain; margin-bottom: 12px;" alt="DiSys Logo">' if logo_b64 else ''

    st.markdown("""
    <head>
        <link rel="manifest" href="/app/static/manifest.json">
        <meta name="theme-color" content="#F9690E">
        <link rel="apple-touch-icon" href="/app/static/assets/logo.png">
    </head>
""", unsafe_allow_html=True)

    with st.form("form_login_principal"):
        username = st.text_input("Usuario de Acceso")
        password = st.text_input("Clave / PIN de Seguridad", type="password")
        recordar = st.checkbox("Recordar sesión en este dispositivo", value=True)
        submit_login = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)

        if submit_login:
            exito, mensaje, datos_sesion = autenticar_usuario(username, password)
            if exito:
                st.session_state["sesion"] = datos_sesion
                st.success(mensaje)
                st.rerun()
            else:
                st.error(mensaje)

    st.markdown("""
                <div style="margin-top: 20px; font-size: 11.5px; color: #64748B;">
                    🔒 Sesión persistente • Respaldo Cloud Drive<br>
                    Exclusivo para Cuentas por Cobrar en Bodegas
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# VISTAS INTERNAS CON SESIÓN ACTIVA Y BOTÓN DE RECARGA
# ==============================================================================
else:
    sesion = st.session_state["sesion"]
    rol = sesion["rol"]
    db = cargar_db()

    nombre_b = ""
    if sesion.get("bodega_id"):
        b_inf = db["bodegas"].get(sesion["bodega_id"], {})
        nombre_b = b_inf.get("nombre", "")

    # Cabecera corporativa según rol
    if rol == "SUPER_MASTER":
        mostrar_cabecera_corporativa("Panel Super Máster", "Administración Central", True)
    elif rol == "MASTER":
        mostrar_cabecera_corporativa("Usuario Máster", nombre_b, True)
    else:
        mostrar_cabecera_corporativa("Usuario Empleado", nombre_b, True)

    # Barra superior con Botón de Recarga de Datos y Cerrar Sesión
    col_vacio, col_recarga, col_btn = st.columns([6, 2, 2])
    with col_recarga:
        if st.button("🔄 Recargar Datos", use_container_width=True):
            st.rerun()
    with col_btn:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["sesion"] = None
            st.rerun()

    # Enrutar a la vista correspondiente
    if rol == "SUPER_MASTER":
        render_super_master_view(sesion)
    elif rol == "MASTER":
        render_master_view(sesion)
    elif rol == "EMPLEADO":
        render_empleado_view(sesion)