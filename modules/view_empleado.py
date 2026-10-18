import streamlit as st
from datetime import datetime
from modules.database import cargar_db, guardar_db, encolar_y_sincronizar, solo_fecha_str, fecha_actual_str
from modules.whatsapp import formatear_cop, link_whatsapp_nueva_deuda

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
        nombres_map = {f"{c['nombre']} (Cédula: {c['cedula']}) - Saldo: {formatear_cop(c.get('saldo_cop',0))}": c for c in clientes_filtrados}
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
                elif excede_limite:
                    # Registrar solicitud de sobregiro pendiente
                    db["solicitudes_sobregiro"].append({
                        "id": "sob_" + str(datetime.now().timestamp()),
                        "bodega_id": bodega_id,
                        "cliente_id": cliente_seleccionado["id"],
                        "cliente_nombre": cliente_seleccionado["nombre"],
                        "monto_solicitado": monto_compra,
                        "empleado": sesion["nombre"],
                        "fecha": fecha_actual_str(),
                        "estado": "PENDIENTE"
                    })
                    guardar_db(db)
                    st.warning("⏳ Solicitud de sobregiro enviada al Usuario Máster. Espere que el dueño autorice desde su panel para reintentar.")
                else:
                    # Actualizar saldo del cliente
                    nuevo_saldo = float(cliente_seleccionado.get("saldo_cop", 0)) + float(monto_compra)
                    cliente_seleccionado["saldo_cop"] = nuevo_saldo
                    if not cliente_seleccionado.get("fecha_deuda_activa"):
                        cliente_seleccionado["fecha_deuda_activa"] = solo_fecha_str()

                    # Registrar movimiento
                    movimiento = {
                        "id": "mov_" + str(datetime.now().timestamp()),
                        "bodega_id": bodega_id,
                        "tipo": "DEUDA",
                        "cliente_id": cliente_seleccionado["id"],
                        "cliente_nombre": cliente_seleccionado["nombre"],
                        "cliente_cedula": cliente_seleccionado["cedula"],
                        "monto_cop": monto_compra,
                        "detalle": detalle_compra,
                        "usuario_registro": sesion["nombre"],
                        "fecha": fecha_actual_str(),
                        "saldo_resultante_cop": nuevo_saldo
                    }
                    db["movimientos"].append(movimiento)
                    encolar_y_sincronizar(db, bodega_id, "NUEVA_DEUDA", movimiento)

                    st.success("¡Deuda registrada y guardada exitosamente!")

                    # Generar enlace directo para WhatsApp
                    url_w = link_whatsapp_nueva_deuda(
                        nombre_bodega,
                        cliente_seleccionado["nombre"],
                        cliente_seleccionado["telefono"],
                        monto_compra,
                        nuevo_saldo,
                        detalle_compra
                    )
                    st.markdown(f"""
                        <div style="margin-top: 15px; padding: 14px; background: #D1FAE5; border-radius: 10px; text-align: center;">
                            <b>📲 ¡Comprobante listo para enviar por WhatsApp!</b><br><br>
                            <a href="{url_w}" target="_blank" style="background: #25D366; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 700; display: inline-block;">
                                Enviar Comprobante al Cliente 🚀
                            </a>
                        </div>
                    """, unsafe_allow_html=True)