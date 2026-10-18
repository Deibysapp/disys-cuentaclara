import streamlit as st
from modules.database import cargar_db, guardar_db, generar_excel_respaldo, solo_fecha_str

def render_super_master_view(sesion):
    db = cargar_db()
    
    st.markdown("""
        <div style="background: linear-gradient(135deg, #0A2239 0%, #13385C 100%); color: #FFFFFF; padding: 22px; border-radius: 14px; border-left: 6px solid #F9690E; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #FFFFFF; font-size: 24px;">👑 Panel de Control Super Máster</h2>
            <p style="margin: 5px 0 0 0; color: #CBD5E1; font-size: 14px;">Administración central de bodegas, suscripciones SaaS, licencias de empleados y respaldos en la nube.</p>
        </div>
    """, unsafe_allow_html=True)

    # Métricas Globales Superiores
    total_bodegas = len(db["bodegas"])
    total_activas = sum(1 for b in db["bodegas"].values() if b.get("activa", True))
    total_clientes_global = len(db["clientes"])

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f"""<div class="disys-card" style="text-align:center;">
            <div style="font-size:12px; color:#64748B; font-weight:700;">BODEGAS REGISTRADAS</div>
            <div style="font-size:26px; font-weight:900; color:#0A2239;">{total_bodegas} <span style="font-size:14px; color:#10B981;">({total_activas} Activas)</span></div>
        </div>""", unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"""<div class="disys-card" style="text-align:center;">
            <div style="font-size:12px; color:#64748B; font-weight:700;">TOTAL CARTERA CLIENTES</div>
            <div style="font-size:26px; font-weight:900; color:#F9690E;">{total_clientes_global}</div>
        </div>""", unsafe_allow_html=True)
    with col_m3:
        st.markdown(f"""<div class="disys-card" style="text-align:center;">
            <div style="font-size:12px; color:#64748B; font-weight:700;">ESTADO DE CONEXIÓN CLOUD</div>
            <div style="font-size:16px; font-weight:800; color:#10B981; margin-top:6px;">🟢 Sistema Sincronizado</div>
        </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🏪 Gestión de Bodegas", "➕ Registrar Nueva Bodega", "📊 Respaldo General (Excel)"])

    with tab1:
        st.markdown("### 📋 Listado de Bodegas Asociadas al Servicio")
        if not db["bodegas"]:
            st.info("No hay bodegas registradas todavía. Ve a la pestaña 'Registrar Nueva Bodega' para dar de alta la primera.")
        else:
            for b_id, b_info in list(db["bodegas"].items()):
                estado_txt = "🟢 Activa (Al día)" if b_info.get("activa", True) else "🔴 Suspendida (Falta de pago)"
                border_color = "#10B981" if b_info.get("activa", True) else "#EF4444"

                st.markdown(f"""
                    <div style="background: #FFFFFF; border-radius: 12px; padding: 16px; border: 1px solid #E2E8F0; border-left: 5px solid {border_color}; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0; color: #0A2239; font-size: 17px;">{b_info['nombre']}</h4>
                                <p style="margin: 3px 0; font-size: 13px; color: #64748B;">
                                    <b>Dueño/a:</b> {b_info['dueño']} | <b>Teléfono:</b> {b_info['telefono']} | <b>Gmail:</b> {b_info.get('gmail_respaldo', 'N/A')}
                                </p>
                                <p style="margin: 3px 0; font-size: 12.5px; color: #1E293B;">
                                    <b>Estado Licencia:</b> {estado_txt} | <b>Cupo Empleados Autorizados:</b> {b_info.get('max_empleados', 1)}
                                </p>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Controles rápidos de edición para cada bodega
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    nueva_activa = st.selectbox(
                        f"Estado Suscripción [{b_info['nombre']}]",
                        options=[True, False],
                        format_func=lambda x: "🟢 Activo" if x else "🔴 Suspendido (Bloqueado)",
                        index=0 if b_info.get("activa", True) else 1,
                        key=f"estado_{b_id}"
                    )
                    if nueva_activa != b_info.get("activa", True):
                        b_info["activa"] = nueva_activa
                        guardar_db(db)
                        st.success("¡Estado actualizado!")
                        st.rerun()

                with col_c2:
                    nuevo_cupo = st.number_input(
                        f"Cupo Empleados [{b_info['nombre']}]",
                        min_value=1, max_value=20, value=b_info.get("max_empleados", 1),
                        key=f"cupo_{b_id}"
                    )
                    if nuevo_cupo != b_info.get("max_empleados", 1):
                        b_info["max_empleados"] = nuevo_cupo
                        guardar_db(db)
                        st.success("¡Cupo de empleados actualizado!")
                        st.rerun()

                with col_c3:
                    # Opciones modulares de carga habilitadas
                    mods = b_info.get("modulos_carga", {"monto": True, "productos": False, "foto": False})
                    m_prod = st.checkbox("Listado de Productos", value=mods.get("productos", False), key=f"mod_prod_{b_id}")
                    m_foto = st.checkbox("Evidencia Fotográfica", value=mods.get("foto", False), key=f"mod_foto_{b_id}")
                    if m_prod != mods.get("productos", False) or m_foto != mods.get("foto", False):
                        b_info["modulos_carga"] = {"monto": True, "productos": m_prod, "foto": m_foto}
                        guardar_db(db)
                        st.success("¡Preferencias de carga actualizadas!")
                        st.rerun()

                st.markdown("<hr style='margin: 10px 0; border: 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    with tab2:
        st.markdown("### ➕ Alta de Nueva Bodega (Inquilino SaaS)")
        st.write("Registra los datos de la bodega, el correo Gmail asignado para su respaldo en Drive y crea las credenciales iniciales de su Usuario Máster.")

        with st.form("form_nueva_bodega"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                nom_bodega = st.text_input("Nombre de la Bodega (Ej. Bodega Mi Futuro)")
                dueño_bodega = st.text_input("Nombre del Dueño / Propietario")
                tel_bodega = st.text_input("Teléfono del Dueño / Bodega (WhatsApp)")
            with col_f2:
                gmail_bodega = st.text_input("Correo Gmail Asignado para Google Drive")
                user_master = st.text_input("Usuario Máster de Acceso")
                pass_master = st.text_input("Clave Inicial de Acceso Máster", type="password")

            st.markdown("<b>Opciones de Carga Permitidas para esta Bodega:</b>", unsafe_allow_html=True)
            c_prod = st.checkbox("Habilitar Listado Detallado de Productos", value=False)
            c_foto = st.checkbox("Habilitar Carga de Evidencia Fotográfica", value=False)

            submit_bodega = st.form_submit_button("Crear Bodega y Credenciales Máster", type="primary")
            if submit_bodega:
                if not nom_bodega or not user_master or not pass_master:
                    st.error("Por favor completa al menos el nombre de la bodega, el usuario y la clave.")
                else:
                    b_id = "bodega_" + str(uuid.uuid4())[:8]
                    db["bodegas"][b_id] = {
                        "id": b_id,
                        "nombre": nom_bodega,
                        "dueño": dueño_bodega,
                        "telefono": tel_bodega,
                        "gmail_respaldo": gmail_bodega,
                        "activa": True,
                        "max_empleados": 1,
                        "modulos_carga": {"monto": True, "productos": c_prod, "foto": c_foto},
                        "drive_webhook_url": ""
                    }
                    # Crear el Usuario Máster asociado
                    db["usuarios"].append({
                        "username": user_master.strip(),
                        "password": pass_master.strip(),
                        "nombre": dueño_bodega or "Dueño",
                        "rol": "MASTER",
                        "bodega_id": b_id,
                        "activo": True
                    })
                    guardar_db(db)
                    st.success(f"¡Bodega '{nom_bodega}' creada exitosamente junto con su Usuario Máster!")
                    st.rerun()

    with tab3:
        st.markdown("### 📊 Respaldo Centralizado en Excel (.xlsx)")
        st.write("Descarga un libro completo consolidado con la cartera de clientes, todas las deudas, abonos y cierres diarios de todas las bodegas del sistema.")

        excel_bytes = generar_excel_respaldo(bodega_id=None)
        st.download_button(
            label="📥 Descargar Respaldo General Consolidado (.xlsx)",
            data=excel_bytes,
            file_name=f"DiSys_CuentaClara_Respaldo_General_{solo_fecha_str()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )