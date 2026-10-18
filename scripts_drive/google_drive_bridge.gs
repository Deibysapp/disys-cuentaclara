/**
 * DiSys CuentaClara - Puente Webhook para Google Drive y Google Sheets
 * Recibe las cargas de deudas, abonos y cierres y los escribe automáticamente en el Excel de la bodega.
 */
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    var tipo = data.tipo;
    var bodegaNombre = data.bodega_nombre || "General";
    var fecha = data.fecha;
    var payload = data.datos;
    
    var sheetName = "Historial_General";
    if (tipo === "NUEVA_DEUDA" || tipo === "SOBREGIRO_AUTORIZADO" || tipo === "SALDO_INICIAL") {
      sheetName = "Historial_Deudas";
    } else if (tipo === "PAGO_RECIBIDO") {
      sheetName = "Historial_Pagos";
    }
    
    var sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
    }
    
    // Si la hoja está nueva, colocar encabezados
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["Fecha", "Bodega", "Tipo Operación", "Cliente / Detalle", "Monto (COP)", "Registrado Por"]);
    }
    
    // Agregar la fila con la información recibida
    sheet.appendRow([
      fecha,
      bodegaNombre,
      tipo,
      payload.cliente_nombre || payload.detalle || "N/A",
      payload.monto_cop || 0,
      payload.usuario_registro || "Sistema"
    ]);
    
    return ContentService.createTextOutput(JSON.stringify({"status": "success", "message": "Registrado en Drive con éxito"})).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({"status": "error", "message": error.toString()})).setMimeType(ContentService.MimeType.JSON);
  }
}