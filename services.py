from datetime import datetime
from utils import es_numero, obtener_hoja_segura

def obtener_egresos_pendientes():
    hoja = obtener_hoja_segura()
    datos = hoja.get_all_records()
    pendientes = []

    for i, fila in enumerate(datos, start=2):
        if "Pagado" in fila and str(fila["Pagado"]).lower() == "true":
            continue
        if not fila.get("Proveedor") or not fila.get("Monto"):
            continue
        pendientes.append((i, fila["Proveedor"], abs(float(fila["Monto"]))))
    return pendientes

def marcar_como_pagado(fila_idx):
    hoja = obtener_hoja_segura()
    hoja.update_cell(fila_idx, 5, "'true")
    fila = hoja.row_values(fila_idx)
    return fila[2], abs(float(fila[3]))

def calcular_total_diario(proveedor="cliente"):
    hoja = obtener_hoja_segura()
    datos = hoja.get_all_records()
    hoy = datetime.now().date()

    return sum(
        float(row["Monto"]) for row in datos
        if "Fecha" in row and "Monto" in row and "Proveedor" in row
        and row["Proveedor"] == proveedor
        and es_numero(row["Monto"])
        and datetime.strptime(row["Fecha"], "%Y-%m-%d").date() == hoy
    )