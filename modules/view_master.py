import streamlit as st
from datetime import datetime
from modules.database import cargar_db, guardar_db, encolar_y_sincronizar, fecha_actual_str, solo_fecha_str, generar_excel_respaldo
from modules.whatsapp import (
    formatear_cop,
    link_whatsapp_pago,
    link_whatsapp_cobranza_cordial,
    link_whatsapp_nueva_deuda,
    link_whatsapp_detalle_deuda
)

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
        bodega_info["tasas"] = {"usd_to_cop": 4100.0, "ves_factor": 3.0}
        guardar_db(db)

    clientes_b = [c for c in db["clientes"] if c["bodega_id"] == bodega_id]

    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "💰 Tasas y Caja", 
        "👥 Clientes y Deudas", 
        "📥 Cobranza y Pagos", 
        "👨‍💼 Empleados", 
        "⚠️ Sobregiros", 
        "🗑️ Auditoría y Corrección",
        "📊 Cierre Diario y Respaldo"
    ])

    with t1:
        st.markdown("### 💱 Tasas de Cambio del Día (Trimoneda COP/USD/VES)")
        st.write("Configura las tasas oficiales para el cálculo automático de los abonos en divisas o bolívares.")

        with st.form("form_tasas"):
            t_usd = st.number_input("Tasa Dólar (¿Cuántos Pesos COP vale 1 Dólar $?)", min_value=1.0, value=float(bodega_info["tasas"].get("usd_to_cop", 4100.0)), step=50.0)
            t_ves = st.number_input("Tasa Bolívares (Factor VES)", min_value=0.0001, value=float(bodega_info["tasas"].get("ves_factor", 3.0)), format="%.4f", step=0.001)

            if st.form_submit_button("💾 Guardar Tasas del Día", type="primary"):
                bodega_info["tasas"]["usd_to_cop"] = t_usd
                bodega_info["tasas"]["ves_factor"] = t_ves
                guardar_db(db)
                st.success("¡Tasas actualizadas correctamente!")

        st.markdown("<br>", unsafe_allow_html=True)
        total_calle = sum(c.get("saldo_cop", 0) for c in clientes_b)
        st.markdown(f"""
            <div style="background: #FFF7ED; border: 1px solid #FFEDD5; padding: 16px; border-radius: 10px;">
                <h4 style="margin: 0 0 8px 0; color: #0A2239;">📈 Resumen General de Cartera</h4>
                <p style="margin: 0; font-size: 16px;">Total Dinero en la Calle (Deudas Activas): <b style="color: #F9690E; font-size: 20px;">{formatear_cop(total_calle)}</b></p>
            </div>
        """, unsafe_allow_html=True)

    with t2:
        st.markdown("### 👥 Cartera de Clientes y Vaciado de Cuaderno")
        with st.form("form_nuevo_cliente"):
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
                    ahora_dt = datetime.now()
                    c_id = "cli_" + str(ahora_dt.timestamp())
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
                            "id": "mov_ini_" + str(ahora_dt.timestamp()),
                            "bodega_id": bodega_id,
                            "tipo": "SALDO_INICIAL",
                            "cliente_id": c_id,
                            "cliente_nombre": n_nombre,
                            "cliente_cedula": n_cedula,
                            "monto_cop": n_deuda_inicial,
                            "detalle": "Traspaso inicial de saldo desde cuaderno físico",
                            "usuario_registro": sesion["nombre"],
                            "fecha": solo_fecha_str(),
                            "hora": ahora_dt.strftime("%I:%M %p"),
                            "saldo_resultante_cop": n_deuda_inicial
                        })
                    guardar_db(db)
                    st.success(f"¡Cliente '{n_nombre}' registrado con éxito!")
                    st.rerun()

        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        st.markdown("### 📋 Listado de Clientes y Detalle por WhatsApp")
        if not clientes_b:
            st.info("No hay clientes registrados en esta bodega.")
        else:
            for cli in clientes_b:
                s_actual = cli.get("saldo_cop", 0)
                movs_cli = [m for m in db.get("movimientos", []) if m.get("cliente_id"] == cli["id"] and m.get("bodega_id"] == bodega_id]
                url_cordial = link_whatsapp_cobranza_cordial(nombre_bodega, cli["nombre"], cli["telefono"], s_actual, cli.get("fecha_deuda_activa", ""))
                url_detalle = link_whatsapp_detalle_deuda(nombre_bodega, cli, movs_cli)

                color_deuda = "#EF4444" if s_actual > 0 else "#10B981"
                st.markdown(f"""
                    <div style="background: white; padding: 14px 18px; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 8px;">
                        <b>{cli['nombre']}</b> (Cédula: {cli['cedula']})<br>
                        <span style="font-size: 13px; color: #64748B;">Tel: {cli['telefono']}</span><br>
                        <span style="font-size: 15px; font-weight: 800; color: {color_deuda};">Deuda Actual: {formatear_cop(s_actual)}</span>
                    </div>
                """, unsafe_allow_html=True)
                if s_actual > 0:
                    st.markdown(f"""
                        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 8px;">
                            <a href="{url_cordial}" target="_blank" style="background: #25D366; color: white; padding: 8px 14px; border-radius: 6px; text-decoration: none; font-size: 12.5px; font-weight: 700; display: inline-block;">📲 Cobranza Cordial WhatsApp</a>
                            <a href="{url_detalle}" target="_blank" style="background: #0A2239; color: white; padding: 8px 14px; border-radius: 6px; text-decoration: none; font-size: 12.5px; font-weight: 700; display: inline-block;">📋 Enviar Detalle de Deuda por WhatsApp</a>
                        </div>
                    """, unsafe_allow_html=True)

    with t3:
        st.markdown("### 📥 Módulo de Cobranza y Pagos Trimoneda")
        if "ultimo_recibo_wa" in st.session_state and st.session_state["ultimo_recibo_wa"]:
            rec = st.session_state["ultimo_recibo_wa"]
            es_cero = float(rec["saldo_restante"]) <= 0
            titulo_rec = "🎉 ¡Pago Completo Recibido! (Cero Deuda)" if es_cero else "✅ ¡Abono Efectivo Registrado!"
            texto_rec = f"Cliente <b>{rec['cliente_nombre']}</b> pagó <b>{formatear_cop(rec['monto_cop'])}</b>."
            texto_boton = f"📲 Enviar Comprobante WhatsApp a {rec['cliente_nombre']}"

            st.markdown(f"""
                <div style="background: #ECFDF5; border: 2px solid #10B981; padding: 16px; border-radius: 10px; margin-bottom: 18px;">
                    <h4 style="margin: 0 0 6px 0; color: #065F46;">{titulo_rec}</h4>
                    <p style="margin: 0 0 12px 0; font-size: 14px; color: #047857;">{texto_rec}</p>
                    <a href="{rec['url_wa']}" target="_blank" style="background: #25D366; color: white; padding: 10px 18px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 800; display: inline-block;">{texto_boton}</a>
                </div>
            """, unsafe_allow_html=True)
            if st.button("✖️ Limpiar aviso", key="limpiar_rec_wa"):
                st.session_state["ultimo_recibo_wa"] = None
                st.rerun()

        clientes_con_deuda = [c for c in clientes_b if c.get("saldo_cop", 0) > 0]
        if not clientes_con_deuda:
            st.success("🎉 ¡No hay deudas pendientes en este momento!")
        else:
            map_deudores = {f"{c['nombre']} | Deuda: {formatear_cop(c.get('saldo_cop', 0))}": c for c in clientes_con_deuda}
            op_sel = st.selectbox("Seleccione al Cliente que realiza el Pago", options=list(map_deudores.keys()), key="select_cliente_cobro")
            cliente_pagador = map_deudores[op_sel]

            deuda_actual = float(cliente_pagador.get("saldo_cop", 0))
            tasa_usd = float(bodega_info["tasas"].get("usd_to_cop", 4100.0))
            tasa_ves = float(bodega_info["tasas"].get("ves_factor", 3.0))

            # Ecuaciones de conversión (De Pesos a Divisa/Bolívares se DIVIDE)
            sug_usd = deuda_actual / tasa_usd if tasa_usd > 0 else 0
            sug_ves = deuda_actual / tasa_ves if tasa_ves > 0 else 0

            # Selección de moneda y modalidad fuera de formulario para visualización inmediata
            moneda_recibida = st.selectbox("Moneda Recibida", options=["Pesos Colombianos (COP)", "Dólares Americanos (USD)", "Bolívares (VES)"], key="select_moneda_pago")
            tipo_pago = st.radio("Seleccione Modalidad", options=["Abono Parcial", "Pago Completo (Cancela toda la deuda)"], key="radio_tipo_pago")

            # Mostrar la línea sugerida exactamente como lo pediste
            if "Dólares" in moneda_recibida:
                st.markdown(f"""
                    <div style="background: #EFF6FF; border: 2px solid #3B82F6; padding: 14px 16px; border-radius: 10px; margin: 10px 0; color: #1E3A8A;">
                        <b>💵 Cálculo en Dólares:</b> La deuda de {formatear_cop(deuda_actual)} equivale a <b style="font-size: 18px; color: #1D4ED8;">${sug_usd:,.2f} USD</b> (Tasa: {tasa_usd:,.2f} COP).
                    </div>
                """, unsafe_allow_html=True)
                sufijo_monto = "USD ($)"
                default_monto = sug_usd if "Completo" in tipo_pago else 0.0
            elif "Bolívares" in moneda_recibida:
                st.markdown(f"""
                    <div style="background: #F0FDF4; border: 2px solid #22C55E; padding: 14px 16px; border-radius: 10px; margin: 10px 0; color: #14532D;">
                        <b>🇻🇪 Cálculo en Bolívares:</b> La deuda de {formatear_cop(deuda_actual)} equivale a <b style="font-size: 18px; color: #15803D;">{sug_ves:,.2f} Bs</b> (Factor: {tasa_ves:,.2f}).
                    </div>
                """, unsafe_allow_html=True)
                sufijo_monto = "Bs"
                default_monto = sug_ves if "Completo" in tipo_pago else 0.0
            else:
                st.markdown(f"""
                    <div style="background: #FFF7ED; border: 2px solid #F97316; padding: 14px 16px; border-radius: 10px; margin: 10px 0; color: #7C2D12;">
                        <b>🇨🇴 Monto en Pesos:</b> Deuda actual de <b style="font-size: 18px; color: #C2410C;">{formatear_cop(deuda_actual)}</b>.
                    </div>
                """, unsafe_allow_html=True)
                sufijo_monto = "COP ($)"
                default_monto = deuda_actual if "Completo" in tipo_pago else 0.0

            with st.form("form_procesar_pago_trin"):
                monto_entregado = st.number_input(f"Monto entregado por el cliente en {sufijo_monto}", min_value=0.0, value=float(default_monto), step=1.0)
                nota_pago = st.text_input("Nota o Referencia bancaria (Opcional)")

                if st.form_submit_button("✅ Procesar Pago y Generar Comprobante WhatsApp", type="primary"):
                    if "Completo" in tipo_pago:
                        descuento_cop = deuda_actual
                        tasa_usada = tasa_usd if "Dólares" in moneda_recibida else (tasa_ves if "Bolívares" in moneda_recibida else 1.0)
                        monto_orig = sug_usd if "Dólares" in moneda_recibida else (sug_ves if "Bolívares" in moneda_recibida else deuda_actual)
                    else:
                        if monto_entregado <= 0:
                            st.error("⚠️ Ingrese un monto mayor a 0 para el abono.")
                            st.stop()
                        
                        if "Pesos" in moneda_recibida:
                            descuento_cop = monto_entregado
                            tasa_usada = 1.0
                            monto_orig = monto_entregado
                        elif "Dólares" in moneda_recibida:
                            # De Dólares a Pesos se MULTIPLICA
                            descuento_cop = monto_entregado * tasa_usd
                            tasa_usada = tasa_usd
                            monto_orig = monto_entregado
                        else:
                            # De Bolívares a Pesos se MULTIPLICA (Ej: 20000 Bs * 3 = 60000 Pesos)
                            descuento_cop = monto_entregado * tasa_ves
                            tasa_usada = tasa_ves
                            monto_orig = monto_entregado

                    nuevo_saldo = max(0.0, deuda_actual - descuento_cop)
                    cliente_pagador["saldo_cop"] = nuevo_saldo
                    if nuevo_saldo == 0:
                        cliente_pagador["fecha_deuda_activa"] = ""

                    ahora_dt = datetime.now()
                    fecha_str = solo_fecha_str()
                    hora_str = ahora_dt.strftime("%I:%M %p")
                    fh_completa = f"{fecha_str} {hora_str}"

                    mov_pago = {
                        "id": "pag_" + str(ahora_dt.timestamp()),
                        "bodega_id": bodega_id,
                        "tipo": "PAGO",
                        "cliente_id": cliente_pagador["id"],
                        "cliente_nombre": cliente_pagador["nombre"],
                        "monto_cop": descuento_cop,
                        "moneda_pago": moneda_recibida,
                        "monto_moneda_original": monto_orig,
                        "tasa_aplicada": tasa_usada,
                        "detalle": nota_pago or ("Pago completo (Cero deuda)" if nuevo_saldo == 0 else "Abono a cuenta"),
                        "usuario_registro": sesion["nombre"],
                        "fecha": fecha_str,
                        "hora": hora_str,
                        "saldo_resultante_cop": nuevo_saldo
                    }
                    db["movimientos"].append(mov_pago)
                    guardar_db(db)

                    url_wa_pago = link_whatsapp_pago(
                        nombre_bodega=nombre_bodega,
                        cliente_nombre=cliente_pagador["nombre"],
                        telefono=cliente_pagador.get("telefono", ""),
                        monto_cop=descuento_cop,
                        saldo_restante=nuevo_saldo,
                        moneda_recibida=moneda_recibida,
                        monto_original=monto_orig,
                        fecha_hora=fh_completa
                    )

                    st.session_state["ultimo_recibo_wa"] = {
                        "cliente_nombre": cliente_pagador["nombre"],
                        "monto_cop": descuento_cop,
                        "saldo_restante": nuevo_saldo,
                        "url_wa": url_wa_pago
                    }
                    st.success("¡Pago procesado con éxito!")
                    st.rerun()

    with t4:
        st.markdown("### 👨‍💼 Gestión de Empleados")
        empleados_b = [u for u in db["usuarios"] if u["bodega_id"] == bodega_id and u["rol"] == "EMPLEADO"]
        max_cupos = bodega_info.get("max_empleados", 20)
        st.info(f"Licencias utilizadas: {len(empleados_b)} de {max_cupos}")
        if len(empleados_b) < max_cupos:
            with st.form("form_crear_emp"):
                e_nom = st.text_input("Nombre del Empleado")
                e_user = st.text_input("Usuario")
                e_pass = st.text_input("Clave", type="password")
                if st.form_submit_button("Crear Empleado", type="primary"):
                    if not e_nom or not e_user or not e_pass:
                        st.error("Todos los campos son obligatorios.")
                    else:
                        db["usuarios"].append({
                            "username": e_user.strip(),
                            "password": e_pass.strip(),
                            "nombre": e_nom.strip(),
                            "rol": "EMPLEADO",
                            "bodega_id": bodega_id,
                            "activo": True
                        })
                        guardar_db(db)
                        st.success("¡Empleado creado con éxito!")
                        st.rerun()

    with t5:
        st.markdown("### ⚠️ Solicitudes de Sobregiro")
        sobregiros_b = [s for s in db.get("solicitudes_sobregiro", []) if s["bodega_id"] == bodega_id and s["estado"] == "PENDIENTE"]
        if not sobregiros_b:
            st.info("No hay solicitudes pendientes.")
        else:
            for sob in sobregiros_b:
                emp_solicita = sob.get("empleado", sob.get("usuario_registro", "Empleado"))
                st.write(f"**Cliente:** {sob['cliente_nombre']} | **Monto:** {formatear_cop(sob['monto_solicitado'])} | **Empleado:** {emp_solicita}")
                if st.button(f"✅ Aprobar {sob['cliente_nombre']}", key=f"ap_{sob['id']}", type="primary"):
                    ahora_dt = datetime.now()
                    for cli in db["clientes"]:
                        if cli["id"] == sob["cliente_id"]:
                            nuevo_s = float(cli.get("saldo_cop", 0)) + float(sob["monto_solicitado"])
                            cli["saldo_cop"] = nuevo_s
                            if not cli.get("fecha_deuda_activa"):
                                cli["fecha_deuda_activa"] = solo_fecha_str()
                            db["movimientos"].append({
                                "id": "mov_sob_" + str(ahora_dt.timestamp()),
                                "bodega_id": bodega_id,
                                "tipo": "DEUDA",
                                "cliente_id": cli["id"],
                                "cliente_nombre": cli["nombre"],
                                "cliente_cedula": cli.get("cedula", ""),
                                "monto_cop": float(sob["monto_solicitado"]),
                                "detalle": sob.get("detalle", "Compra autorizada por sobregiro"),
                                "usuario_registro": emp_solicita,
                                "fecha": solo_fecha_str(),
                                "hora": ahora_dt.strftime("%I:%M %p"),
                                "saldo_resultante_cop": nuevo_s
                            })
                    sob["estado"] = "APROBADO"
                    guardar_db(db)
                    st.success("¡Aprobado!")
                    st.rerun()

    with t6:
        st.markdown("### 🗑️ Auditoría y Corrección de Deudas (Exclusivo Dueño)")
        st.write("Si un empleado cargó mal una deuda, aquí puedes eliminar o corregir el registro reportado, ajustando automáticamente el saldo del cliente.")

        movs_deudas = [m for m in db.get("movimientos", []) if m["bodega_id"] == bodega_id and m.get("tipo") in ["DEUDA", "SALDO_INICIAL"]]
        if not movs_deudas:
            st.info("No hay registros de deudas cargadas para auditar.")
        else:
            map_movs = {f"[{m.get('fecha')} {m.get('hora')}] Cliente: {m.get('cliente_nombre')} - Monto: {formatear_cop(m.get('monto_cop'))} (Cargado por: {m.get('usuario_registro')})": m for m in movs_deudas}
            mov_sel_key = st.selectbox("Seleccione la deuda reportada como errónea para eliminar", options=list(map_movs.keys()))
            mov_a_borrar = map_movs[mov_sel_key]

            if st.button("🗑️ Eliminar Deuda Errónea y Reajustar Saldo", type="primary"):
                c_id_afectado = mov_a_borrar.get("cliente_id")
                monto_mal = float(mov_a_borrar.get("monto_cop", 0))

                for cli in db["clientes"]:
                    if cli["id"] == c_id_afectado:
                        saldo_actual_cli = float(cli.get("saldo_cop", 0))
                        cli["saldo_cop"] = max(0.0, saldo_actual_cli - monto_mal)
                        if cli["saldo_cop"] == 0:
                            cli["fecha_deuda_activa"] = ""

                db["movimientos"] = [m for m in db["movimientos"] if m.get("id") != mov_a_borrar.get("id")]
                guardar_db(db)
                st.success("¡Deuda errónea eliminada y saldo del cliente reajustado con éxito!")
                st.rerun()

    with t7:
        st.markdown("### 📊 Cierre Diario y Respaldo")
        hoy_str = solo_fecha_str()
        movs_hoy = [m for m in db["movimientos"] if m["bodega_id"] == bodega_id and hoy_str in m.get("fecha", "")]
        fiados_hoy = sum(m["monto_cop"] for m in movs_hoy if m["tipo"] in ["DEUDA", "SALDO_INICIAL"])
        pagos_hoy = sum(m["monto_cop"] for m in movs_hoy if m["tipo"] == "PAGO")
        total_calle = sum(c.get("saldo_cop", 0) for c in clientes_b)

        st.metric("Total en la Calle", formatear_cop(total_calle))
        st.metric("Fiado Hoy", formatear_cop(fiados_hoy))
        st.metric("Recuperado Hoy", formatear_cop(pagos_hoy))

        excel_b_bytes = generar_excel_respaldo(bodega_id=bodega_id)
        st.download_button(
            "📥 Descargar Respaldo Excel",
            data=excel_b_bytes,
            file_name=f"Respaldo_{nombre_bodega}_{solo_fecha_str()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )