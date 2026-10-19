import urllib.parse

def formatear_cop(valor):
    try:
        val = float(valor)
        return f"${val:,.0f} COP".replace(",", ".")
    except Exception:
        return "$0 COP"

def limpiar_telefono(telefono):
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

def link_whatsapp_nueva_deuda(nombre_bodega, cliente_nombre, telefono, monto_compra, nuevo_saldo, detalle_compra="", empleado_nombre="Mostrador", fecha_hora=""):
    num = limpiar_telefono(telefono)
    det_txt = detalle_compra.strip() if detalle_compra and detalle_compra.strip() else "Compra a crédito en mostrador"
    fh_linea = f"• *Fecha y Hora:* {fecha_hora}\n" if fecha_hora else ""
    emp_linea = f"• *Cargado por:* {empleado_nombre}\n" if empleado_nombre else ""
    
    mensaje = (
        f"🛒 *NUEVO CARGO A CRÉDITO - {nombre_bodega}*\n\n"
        f"Hola *{cliente_nombre}*, se ha registrado una compra en tu cuenta:\n"
        f"{fh_linea}"
        f"{emp_linea}"
        f"• *Monto cargado:* {formatear_cop(monto_compra)}\n"
        f"• *Detalle:* {det_txt}\n\n"
        f"💰 *Saldo Total Acumulado:* *{formatear_cop(nuevo_saldo)}*\n\n"
        f"_Control transparente • DiSys CuentaClara_"
    )
    return f"https://wa.me/{num}?text={urllib.parse.quote(mensaje)}"

def link_whatsapp_pago(nombre_bodega, cliente_nombre, telefono, monto_cop, saldo_restante, moneda_recibida="Pesos (COP)", monto_original=0.0, fecha_hora=""):
    """Criterio 1: Mensaje de WhatsApp para Abono Parcial (con saldo restante) o Pago Completo (Cero Deuda)."""
    num = limpiar_telefono(telefono)
    fh_linea = f"• *Fecha y Hora:* {fecha_hora}\n" if fecha_hora else ""
    
    if float(saldo_restante) <= 0:
        mensaje = (
            f"✅ *PAGO COMPLETO RECIBIDO - {nombre_bodega}*\n\n"
            f"Hola *{cliente_nombre}*, confirmamos la recepción de tu pago total:\n"
            f"{fh_linea}"
            f"• *Monto acreditado:* {formatear_cop(monto_cop)}\n"
            f"• *Moneda entregada:* {moneda_recibida}\n\n"
            f"🎉 *ESTADO DE CUENTA: CERO DEUDA ($0 COP)*\n"
            f"Tu cuenta ha quedado completamente al día y en cero deuda. ¡Muchas gracias por tu pago!\n\n"
            f"_Respaldado por DiSys CuentaClara_"
        )
    else:
        mensaje = (
            f"📥 *COMPROBANTE DE ABONO EFECTIVO - {nombre_bodega}*\n\n"
            f"Hola *{cliente_nombre}*, hemos registrado tu abono en cuenta:\n"
            f"{fh_linea}"
            f"• *Abono efectivo recibido:* {formatear_cop(monto_cop)}\n"
            f"• *Moneda entregada:* {moneda_recibida}\n"
            f"• *Saldo Restante Pendiente:* *{formatear_cop(saldo_restante)}*\n\n"
            f"¡Muchas gracias por tu abono!\n"
            f"_Respaldado por DiSys CuentaClara_"
        )
    return f"https://wa.me/{num}?text={urllib.parse.quote(mensaje)}"

def link_whatsapp_cobranza_cordial(nombre_bodega, cliente_nombre, telefono, saldo_actual, fecha_deuda=""):
    num = limpiar_telefono(telefono)
    f_txt = f" (registrada desde el {fecha_deuda})" if fecha_deuda else ""
    mensaje = (
        f"👋 Hola *{cliente_nombre}*, te saludamos cordialmente de *{nombre_bodega}*.\n\n"
        f"Te escribimos para recordarte que a la fecha presentas un saldo pendiente en tu cuenta{f_txt} por un total de:\n"
        f"👉 *{formatear_cop(saldo_actual)}*\n\n"
        f"Quedamos atentos a tu abono o pago. ¡Muchas gracias por tu preferencia!\n"
        f"_Mensaje generado con DiSys CuentaClara_"
    )
    return f"https://wa.me/{num}?text={urllib.parse.quote(mensaje)}"

def link_whatsapp_detalle_deuda(nombre_bodega, cliente, movimientos_cliente):
    """Criterio 2: Envía relación detallada de la deuda con monto, fecha, hora y empleado que cargó."""
    num = limpiar_telefono(cliente.get("telefono", ""))
    lineas = []

    for m in movimientos_cliente:
        tipo = m.get("tipo", "DEUDA")
        fecha_str = m.get("fecha", "S/F")
        hora_str = m.get("hora", "")
        fh_mostrar = f"{fecha_str} {hora_str}".strip() if hora_str not in fecha_str else fecha_str
        monto = m.get("monto_cop", 0)
        empleado = m.get("usuario_registro", "Mostrador")
        detalle = m.get("detalle", "Compra a crédito")

        if tipo in ["DEUDA", "SALDO_INICIAL", "CARGO"]:
            icono = "📓 Saldo Inicial" if tipo == "SALDO_INICIAL" else "🛒 Deuda cargada"
            lineas.append(
                f"• *{fh_mostrar}* | {icono}: *{formatear_cop(monto)}*\n"
                f"  _Detalle:_ {detalle}\n"
                f"  _Cargado por:_ *{empleado}*"
            )
        elif tipo == "PAGO":
            lineas.append(
                f"• *{fh_mostrar}* | ✅ Abono efectivo: *{formatear_cop(monto)}* _(Recibido por: {empleado})_"
            )

    cuerpo = "\n\n".join(lineas) if lineas else "• Sin movimientos detallados registrados."
    saldo_total = cliente.get("saldo_cop", 0)

    mensaje = (
        f"📋 *DETALLE DE DEUDA - {nombre_bodega}*\n"
        f"Cliente: *{cliente.get('nombre', '')}* (C.I: {cliente.get('cedula', '')})\n\n"
        f"*Relación detallada de cargos y abonos:*\n"
        f"{cuerpo}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *SALDO TOTAL PENDIENTE: {formatear_cop(saldo_total)}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_DiSys CuentaClara_"
    )
    return f"https://wa.me/{num}?text={urllib.parse.quote(mensaje)}"