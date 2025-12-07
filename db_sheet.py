import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# SCOPES necesarios
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Cargar credenciales
credenciales = Credentials.from_service_account_file("credential.json", scopes=SCOPES)
cliente = gspread.authorize(credenciales)

SPREADSHEET_NAME = "Registro_Movimientos"

def obtener_hoja_mes():
    try:
        sheet = cliente.open(SPREADSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sheet = cliente.create(SPREADSHEET_NAME)

    mes = datetime.now().strftime("%Y-%m")

    try:
        hoja = sheet.worksheet(mes)
    except gspread.WorksheetNotFound:
        hoja = sheet.add_worksheet(title=mes, rows="1000", cols="4")
        hoja.append_row(["Fecha", "Hora", "Proveedor", "Monto", "Pagado"])

    return hoja

def registrar_ingreso(monto, hora=None):
    ahora = datetime.now()
    hora_formateada = hora if hora else ahora.strftime("%H:%M")
    hoja = obtener_hoja_mes()
    hoja.append_row([ahora.strftime("%Y-%m-%d"), hora_formateada, "cliente", monto, "True"])

def registrar_egreso(proveedor, monto, hora=None, pagado=True):
    ahora = datetime.now()
    hora_formateada = hora if hora else ahora.strftime("%H:%M")
    hoja = obtener_hoja_mes()

    # Verificar si ya tiene columna Pagado
    encabezado = hoja.row_values(1)
    if "Pagado" not in encabezado:
        hoja.update("E1", "Pagado")

    fila = [ahora.strftime("%Y-%m-%d"), hora_formateada, proveedor, monto]

    # Asegurarse de que hay una columna E
    if len(encabezado) < 5:
        fila.append(pagado)
    else:
        while len(fila) < 5:
            fila.append("")  # rellenar columnas vacías si hiciera falta
        fila[4] = str(pagado)

    hoja.append_row(fila)
    
def eliminar_ultimo_cliente():
    """Elimina la última fila donde el proveedor es 'cliente'"""
    try:
        hoja = obtener_hoja_mes()
        datos = hoja.get_all_records()
        
        # Buscar la última fila con "cliente" (de abajo hacia arriba)
        for idx in range(len(datos) - 1, -1, -1):
            if datos[idx].get("Proveedor") == "cliente":
                fila_numero = idx + 2  # +2 porque: 1 por header, 1 por índice base-0
                hoja.delete_rows(fila_numero)
                return True
        
        return False
    except Exception as e:
        return False
