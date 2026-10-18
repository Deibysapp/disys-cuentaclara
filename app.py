import streamlit as st
from modules.shield import aplicar_blindaje_y_estilos, mostrar_cabecera_corporativa
from modules.database import autenticar_usuario, cargar_db
from modules.view_supermaster import render_super_master_view
from modules.view_master import render_master_view
from modules.view_empleado import render_empleado_view

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA Y APLICACIÓN DE BLINDAJE DE SEGURIDAD
# ==============================================================================
st.set_page_config(
    page_title="DiSys CuentaClara | Gestión de Créditos",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Aplicar ocultamiento de GitHub/Streamlit y bloqueo de clic derecho/F12
aplicar_blindaje_y_estilos()

# Inicializar estado de sesión si no existe
if "sesion" not in st.session_state:
    st.session_state["sesion"] = None

# ==============================================================================
# PANTALLA DE LOGIN SI NO HAY SESIÓN ACTIVA
# ==============================================================================
if st.session_state["sesion"] is None:
    logo_b64 = obtener_logo_base64()
    if logo_b64:
        img_login_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height: 60px; object-fit: contain; margin-bottom: 12px;" alt="DiSys Logo">'
    else:
        img_login_tag = ''

    st.markdown(f"""
        <div style="min-height: 80vh; display: flex; align-items: center; justify-content: center;">
            <div class="disys-card" style="width: 100%; max-width: 420px; text-align: center; border-top: 6px solid #F9690E; padding: 32px;">
                {img_login_tag}
                <h2 style="color: #0A2239; margin-bottom: 5px;">DiSys CuentaClara</h2>
                <p style="color: #F9690E; font-weight: 700; font-size: 13px; margin-bottom: 24px; text-transform: uppercase;">Tecnología para la distribución eficiente</p>
    """, unsafe_allow_html=True)

    with st.form("form_login_principal"):
        username = st.text_input("Usuario de Acceso")
        password = st.text_input("Clave / PIN de Seguridad", type="password")
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
                    🔒 Operación Offline-First • Respaldo Cloud Drive<br>
                    Exclusivo para Cuentas por Cobrar en Bodegas
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
# ==============================================================================
# VISTAS INTERNAS SEGÚN EL ROL DEL USUARIO AUTENTICADO
# ==============================================================================
else:
    sesion = st.session_state["sesion"]
    rol = sesion["rol"]
    db = cargar_db()

    # Obtener nombre de la bodega si aplica
    nombre_b = ""
    if sesion.get("bodega_id"):
        b_inf = db["bodegas"].get(sesion["bodega_id"], {})
        nombre_b = b_inf.get("nombre", "")

    # Barra superior corporativa fija con logo DiSys y semáforo de sincronización
    if rol == "SUPER_MASTER":
        mostrar_cabecera_corporativa("Panel Super Máster", "Administración Central", True)
    elif rol == "MASTER":
        mostrar_cabecera_corporativa("Usuario Máster", nombre_b, True)
    else:
        mostrar_cabecera_corporativa("Usuario Empleado", nombre_b, True)

    # Botón flotante superior para Cerrar Sesión
    col_vacio, col_btn = st.columns([8, 2])
    with col_btn:
        if st.button("🚪 Cerrar Sesión"):
            st.session_state["sesion"] = None
            st.rerun()

    # Enrutar a la vista correspondiente
    if rol == "SUPER_MASTER":
        render_super_master_view(sesion)
    elif rol == "MASTER":
        render_master_view(sesion)
    elif rol == "EMPLEADO":
        render_empleado_view(sesion)