import streamlit as st
from datetime import datetime
from modules.database import cargar_db, guardar_db, encolar_y_sincronizar, fecha_actual_str, solo_fecha_str, generar_excel_respaldo
from modules.whatsapp import formatear_cop, link_whatsapp_pago, link_whatsapp_cobranza_cordial, link_whatsapp_nueva_deuda

def render_master_view(sesion):
    db = cargar_db()
    bodega_id = sesion["bodega_id"]
    bodega_info = db["bodegas"].get(bodega_id, {})
    nombre_bodega = bodega_info.get("nombre", "Bodega")

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0A2239 0%, #13385C 100%); color: #FFFFFF; padding: 20px 24px; border-radius: 14px; border-left: 6px solid #F9690E; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #FFFFFF; font-size: 22px;">🔑 Panel de Control • Usuario Máster (Dueño/a)</h2>
            <p style="margin: 4px 0 0 0; color: #CBD5E1; font-size: 13.5px;">Bodega: <b>{nombre_bodega}</b> | Administrador: <b>{sesion['nombre']}</b></p>
        </div>
    """, unsafe_allow_html=True)

    if "tasas" not in bodega_info:
        bodega_info["tasas"] = {"usd_to_cop": 4100.0, "ves_factor": 1.0}
        guardar_db(db)

    t1, t2, t3, t4, t5, t6 = st.tabs([
        "💰 Tasas y Caja", 
        "👥 Clientes y Deudas", 
        "📥 Cobranza y Pagos", 
        "👨‍💼 Empleados", 
        "⚠️ Sobregiros", 
        "📊 Cierre Diario y Respaldo"
    ])

    with t1:
        st.markdown("### 💱 Tasas de Cambio del Día (Trimoneda COP/USD/VES)")
        st.write("Fija las tasas manuales con las que el sistema calculará los equivalentes al momento de recibir dólares o bolívares por abonos de crédito.")

        with st.form("form_tasas"):
            t_usd = st.number_input("Tasa Dólar (¿Cuántos Pesos COP vale 1 Dólar $?)", min_value=1.0, value=float(bodega_info["tasas"].get("usd_to_cop", 4100.0)), step=50.0)
            t_ves = st.number_input("Tasa Bolívares (Factor VES/COP para calcular el pago móvil)", min_value=0.0001, value=float(bodega_info["tasas"].get("ves_factor", 1.0)), format="%.4f", step=0.001)

            if st.form_submit_button("💾 Guardar Tasas del Día", type="primary"):
                bodega_info["tasas"]["usd_to_cop"] = t_usd
                bodega_info["tasas"]["ves_factor"] = t_ves
                guardar_db(db)
                st.success("¡Tasas actualizadas correctamente para toda la bodega!")

        st.markdown("<br>", unsafe_allow_html=True)
        clientes_b = [c for c in db["clientes"] if c["bodega_id"] == bodega_id]
        total_calle = sum(c.get("saldo_cop", 0) for c in clientes_b)
        st.markdown(f"""
            <div class="disys-card disys-card-orange">
                <h4 style="margin: 0 0 8px 0; color: #0A2239;">📈 Resumen General de Cartera</h4>
                <p style="margin: 0; font-size: 16px;">Total Dinero en la Calle (Deudas Activas): <b style="color: #F9690E; font-size: 20px;">{formatear_cop(total_calle)}</b></p>
            </div>
        """, unsafe_allow_html=True)

    with t2:
        st.markdown("### 👥 Cartera de Clientes y Vaciado de Cuaderno")
        st.write("Aquí puedes registrar nuevos clientes, asignarles límite de crédito en pesos, marcarlos como VIP o pasar sus cuentas viejas desde el cuaderno físico.")

        with st.form("form_nuevo_cliente"):
            st.markdown("<b>Crear / Migrar Cliente desde el Cuaderno</b>", unsafe_allow_html=True)
            col_nc1, col_nc2 = st.columns(2)
            with col_nc1:
                n_nombre = st.text_input("Nombre y Apellido del Cliente")
                n_cedula = st.text_input("Cédula de Identidad")
                n_tel = st.text_input("Número de Teléfono (WhatsApp)")
            with col_nc2:
                n_es_vip = st.checkbox("⭐ Cliente VIP (Sin límite de crédito)")
                n_limite = st.number_input("Límite de Crédito en Pesos (COP)", min_value=0.0, value=50000.0, step=10000.0)
                n_deuda_inicial = st.number_input("📓 Saldo Inicial (Vaciado de Cuaderno en COP)", min_value=0.0, value=0.0, step=5000.0)

            if st.form_submit_button("➕ Guardar Cliente Autorizado", type="primary"):
                if not n_nombre or not n_cedula:
                    st.error("El nombre y la cédula son obligatorios.")
                else:
                    c_id = "cli_" + str(datetime.now().timestamp())
                    nuevo_c = {
                        "id": c_id,
                        "bodega_id": bodega_id,
                        "nombre": n_nombre,
                        "cedula": n_cedula,
                        "telefono": n_tel,
                        "es_vip": n_es_vip,
                        "limite_cop": 0.0 if n_es_vip else n_limite,
                        "saldo_cop": n_deuda_inicial,
                        "fecha_deuda_activa": solo_fecha_str() if n_deuda_inicial > 0 else ""
                    }
                    db["clientes"].append(nuevo_c)

                    if n_deuda_inicial > 0:
                        db["movimientos"].append({
                            "id": "mov_ini_" + str(datetime.now().timestamp()),
                            "bodega_id": bodega_id,
                            "tipo": "SALDO_INICIAL",
                            "cliente_id": c_id,
                            "cliente_nombre": n_nombre,
                            "cliente_cedula": n_cedula,
                            "monto_cop": n_deuda_inicial,
                            "detalle": "Traspaso inicial de saldo desde cuaderno físico",
                            "usuario_registro": sesion["nombre"],
                            "fecha": fecha_actual_str(),
                            "saldo_resultante_cop": n_deuda_inicial
                        })

                    guardar_db(db)
                    st.success(f"¡Cliente '{n_nombre}' registrado con éxito!")
                    st.rerun()

        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        st.markdown("### 📋 Listado de Clientes Registrados y Estado de Deuda")
        
        if not clientes_b:
            st.info("No hay clientes registrados en esta bodega.")
        else:
            for cli in clientes_b:
                s_actual = cli.get("saldo_cop", 0)
                url_cordial = link_whatsapp_cobranza_cordial(
                    nombre_bodega, cli["nombre"], cli["telefono"], s_actual, cli.get("fecha_deuda_activa", "")
                )
                tipo_credito_txt = "⭐ VIP" if cli.get("es_vip") else f"Límite: {formatear_cop(cli['limite_cop'])}"
                color_deuda = "#EF4444" if s_actual > 0 else "#10B981"
                
                st.markdown(f"""
                    <div style="background: white; padding: 14px 18px; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 10px;">
                        <b>{cli['nombre']}</b> (Cédula: {cli['cedula']})<br>
                        <span style="font-size: 13px; color: #64748B;">Tel: {cli['telefono']} | {tipo_credito_txt}</span><br>
                        <span style="font-size: 15px; font-weight: 800; color: {color_deuda};">Deuda: {formatear_cop(s_actual)}</span>
                    </div>
                """, unsafe_allow_html=True)
                if s_actual > 0:
                    st.markdown(f'<a href="{url_cordial}" target="_blank" style="background: #25D366; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 700; display: inline-block; margin-bottom: 10px;">📲 Cobranza Cordial WhatsApp</a>', unsafe_allow_html=True)

    with t3:
        st.markdown("### 📥 Módulo Exclusivo de Cobranza (Abonos y Pagos)")
        clientes_con_deuda = [c for c in clientes_b if c.get("saldo_cop", 0) > 0]

        if not clientes_con_deuda:
            st.success("🎉 ¡Excelente noticia! No hay deudas pendientes.")
        else:
            map_deudores = {f"{c['nombre']} - Deuda: {formatear_cop(c.get('saldo_cop',0))}" : c for c in clientes_con_deuda}
            op_sel = st.selectbox("Seleccione al Cliente que va a Pagar", options=list(map_deudores.keys()))
            cliente_pagador = map_deudores[op_sel]

            deuda_actual = cliente_pagador.get("saldo_cop", 0)
            tasa_usd = float(bodega_info["tasas"].get("usd_to_cop", 4100.0))
            tasa_ves = float(bodega_info["tasas"].get("ves_factor", 1.0))

            with st.form("form_procesar_pago"):
                tipo_pago = st.radio("Tipo de Pago", options=["Pago Completo (Cancela toda la deuda)", "Abono Parcial"])
                moneda_recibida = st.selectbox("Moneda", options=["Pesos Colombianos (COP)", "Dólares Americanos (USD)", "Bolívares (VES)"])
                
                if "Completo" in tipo_pago:
                    monto_entregado = deuda_actual
                else:
                    monto_entregado = st.number_input("Monto entregado", min_value=0.0, step=1.0)

                nota_pago = st.text_input("Nota o Referencia bancaria (Opcional)")

                if st.form_submit_button("✅ Procesar Pago", type="primary"):
                    if "Pesos" in moneda_recibida:
                        descuento_cop = monto_entregado
                        tasa_usada = 1.0
                    elif "Dólares" in moneda_recibida:
                        descuento_cop = monto_entregado * tasa_usd
                        tasa_usada = tasa_usd
                    else:
                        descuento_cop = monto_entregado / tasa_ves if tasa_ves > 0 else 0
                        tasa_usada = tasa_ves

                    if "Completo" in tipo_pago:
                        descuento_cop = deuda_actual

                    nuevo_saldo = max(0.0, deuda_actual - descuento_cop)
                    cliente_pagador["saldo_cop"] = nuevo_saldo
                    if nuevo_saldo == 0:
                        cliente_pagador["fecha_deuda_activa"] = ""

                    mov_pago = {
                        "id": "pag_" + str(datetime.now().timestamp()),
                        "bodega_id": bodega_id,
                        "tipo": "PAGO",
                        "cliente_id": cliente_pagador["id"],
                        "cliente_nombre": cliente_pagador["nombre"],
                        "monto_cop": descuento_cop,
                        "moneda_pago": moneda_recibida,
                        "monto_moneda_original": monto_entregado,
                        "tasa_aplicada": tasa_usada,
                        "detalle": nota_pago,
                        "usuario_registro": sesion["nombre"],
                        "fecha": fecha_actual_str(),
                        "saldo_resultante_cop": nuevo_saldo
                    }
                    db["movimientos"].append(mov_pago)
                    encolar_y_sincronizar(db, bodega_id, "PAGO_RECIBIDO", mov_pago)
                    st.success("¡Pago procesado con éxito!")
                    st.rerun()

    with t4:
        st.markdown("### 👨‍💼 Gestión de Empleados")
        empleados_b = [u for u in db["usuarios"] if u["bodega_id"] == bodega_id and u["rol"] == "EMPLEADO"]
        max_cupos = bodega_info.get("max_empleados", 1)
        
        st.info(f"Licencias utilizadas: {len(empleados_b)} de {max_cupos}")
        if len(empleados_b) < max_cupos:
            with st.form("form_crear_emp"):
                e_nom = st.text_input("Nombre del Empleado")
                e_user = st.text_input("Usuario")
                e_pass = st.text_input("Clave", type="password")
                if st.form_submit_button("Crear Empleado", type="primary"):
                    db["usuarios"].append({"username": e_user.strip(), "password": e_pass.strip(), "nombre": e_nom, "rol": "EMPLEADO", "bodega_id": bodega_id, "activo": True})
                    guardar_db(db)
                    st.success("¡Creado con éxito!")
                    st.rerun()

    with t5:
        st.markdown("### ⚠️ Solicitudes de Sobregiro")
        sobregiros_b = [s for s in db["solicitudes_sobregiro"] if s["bodega_id"] == bodega_id and s["estado"] == "PENDIENTE"]
        if not sobregiros_b:
            st.info("No hay solicitudes pendientes.")
        else:
            for sob in sobregiros_b:
                st.write(f"Cliente: {sob['cliente_nombre']} - Monto: {formatear_cop(sob['monto_solicitado'])}")
                if st.button(f"Aprobar {sob['id']}", key=f"ap_{sob['id']}"):
                    for cli in db["clientes"]:
                        if cli["id"] == sob["cliente_id"]:
                            cli["saldo_cop"] = float(cli.get("saldo_cop", 0)) + float(sob["monto_solicitado"])
                    sob["estado"] = "APROBADO"
                    guardar_db(db)
                    st.success("¡Aprobado!")
                    st.rerun()

    with t6:
        st.markdown("### 📊 Cierre Diario y Respaldo")
        hoy_str = solo_fecha_str()
        movs_hoy = [m for m in db["movimientos"] if m["bodega_id"] == bodega_id and hoy_str in m["fecha"]]
        fiados_hoy = sum(m["monto_cop"] for m in movs_hoy if m["tipo"] in ["DEUDA", "SALDO_INICIAL"])
        pagos_hoy = sum(m["monto_cop"] for m in movs_hoy if m["tipo"] == "PAGO")
        total_calle = sum(c.get("saldo_cop", 0) for c in clientes_b)

        st.metric("Total en la Calle", formatear_cop(total_calle))
        st.metric("Fiado Hoy", formatear_cop(fiados_hoy))
        st.metric("Recuperado Hoy", formatear_cop(pagos_hoy))

        excel_b_bytes = generar_excel_respaldo(bodega_id=bodega_id)
        st.download_button("📥 Descargar Respaldo Excel", data=excel_b_bytes, file_name=f"Respaldo_{nombre_bodega}_{solo_fecha_str()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")