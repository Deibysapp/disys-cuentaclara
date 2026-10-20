import streamlit as st
import urllib.parse
from datetime import datetime
from modules.database import cargar_db, guardar_db, encolar_y_sincronizar, solo_fecha_str, fecha_actual_str
from modules.whatsapp import formatear_cop, link_whatsapp_nueva_deuda


def _limpiar_telefono_wa(telefono):
    """Normaliza el número telefónico para enlaces wa.me."""
    num = "".join(c for c in str(telefono or "") if c.isdigit())
    if not num:
        return ""
    if num.startswith("0"):
        num = "58" + num[1:]
    elif len(num) == 10 and num.startswith("3"):
        num = "57" + num
    elif len(num) == 10 and num.startswith("4"):
        num = "58" + num
    return num


def generar_link_wa_nueva_deuda_empleado(nombre_bodega, cliente_nombre, telefono, monto_compra, nuevo_saldo, detalle_compra, empleado_nombre, fecha_hora):
    """Genera enlace de WhatsApp al registrar un nuevo cargo indicando fecha, hora y empleado."""
    num = _limpiar_telefono_wa(telefono)
    det_txt = detalle_compra.strip() if detalle_compra and detalle_compra.strip() else "Compra a crédito en mostrador"
    mensaje = (
        f"🛒 *NUEVO CARGO A CRÉDITO - {nombre_bodega}*\n\n"
        f"Hola *{cliente_nombre}*, se ha registrado una compra en tu cuenta:\n"
        f"• *Fecha y Hora:* {fecha_hora}\n"
        f"• *Atendido por:* {empleado_nombre}\n"
        f"• *Monto de la compra:* {formatear_cop(monto_compra)}\n"
        f"• *Detalle:* {det_txt}\n\n"
        f"💰 *Saldo Total Acumulado:* *{formatear_cop(nuevo_saldo)}*\n\n"
        f"_Gracias por tu compra • DiSys CuentaClara_"
    )
    texto_encoded = urllib.parse.quote(mensaje)
    return f"https://wa.me/{num}?text={texto_encoded}"


def generar_link_wa_detalle_deuda_empleado(nombre_bodega, cliente, movimientos_cliente):
    """Genera enlace de WhatsApp con el desglose detallado de la deuda (Monto, Fecha, Hora y Empleado)."""
    num = _limpiar_telefono_wa(cliente.get("telefono", ""))
    lineas_detalle = []

    for m in movimientos_cliente:
        tipo = m.get("tipo", "DEUDA")
        fecha_str = m.get("fecha", "S/F")
        hora_str = m.get("hora", "")
        fecha_hora_mostrar = f"{fecha_str} {hora_str}".strip()
        monto = m.get("monto_cop", 0)
        operador = m.get("usuario_registro", "Mostrador")
        detalle_prod = m.get("detalle", "Compra a crédito")

        if tipo in ["DEUDA", "SALDO_INICIAL", "CARGO"]:
            etiqueta = "📓 Saldo Inicial" if tipo == "SALDO_INICIAL" else "🛒 Cargo"
            lineas_detalle.append(
                f"• *{fecha_hora_mostrar}* | {etiqueta}: *{formatear_cop(monto)}*\n"
                f"  _Detalle:_ {detalle_prod}\n"
                f"  _Cargado por:_ {operador}"
            )
        elif tipo == "PAGO":
            lineas_detalle.append(
                f"• *{fecha_hora_mostrar}* | ✅ Abono recibido: *-{formatear_cop(monto)}* _(Recibido por: {operador})_"
            )

    cuerpo_movs = "\n\n".join(lineas_detalle) if lineas_detalle else "• Sin movimientos detallados registrados."
    saldo_total = cliente.get("saldo_cop", 0)

    mensaje = (
        f"📋 *ESTADO DE CUENTA DETALLADO - {nombre_bodega}*\n"
        f"Cliente: *{cliente.get('nombre', '')}* (C.I: {cliente.get('cedula', '')})\n\n"
        f"*Historial de movimientos registrados:*\n"
        f"{cuerpo_movs}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *SALDO TOTAL PENDIENTE: {formatear_cop(saldo_total)}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Control transparente con DiSys CuentaClara_"
    )
    texto_encoded = urllib.parse.quote(mensaje)
    return f"https://wa.me/{num}?text={texto_encoded}"


def render_empleado_view(sesion):
    db = cargar_db()
    bodega_id = sesion["bodega_id"]
    bodega_info = db["bodegas"].get(bodega_id, {})
    nombre_bodega = bodega_info.get("nombre", "Bodega")
    mods_carga = bodega_info.get("modulos_carga", {"monto": True, "productos": False, "foto": False})

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0A2239 0%, #13385C 100%); color: #FFFFFF; padding: 18px 22px; border-radius: 14px; border-left: 6px solid #10B981; margin-bottom: 18px;">
            <h3 style="margin: 0; color: #FFFFFF; font-size: 20px;">🛒 Módulo de Carga • Empleado</h3>
            <p style="margin: 4px 0 0 0; color: #CBD5E1; font-size: 13.5px;">Bodega: <b>{nombre_bodega}</b> | Atiende: <b>{sesion['nombre']}</b> (Registro exclusivo de deudas)</p>
        </div>
    """, unsafe_allow_html=True)

    # Filtrar clientes de esta bodega
    clientes_bodega = [c for c in db["clientes"] if c["bodega_id"] == bodega_id]

    if not clientes_bodega:
        st.warning("⚠️ No hay clientes registrados en esta bodega. El Usuario Máster (Dueño/a) debe crear los clientes primero desde su sesión para que puedas cargarlos aquí.")
        return

    # Buscador rápido de clientes
    busqueda = st.text_input("🔍 Buscar Cliente por Nombre o Cédula", placeholder="Escribe para filtrar clientes...")
    clientes_filtrados = [
        c for c in clientes_bodega 
        if busqueda.lower() in c["nombre"].lower() or busqueda in c["cedula"]
    ] if busqueda else clientes_bodega

    cliente_seleccionado = None
    if clientes_filtrados:
        nombres_map = {f"{c['nombre']} (Cédula: {c['cedula']}) - Saldo: {formatear_cop(c.get('saldo_cop', 0))}": c for c in clientes_filtrados}
        opcion_elegida = st.selectbox("Seleccione el Cliente", options=list(nombres_map.keys()))
        cliente_seleccionado = nombres_map[opcion_elegida]
    else:
        st.info("No se encontró ningún cliente con ese nombre o cédula.")
        return

    if cliente_seleccionado:
        # Tarjeta resumen del cliente seleccionado
        es_vip = cliente_seleccionado.get("es_vip", False)
        limite = cliente_seleccionado.get("limite_cop", 0)
        saldo_actual = cliente_seleccionado.get("saldo_cop", 0)
        disponible = float("inf") if es_vip else max(0.0, float(limite) - float(saldo_actual))

        # Filtrar el historial de movimientos de este cliente
        movs_cli = [m for m in db.get("movimientos", []) if m.get("cliente_id") == cliente_seleccionado["id"] and m.get("bodega_id") == bodega_id]
        url_detalle_wa = generar_link_wa_detalle_deuda_empleado(nombre_bodega, cliente_seleccionado, movs_cli)

        st.markdown(f"""
            <div class="disys-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: #0A2239; font-size: 18px;">{cliente_seleccionado['nombre']}</h4>
                        <p style="margin: 4px 0; font-size: 13px; color: #64748B;">Cédula: <b>{cliente_seleccionado['cedula']}</b> | Teléfono: <b>{cliente_seleccionado['telefono']}</b></p>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {'#D1FAE5' if es_vip else '#FEF3C7'}; color: {'#065F46' if es_vip else '#92400E'}; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 700;">
                            {'⭐ Cliente VIP (Sin Límite)' if es_vip else f'Límite: {formatear_cop(limite)}'}
                        </span>
                    </div>
                </div>
                <hr style="margin: 10px 0; border: 0; border-top: 1px solid #E2E8F0;">
                <div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 600;">
                    <span>Deuda Actual: <span style="color: #EF4444;">{formatear_cop(saldo_actual)}</span></span>
                    <span>Crédito Disponible: <span style="color: #10B981;">{'Ilimitado' if es_vip else formatear_cop(disponible)}</span></span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Opción para enviar el detalle de la deuda por WhatsApp si el cliente lo solicita
        if saldo_actual > 0:
            st.markdown(f"""
                <div style="margin-bottom: 12px;">
                    <a href="{url_detalle_wa}" target="_blank" style="background: #0A2239; color: white; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 700; display: inline-block; border-left: 4px solid #F9690E;">
                        📋 Enviar Detalle de Deuda por WhatsApp al Cliente
                    </a>
                </div>
            """, unsafe_allow_html=True)

        with st.expander(f"👁️ Ver historial detallado de consumos y abonos ({len(movs_cli)} registros)"):
            if not movs_cli:
                st.caption("No hay movimientos registrados para este cliente todavía.")
            else:
                for m in reversed(movs_cli):
                    f_m = m.get("fecha", "")
                    h_m = m.get("hora", "")
                    fh_txt = f"{f_m} {h_m}".strip()
                    op_m = m.get("usuario_registro", "Mostrador")
                    det_m = m.get("detalle", "")
                    mon_m = formatear_cop(m.get("monto_cop", 0))
                    if m.get("tipo") == "PAGO":
                        st.markdown(f"✅ **ABONO/PAGO:** `{mon_m}` | 📅 {fh_txt} | 👤 Recibido por: **{op_m}** | _{det_m}_")
                    else:
                        st.markdown(f"🛒 **CARGO:** `{mon_m}` | 📅 {fh_txt} | 👨‍💼 Cargado por: **{op_m}** | _{det_m}_")

        # Mostrar comprobante de la última deuda cargada si existe en sesión
        if "ultimo_cargo_emp_wa" in st.session_state and st.session_state["ultimo_cargo_emp_wa"]:
            uc = st.session_state["ultimo_cargo_emp_wa"]
            if uc.get("cliente_id") == cliente_seleccionado["id"]:
                st.markdown(f"""
                    <div style="margin: 12px 0; padding: 14px; background: #D1FAE5; border: 1px solid #10B981; border-radius: 10px; text-align: center;">
                        <b style="color: #065F46;">📲 ¡Deuda registrada por {formatear_cop(uc['monto'])}! Comprobante listo para enviar:</b><br><br>
                        <a href="{uc['url_w']}" target="_blank" style="background: #25D366; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 700; display: inline-block;">
                            Enviar Comprobante al Cliente por WhatsApp 🚀
                        </a>
                    </div>
                """, unsafe_allow_html=True)

        # Formulario para registrar la deuda
        with st.form("form_cargar_deuda_empleado"):
            st.markdown("<b>Registrar Compra a Crédito (En Pesos - COP)</b>", unsafe_allow_html=True)
            monto_compra = st.number_input("Monto de la Compra en Pesos (COP)", min_value=0.0, step=1000.0, format="%.2f")

            detalle_compra = ""
            if mods_carga.get("productos", False):
                detalle_compra = st.text_area("Listado Detallado de Productos (Opcional)", placeholder="Ej. 2 Harinas P.A.N, 1 Harina La Rosa, 1 Refresco 2L")
            else:
                detalle_compra = st.text_input("Nota o Breve Descripción (Opcional)", placeholder="Ej. Compras de víveres para la casa")

            # Validar límite de crédito
            excede_limite = False
            if not es_vip and monto_compra > disponible:
                excede_limite = True

            if excede_limite:
                st.markdown("""
                    <div style="background-color: #FEF2F2; border: 1.5px solid #EF4444; color: #991B1B; padding: 12px; border-radius: 10px; margin-bottom: 12px; font-size: 13.5px;">
                        ⚠️ <b>ATENCIÓN:</b> Este monto supera el límite de crédito disponible del cliente.<br>
                        Para procesar la venta, debes solicitar la autorización de excepción al Dueño (Usuario Máster).
                    </div>
                """, unsafe_allow_html=True)
                btn_enviar = st.form_submit_button("🔒 Solicitar Autorización de Sobregiro al Dueño", type="primary")
            else:
                btn_enviar = st.form_submit_button("✅ Registrar Deuda y Enviar WhatsApp", type="primary")

           if btn_enviar:
                if monto_compra <= 0:
                    st.error("El monto de la compra debe ser mayor a cero.")
                else:
                    # 🚀 DEFINIMOS LAS VARIABLES DE TIEMPO AQUÍ ARRIBA PARA QUE ESTÉN DISPONIBLES SIEMPRE
                    ahora_dt = datetime.now()
                    fecha_str = solo_fecha_str()
                    hora_str = ahora_dt.strftime("%I:%M %p")
                    fh_completa = f"{fecha_str} {hora_str}"

                    if excede_limite:
                        # Registrar solicitud de sobregiro pendiente
                        db["solicitudes_sobregiro"].append({
                            "id": "sob_" + str(ahora_dt.timestamp()),
                            "bodega_id": bodega_id,
                            "cliente_id": cliente_seleccionado["id"],
                            "cliente_nombre": cliente_seleccionado["nombre"],
                            "monto_solicitado": monto_compra,
                            "detalle": detalle_compra or "Compra en mostrador",
                            "empleado": sesion["nombre"],
                            "empleado_nombre": sesion["nombre"],
                            "usuario_registro": sesion["nombre"],
                            "fecha": fecha_str,  # <--- Ahora sí la encuentra perfectamente
                            "hora": hora_str,
                            "estado": "PENDIENTE"
                        })
                        guardar_db(db)
                        st.warning("⏳ Solicitud de sobregiro enviada al Usuario Máster. Espere que el dueño autorice desde su panel para continuar.")
                    else:
                        # Actualizar saldo del cliente para venta normal
                        nuevo_saldo = float(cliente_seleccionado.get("saldo_cop", 0)) + float(monto_compra)
                        cliente_seleccionado["saldo_cop"] = nuevo_saldo
                        if not cliente_seleccionado.get("fecha_deuda_activa"):
                            cliente_seleccionado["fecha_deuda_activa"] = fecha_str

                        movimiento = {
                            "id": "mov_" + str(ahora_dt.timestamp()),
                            "bodega_id": bodega_id,
                            "tipo": "DEUDA",
                            "cliente_id": cliente_seleccionado["id"],
                            "cliente_nombre": cliente_seleccionado["nombre"],
                            "cliente_cedula": cliente_seleccionado["cedula"],
                            "monto_cop": monto_compra,
                            "detalle": detalle_compra or "Compra a crédito en mostrador",
                            "usuario_registro": sesion["nombre"],
                            "fecha": fecha_str,
                            "hora": hora_str,
                            "saldo_resultante_cop": nuevo_saldo
                        }
                        db["movimientos"].append(movimiento)
                        encolar_y_sincronizar(db, bodega_id, "NUEVA_DEUDA", movimiento)
                        guardar_db(db)
                        
                        # (resto del código de WhatsApp y éxito...)

                # 🚀 ¡ESTA ES LA LÍNEA QUE FALTABA PARA GUARDAR EN SUPABASE!
                guardar_db(db)

                # Generar enlace directo para WhatsApp incluyendo fecha, hora y empleado
                url_w = generar_link_wa_nueva_deuda_empleado(
                    nombre_bodega=nombre_bodega,
                    cliente_nombre=cliente_seleccionado["nombre"],
                    telefono=cliente_seleccionado["telefono"],
                    monto_compra=monto_compra,
                    nuevo_saldo=nuevo_saldo,
                    detalle_compra=detalle_compra,
                    empleado_nombre=sesion["nombre"],
                    fecha_hora=fh_completa
                )

                st.session_state["ultimo_cargo_emp_wa"] = {
                    "cliente_id": cliente_seleccionado["id"],
                    "monto": monto_compra,
                    "url_w": url_w
                }

                st.success("¡Deuda registrada y guardada exitosamente!")
                st.rerun()