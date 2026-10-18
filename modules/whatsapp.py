import urllib.parse
from datetime import datetime

def formatear_cop(monto):
    """Formatea cualquier número al estándar de Pesos Colombianos: $ 50.000 COP"""
    try:
        valor = int(round(float(monto)))
        return f"$ {valor:,}".replace(",", ".") + " COP"
    except Exception:
        return "$ 0 COP"

def limpiar_telefono(telefono):
    """Normaliza el teléfono para el enlace oficial de WhatsApp (Venezuela +58 / Colombia +57)."""
    num = "".join(filter(str.isdigit, str(telefono)))
    if not num:
        return ""
    # Si es número venezolano escrito como 0424... -> 58424...
    if num.startswith("04") and len(num) == 11:
        num = "58" + num[1:]
    elif len(num) == 10 and num.startswith("4"):
        num = "58" + num
    # Si es número colombiano de 10 dígitos que empieza por 3 -> 573...
    elif len(num) == 10 and num.startswith("3"):
        num = "57" + num
    return num

def calcular_dias_transcurridos(fecha_iso):
    """Calcula cuántos días han pasado desde que se registró la deuda o último movimiento."""
    if not fecha_iso:
        return 0
    try:
        fecha_base = datetime.strptime(str(fecha_iso)[:10], "%Y-%m-%d").date()
        hoy = datetime.now().date()
        dias = (hoy - fecha_base).days
        return max(0, dias)
    except Exception:
        return 0

def link_whatsapp_nueva_deuda(bodega_nombre, cliente_nombre, cliente_tel, monto_compra_cop, saldo_total_cop, detalle=""):
    """Escenario 1: Notificación al cliente cuando lleva mercancía a crédito."""
    tel = limpiar_telefono(cliente_tel)
    detalle_txt = f"\n📦 *Detalle:* {detalle}" if detalle else ""
    mensaje = (
        f"Hola *{cliente_nombre}*, te saludamos de *{bodega_nombre}*.\n\n"
        f"Se ha registrado satisfactoriamente tu compra a crédito por *{formatear_cop(monto_compra_cop)}*.{detalle_txt}\n\n"
        f"📌 *Saldo total acumulado:* {formatear_cop(saldo_total_cop)}\n\n"
        f"Gracias por tu preferencia.\n"
        f"— _DiSys CuentaClara_"
    )
    return f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"

def link_whatsapp_pago(bodega_nombre, cliente_nombre, cliente_tel, monto_abonado_cop, saldo_restante_cop):
    """Escenarios 2 y 3: Notificación al procesar un Abono Parcial o un Pago Completo."""
    tel = limpiar_telefono(cliente_tel)
    if float(saldo_restante_cop) <= 0:
        # Pago Completo
        mensaje = (
            f"¡Hola *{cliente_nombre}*! Te saludamos de *{bodega_nombre}*.\n\n"
            f"✅ Confirmamos la recepción de tu pago completo por *{formatear_cop(monto_abonado_cop)}*.\n"
            f"🎉 Tu cuenta con nosotros queda totalmente al día (*$ 0 COP*).\n\n"
            f"¡Muchas gracias por tu puntualidad y confianza!\n"
            f"— _DiSys CuentaClara_"
        )
    else:
        # Abono Parcial
        mensaje = (
            f"Hola *{cliente_nombre}*, te saludamos de *{bodega_nombre}*.\n\n"
            f"✅ Hemos registrado tu abono equivalente a *{formatear_cop(monto_abonado_cop)}*.\n"
            f"📌 *Saldo restante pendiente:* {formatear_cop(saldo_restante_cop)}\n\n"
            f"¡Gracias por tu abono!\n"
            f"— _DiSys CuentaClara_"
        )
    return f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"

def link_whatsapp_cobranza_cordial(bodega_nombre, cliente_nombre, cliente_tel, saldo_total_cop, fecha_deuda):
    """Escenario 4: Botón de Cobranza Cordial en 1 clic con días transcurridos (Solo en Pesos)."""
    tel = limpiar_telefono(cliente_tel)
    dias = calcular_dias_transcurridos(fecha_deuda)
    texto_dias = "registrada el día de hoy" if dias == 0 else f"con *{dias} día(s)* transcurridos"

    mensaje = (
        f"¡Hola *{cliente_nombre}*! Te saludamos cordialmente desde *{bodega_nombre}*.\n\n"
        f"Pasamos por aquí para recordarte amablemente que a la fecha presentas un saldo pendiente acumulado de "
        f"*{formatear_cop(saldo_total_cop)}*, {texto_dias}.\n\n"
        f"Agradecemos de antemano tu valiosa colaboración para poner tu cuenta al día. "
        f"Quedamos atentos a tus comentarios. ¡Que tengas un excelente día!\n\n"
        f"— _DiSys CuentaClara_"
    )
    return f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"