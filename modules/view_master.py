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

    # Inicializar tasas en bodega si no existen
    if "tasas" not in bodega_info:
        bodega_info["tasas"] = {"usd_to_cop": 4100.0, "ves_factor": 1.0}
        guardar_db(db)

    # Pestañas principales del Dueño
    t1, t2, t3, t4, t5, t6 = st.tabs([
        "💰 Tasas y Caja", 
        "👥 Clientes y Deudas", 
        "📥 Cobranza y Pagos", 
        "👨‍💼 Empleados", 
        "⚠️ Sobregiros", 
        "📊 Cierre Diario y Respaldo"
    ])

    # --------------------------------------------------------------------------
    # PESTAÑA 1: TASAS TRIMONEDA Y CONFIGURACIÓN RÁPIDA
    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    # PESTAÑA 2: GESTIÓN DE CLIENTES Y VACIADO DE CUADERNO
    # --------------------------------------------------------------------------
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
                n_deuda_inicial = st.number_input("📓 Saldo Inicial (Vaciado de Cuaderno en COP)", min_value=0.0, value=0.0, step=5000.0, help="Si el cliente ya debía dinero en el cuaderno de papel, coloca aquí su saldo inicial acumulado para ponerlo al día.")

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
                    st.success(f"¡Cliente '{n_nombre}' registrado exitosamente con saldo inicial de {formatear_cop(n_deuda_inicial)}!")
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
                
                st.markdown(f"""
                    <div style="background: white; padding: 14px 18px; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <b>{cli['nombre']}</b> (Cédula: {cli['cedula']})<br>
                            <span style="font-size: 13px; color: #64748B;">Tel: {cli['telefono']} | {tipo_credito_txt}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 15px; font-weight: 800; color: {'#EF4444' if s_actual > 0 else '#10B981'};">
                                Deuda: {formatear_cop(s_actual)}
                            </span><br>
                            {f'<a href="{url_cordial}" target="_blank" style="background: #25D366; color: white; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 11.5px; font-weight: 700; display: inline-block; margin-top: 4px;">📲 Cobranza Cordial WhatsApp</a>' if s_actual > 0 else ''}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # PESTAÑA 3: COBRANZA Y PROCESAMIENTO DE ABONOS / PAGOS
    # --------------------------------------------------------------------------
    with t3:
        st.markdown("### 📥 Módulo Exclusivo de Cobranza (Abonos y Pagos)")
        st.write("Solo el Usuario Máster está autorizado para recibir dinero, rebajar deudas y procesar abonos parciales o pagos totales.")

        clientes_con_deuda = [c for c in clientes_b if c.get("saldo_cop", 0) > 0]

        if not clientes_con_deuda:
            st.success("🎉 ¡Excelente noticia! No hay ningún cliente con deudas pendientes en este momento.")
        else:
            map_deudores = {f"{c['nombre']} - Deuda: {formatear_cop(c.get('saldo_cop',0))}" : c for c in clientes_con_deuda}
            op_sel = st.selectbox("Seleccione al Cliente que va a Pagar", options=list(map_deudores.keys()), key="select_pagador")
            cliente_pagador = map_deudores[op_sel]

            deuda_actual = cliente_pagador.get("saldo_cop", 0)
            tasa_usd = float(bodega_info["tasas"].get("usd_to_cop", 4100.0))
            tasa_ves = float(bodega_info["tasas"].get("ves_factor", 1.0))

            eq_usd = deuda_actual / tasa_usd if tasa_usd > 0 else 0
            eq_ves = deuda_actual * tasa_ves

            st.markdown(f"""
                <div class="disys-card">
                    <b>Cliente:</b> {cliente_pagador['nombre']}<br>
                    <b>Saldo Total en Deuda (COP):</b> <span style="color: #EF4444; font-weight: 800; font-size: 16px;">{formatear_cop(deuda_actual)}</span><br>
                    <span style="font-size: 13px; color: #64748B;">Equivalentes estimados: approx. $ {eq_usd:.2f} USD | Bs {eq_ves:,.2f} VES</span>
                </div>
            """, unsafe_allow_html=True)

            with st.form("form_procesar_pago"):
                tipo_pago = st.radio("Tipo de Pago", options=["Pago Completo (Cancela toda la deuda)", "Abono Parcial"])
                moneda_recibida = st.selectbox("Moneda en la que entrega el dinero el cliente", options=["Pesos Colombianos (COP)", "Dólares Americanos (USD)", "Bolívares (VES - Pago Móvil / Punto)"])
                
                if "Completo" in tipo_pago:
                    monto_entregado = deuda_actual
                    st.info(f"Se registrará la cancelación total de la deuda: {formatear_cop(deuda_actual)}")
                else:
                    monto_entregado = st.number_input("Monto entregado por el cliente en su moneda respectiva", min_value=0.0, step=1.0, format="%.2f")

                nota_pago = st.text_input("Nota o Referencia bancaria (Opcional)", placeholder="Ej. Ref 1234 pago móvil banesco")

                if st.form_submit_button("✅ Procesar Pago y Generar WhatsApp", type="primary"):
                    if "Pesos" in moneda_recibida:
                        descuento_cop = monto_entregado
                        monto_original = monto_entregado
                        tasa_usada = 1.0
                    elif "Dólares" in moneda_recibida:
                        descuento_cop = monto_entregado * tasa_usd
                        monto_original = monto_entregado
                        tasa_usada = tasa_usd
                    else:
                        descuento_cop = monto_entregado / tasa_ves if tasa_ves > 0 else 0
                        monto_original = monto_entregado
                        tasa_usada = tasa_ves

                    if "Completo" in tipo_pago:
                        descuento_cop = deuda_actual
                        monto_original = deuda_actual

                    if descuento_cop <= 0:
                        st.error("El monto del pago debe ser mayor a cero.")
                    elif descuento_cop > deuda_actual:
                        st.warning("⚠️ El monto ingresado supera la deuda total del cliente. Ajustando al saldo pendiente.")
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