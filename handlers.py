from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from collections import deque

from telegram_conect import mostrar_consultas, teclado_proveedores
from db_sheet import registrar_ingreso, registrar_egreso, obtener_hoja_mes, eliminar_ultimo_cliente
from utils import formatear_monto, es_numero
from services import obtener_egresos_pendientes, marcar_como_pagado
from telegram_conect import mostrar_consultas, teclado_proveedores


procesados = set()
ultimos_ingresos = deque(maxlen=2)


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = update.message.text.strip()

        # Si es un número positivo, registrar como cliente
        if texto.replace(",", ".").replace(".", "", 1).isdigit():
            monto_float = float(texto.replace(",", "."))
            hora_actual = datetime.now().strftime("%H:%M")
            timestamp_actual = datetime.now()

            # Evitar duplicados en los últimos 2 minutos
            for m, t in ultimos_ingresos:
                if m == monto_float and (timestamp_actual - t).total_seconds() < 120:
                    await update.message.reply_text("✅ Tranqui, ya registré ese monto")
                    return

            # Registrar como cliente
            registrar_ingreso(monto_float, hora=hora_actual)
            ultimos_ingresos.append((monto_float, timestamp_actual))

            # Obtener totales
            hoja = obtener_hoja_mes()
            datos = hoja.get_all_records()
            hoy = datetime.now().date()

            # Total de ingresos de hoy
            total_hoy = sum(
                float(row["Monto"]) for row in datos
                if "Fecha" in row and "Monto" in row and "Proveedor" in row
                and row["Proveedor"] == "cliente"
                and es_numero(row["Monto"])
                and datetime.strptime(row["Fecha"], "%Y-%m-%d").date() == hoy
            )

            # Total del mes (excluyendo Mercadería y Desperdicio)
            excluir = {"Mercadería", "Desperdicio", "Mercaderia"}
            total_estado = sum(
                float(row["Monto"]) for row in datos
                if "Monto" in row and es_numero(row["Monto"])
                and row.get("Proveedor") not in excluir
            )

            mensaje = (
                f"💰 Ingreso registrado: ${formatear_monto(monto_float)} ({hora_actual})\n"
                f"📆 Total del día: ${formatear_monto(total_hoy)}\n"
                f"📊 Estado Mes: ${formatear_monto(total_estado)}"
            )

            # 🔹 BOTONES PROVEEDOR Y GASTO
            botones = [
                [
                    InlineKeyboardButton("📤 Proveedor", callback_data=f"elegir_prov:{monto_float}"),
                    InlineKeyboardButton("💸 Gasto", callback_data=f"elegir_gasto:{monto_float}")
                ]
            ]

            # 🔹 ENVIAR MENSAJE CON BOTONES
            await update.message.reply_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(botones)
            )
            return

        # Si no es un número, mostrar menú de consultas
        await update.message.reply_text(
            "📊 Elegí una opción:",
            reply_markup=mostrar_consultas()
        )
    except Exception as e:
        await update.message.reply_text("⚠️ Ocurrió un error, intentá de nuevo.")



async def manejar_boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        if query.id in procesados:
            return
        procesados.add(query.id)

        data = query.data
        if data.startswith("elegir_prov:"):
            _, monto = data.split(":")
            await query.edit_message_text(
                "📤 Seleccioná el proveedor:",
                reply_markup=teclado_proveedores(float(monto))
            )
            return

        # 🔹 MANEJAR BOTÓN "GASTO"
        if data.startswith("elegir_gasto:"):
            _, monto = data.split(":")
            monto_float = float(monto)
            
            # Mostrar opciones de gasto
            botones = [
                [
                    InlineKeyboardButton("🍻💸 Nosotros (100%)", callback_data=f"Nosotros:{monto_float}"),
                ],
                [
                    InlineKeyboardButton("🧀🛒 Mercadería (70%)", callback_data=f"Mercaderia:{monto_float}"),
                ],
                [
                    InlineKeyboardButton("🗑️ Desperdicio (70%)", callback_data=f"Desperdicio:{monto_float}"),
                ],
                [
                    InlineKeyboardButton("📦 Corrección Caja", callback_data=f"correccion:{monto_float}")
                ]
            ]
            
            await query.edit_message_text(
                f"💸 Elegí el tipo de gasto para ${formatear_monto(monto_float)}:",
                reply_markup=InlineKeyboardMarkup(botones)
            )
            return

        if data == "menu:pagar":
            pendientes = obtener_egresos_pendientes()
            if not pendientes:
                await query.edit_message_text("✅ No hay egresos pendientes.")
                return

            botones = [
                [InlineKeyboardButton(f"{prov} - ${formatear_monto(monto)}", callback_data=f"pagar_idx:{idx}")]
                for idx, prov, monto in pendientes
            ]
            await query.edit_message_text("🔻 Egresos pendientes:", reply_markup=InlineKeyboardMarkup(botones))
            return

        if data.startswith("pagar_idx:"):
            fila_idx = int(data.split(":")[1])
            proveedor, monto = marcar_como_pagado(fila_idx)
            await query.edit_message_text(f"✅ Marcado como pagado:\n{proveedor} - ${formatear_monto(monto)}")
            return

#        if data.startswith("proveedor:"):
 #           _, proveedor, monto = data.split(":")
  #          monto = -abs(float(monto))
   #         hora_actual = datetime.now().strftime("%H:%M")
    #        registrar_egreso(proveedor, monto, hora=hora_actual)
     #       await query.edit_message_text(f"📤 {proveedor}: ${formatear_monto(abs(monto))} ({hora_actual})")
      #      return

        elif data.startswith("proveedor:"):
            _, proveedor, monto = data.split(":")
            monto_original = float(monto)  # guardar el monto original positivo
            monto = -abs(float(monto))  # siempre egreso negativo
            hora_actual = datetime.now().strftime("%H:%M")

            # 🔹 ELIMINAR el último registro de "cliente" 
            eliminar_ultimo_cliente()

            # Registrar egreso del proveedor
            registrar_egreso(proveedor, monto, hora=hora_actual)

            # Obtener todos los datos del mes
            hoja = obtener_hoja_mes()
            datos = hoja.get_all_records()

            # --- Calcular totales ---
            # Total pagado al proveedor este mes
            total_proveedor_mes = sum(
                 float(row["Monto"]) for row in datos
                 if row.get("Proveedor") == proveedor
                 and es_numero(row["Monto"])
                 and row.get("Fecha", "").startswith(datetime.now().strftime("%Y-%m"))
            )

            # Total del día (todos los movimientos)
            total_dia = sum(
                 float(row["Monto"]) for row in datos
                 if es_numero(row["Monto"])
                 and row.get("Fecha") == datetime.now().strftime("%Y-%m-%d")
            )

            # Estado del mes (excluyendo Mercadería y Desperdicio)
            excluir = {"Mercadería", "Desperdicio", "Mercaderia"}
            total_estado = sum(
                float(row["Monto"]) for row in datos
                if "Monto" in row and es_numero(row["Monto"])
                and row.get("Proveedor") not in excluir
            )

            # Total de clientes hoy
            hoy = datetime.now().date()
            total_hoy = sum(
                float(row["Monto"]) for row in datos
                if "Fecha" in row and "Monto" in row and "Proveedor" in row
                and row["Proveedor"] == "cliente"
                and es_numero(row["Monto"])
                and datetime.strptime(row["Fecha"], "%Y-%m-%d").date() == hoy
            )

            mensaje = (
                f"📤 {proveedor}: ${formatear_monto(abs(monto))} ({hora_actual})\n"
                f"📊 Total {proveedor} (mes): ${formatear_monto(abs(total_proveedor_mes))}\n"
                f"📆 Total del día: ${formatear_monto(total_hoy)}\n"
                f"💰 Estado Mes: ${formatear_monto(total_estado)}"
            )

            await query.edit_message_text(mensaje)
            return



        if data.startswith("apagar:"):
            _, proveedor, monto = data.split(":")
            monto = -abs(float(monto))
            hora_actual = datetime.now().strftime("%H:%M")
            registrar_egreso(proveedor, monto, hora=hora_actual, pagado="False")
            await query.edit_message_text(f"🕓 A pagar:\n{proveedor} - ${formatear_monto(abs(monto))} ({hora_actual})")
            return

        if data.startswith("Nosotros:"):
            _, monto = data.split(":")
            monto = -abs(float(monto))  # gasto completo
            hora_actual = datetime.now().strftime("%H:%M")
            
            # 🔹 ELIMINAR el último registro de "cliente"
            eliminar_ultimo_cliente()
            
            # Registrar el egreso en la hoja
            registrar_egreso("Nosotros", monto, hora=hora_actual)

            # Obtener todos los datos del mes
            hoja = obtener_hoja_mes()
            datos = hoja.get_all_records()

            # 🔹 Total de egresos con proveedor = Nosotros
            total_nosotros = sum(
                float(row["Monto"]) for row in datos
                if "Monto" in row and "Proveedor" in row
                and row[  "Proveedor"] == "Nosotros"
                and es_numero(row["Monto"])
            )

            # 🔹 Total del estado (excluyendo Mercadería y Desperdicio)
            excluir = {"Mercadería", "Mercaderia", "Desperdicio"}
            total_estado = sum(
                float(row["Monto"]) for row in datos
                if "Monto" in row and es_numero(row["Monto"])
                and row.get("Proveedor") not in excluir
            )

            mensaje = (
                f"💸 Registrado en Nosotros: ${formatear_monto(abs(monto))} ({hora_actual})\n"
                f"📊 Total Nosotros: ${formatear_monto(abs(total_nosotros))}\n"
                f"📊 Estado Mes: ${formatear_monto(total_estado)}"
            )

            await query.edit_message_text(mensaje)
            return


        if data.startswith("Mercaderia:"):
            _, monto = data.split(":")
            monto = -abs(float(monto)) * 0.7
            hora_actual = datetime.now().strftime("%H:%M")
                        # 🔹 ELIMINAR el último registro de "cliente"
            eliminar_ultimo_cliente()
            
            registrar_egreso("Mercaderia", monto, hora=hora_actual)  # 👈 sin tilde, igual que el callback
            await query.edit_message_text(
                 f"🧀🛒 Mercadería (70%): ${formatear_monto(abs(monto))} ({hora_actual})"
            )
            return

        if data.startswith("Desperdicio:"):
            _, monto = data.split(":")
            monto = -abs(float(monto)) * 0.7  # solo 70%
            hora_actual = datetime.now().strftime("%H:%M")
                        # 🔹 ELIMINAR el último registro de "cliente"
            eliminar_ultimo_cliente()
            
            registrar_egreso("Desperdicio", monto, hora=hora_actual)
            await query.edit_message_text(f"🗑️ Desperdicio (70%): ${formatear_monto(abs(monto))} ({hora_actual})")
            return

        if data.startswith("cliente:"):
            _, monto = data.split(":")
            monto_float = float(monto)
            hora_actual = datetime.now().strftime("%H:%M")
            timestamp_actual = datetime.now()

            # Evitar duplicados en los últimos 2 minutos
            for m, t in ultimos_ingresos:
                if m == monto_float and (timestamp_actual - t).total_seconds() < 120:
                    await query.edit_message_text("Tranqui, ya registré")
                    return

            registrar_ingreso(monto_float, hora=hora_actual)
            ultimos_ingresos.append((monto_float, timestamp_actual))

            hoja = obtener_hoja_mes()
            datos = hoja.get_all_records()
            hoy = datetime.now().date()

            # 🔹 Total de ingresos de hoy (solo "cliente")
            total_hoy = sum(
                float(row["Monto"]) for row in datos
                if "Fecha" in row and "Monto" in row and "Proveedor" in row
                and row["Proveedor"] == "cliente"
                and es_numero(row["Monto"])
                and datetime.strptime(row["Fecha"], "%Y-%m-%d").date() == hoy
            )


            # Excluir proveedores no contables
            excluir = {"Mercadería", "Desperdicio", "Mercaderia"}

            total_estado = sum(
                float(row["Monto"]) for row in datos
                if "Monto" in row and es_numero(row["Monto"])
                and row.get("Proveedor") not in excluir
            )

#            # 🔹 Estado menos 900k
#            estado_menos_900k = total_estado  - 900000

            mensaje = (
                f"💰 Ingreso: ${formatear_monto(monto_float)} ({hora_actual})\n"
                f"📆 Total del día: ${formatear_monto(total_hoy)}\n"
                f"📊 Estado Mes: ${formatear_monto(total_estado)}\n"
#                f"📉 Estado: ${formatear_monto(estado_menos_900k)}"
            )

            await query.edit_message_text(mensaje)
            return

        elif data.startswith("correccion:"):
            _, monto = data.split(":")
    # mostramos opciones sobra/falta
            botones = [
                [
                  InlineKeyboardButton("Sobra 💵", callback_data=f"caja_sobra:{monto}"),
                  InlineKeyboardButton("Falta 🪙", callback_data=f"caja_falta:{monto}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(botones)
            await query.edit_message_text("📦 Corrección de Caja: ¿qué ocurrió?", reply_markup=reply_markup)

        elif data.startswith("caja_sobra:"):
            _, monto = data.split(":")
            monto = abs(float(monto))  # positivo
            hora_actual = datetime.now().strftime("%H:%M")
            registrar_egreso("Corrección Caja", monto, hora=hora_actual)
                        # 🔹 Total de ingresos de hoy (solo "cliente")


            hoja = obtener_hoja_mes()
            datos = hoja.get_all_records()
            hoy = datetime.now().date()

            total_hoy = sum(
                float(row["Monto"]) for row in datos
                if "Fecha" in row and "Monto" in row and "Proveedor" in row
                and row["Proveedor"] == "cliente"
                and es_numero(row["Monto"])
                and datetime.strptime(row["Fecha"], "%Y-%m-%d").date() == hoy
            )


            # Excluir proveedores no contables
            excluir = {"Mercadería", "Desperdicio", "Mercaderia"}

            total_estado = sum(
                float(row["Monto"]) for row in datos
                if "Monto" in row and es_numero(row["Monto"])
                and row.get("Proveedor") not in excluir
            )
            mensaje = (

               f"✅ Sobraron ${formatear_monto(abs(monto))} ({hora_actual})\n"
               f"📆 Total del día: ${formatear_monto(total_hoy)}\n"
               f"📊 Estado Mes: ${formatear_monto(total_estado)}"
            )
            await query.edit_message_text(mensaje)
            return
            #    f"✅ Sobraron ${formatear_monto(abs(monto))} ({hora_actual})">
            #    f"📆 Total del día: ${formatear_monto>
            #    f"📊 Estado Mes: ${formatear_monto>
            #)
            #await query.edit_message_text(mensaje)


        elif data.startswith("caja_falta:"):
            _, monto = data.split(":")
            monto = -abs(float(monto))  # negativo
            hora_actual = datetime.now().strftime("%H:%M")
            registrar_egreso("Corrección Caja", monto, hora=hora_actual)
            await query.edit_message_text(f"⚠️ Faltaron ${formatear_monto(abs(monto))} ({hora_actual})")
            return
    except Exception as e:
        print(f"❌ Error en manejar_boton: {e}")
        try:
            await update.callback_query.edit_message_text("⚠️ Ocurrió un error al procesar tu solicitud.")
        except:
            pass
        
