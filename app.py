import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
import urllib.parse
import pandas as pd
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Local Mesitas - Sistema POS y Apartados",
    page_icon="🛏️",
    layout="wide",
)

CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1234"

# 📱 TUS DOS NÚMEROS DE WHATSAPP PERSONALES
NUMERO_1 = "593990847819"
NUMERO_2 = "593983576800"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"
CARPETA_FOTOS = "fotos_ventas"

if not os.path.exists(CARPETA_FOTOS):
  os.makedirs(CARPETA_FOTOS)


# --- FUNCIÓN PARA ENVIAR CORREO (Opcional) ---
def enviar_correo_venta(destinatario, asunto, cuerpo, ruta_foto=None):
  if not destinatario or "@" not in destinatario:
    return
  try:
    remitente = st.secrets["EMAIL_USER"]
    password = st.secrets["EMAIL_PASS"]
  except:
    return

  try:
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = destinatario
    msg.set_content(cuerpo)

    if ruta_foto and ruta_foto != "Sin foto" and os.path.exists(ruta_foto):
      with open(ruta_foto, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(ruta_foto)
      msg.add_attachment(
          file_data, maintype="image", subtype="jpeg", filename=file_name
      )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
      smtp.login(remitente, password)
      smtp.send_message(msg)
  except Exception as e:
    print(f"Error al enviar correo: {e}")


# --- FUNCIÓN PARA GENERAR ENLACE DE WHATSAPP ---
def generar_link_whatsapp(numero, mensaje):
  texto_codificado = urllib.parse.quote(mensaje)
  return f"https://wa.me/{numero}?text={texto_codificado}"


# --- SISTEMA DE BLOQUEO CON CONTRASEÑA ---
if "autenticado" not in st.session_state:
  st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
  st.markdown(
      """
        <style>
        .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; }
        .login-box {
            max-width: 450px;
            margin: 100px auto;
            padding: 50px;
            background: rgba(30, 41, 59, 0.8);
            border-radius: 24px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(12px);
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

  st.markdown(
      """
        <div class="login-box">
            <h1 style="color: #38bdf8; margin-bottom: 15px; font-weight: 800; font-size: 36px;">🔐 Local Mesitas</h1>
            <p style="color: #94a3b8; font-size: 18px;">Ingrese su contraseña para acceder al sistema</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 1.4, 1])
  with col2:
    passw = st.text_input("Contraseña", type="password", key="input_pass_app")
    if st.button("🚀 INGRESAR AL SISTEMA", use_container_width=True):
      if passw == CLAVE_ACCESO:
        st.session_state["autenticado"] = True
        st.rerun()
      else:
        st.error("❌ Clave incorrecta")
  st.stop()

# --- CARGAR O CREAR INVENTARIO (AQUÍ AGREGAS TU NUEVA OPCIÓN DE CAMA) ---
if os.path.exists(FILE_INV):
  df_inv = pd.read_csv(FILE_INV)
  if "PRECIO" not in df_inv.columns:
    df_inv["PRECIO"] = 0.0
else:
  df_inv = pd.DataFrame([
      {"CATEGORIA": "Cama Tapizada", "STOCK": 5, "PRECIO": 150.0},
      {"CATEGORIA": "Cama de Madera", "STOCK": 5, "PRECIO": 140.0},
      {"CATEGORIA": "Cama Mixta", "STOCK": 5, "PRECIO": 145.0},
      {
          "CATEGORIA": "Cama King Size",
          "STOCK": 5,
          "PRECIO": 180.0,
      },  # <-- Tu nueva opción agregada
      {"CATEGORIA": "Colchones", "STOCK": 5, "PRECIO": 100.0},
      {"CATEGORIA": "Armarios Grandes", "STOCK": 3, "PRECIO": 200.0},
      {"CATEGORIA": "Armarios Pequeños", "STOCK": 3, "PRECIO": 120.0},
      {"CATEGORIA": "Pajaritas", "STOCK": 10, "PRECIO": 15.0},
  ])
  df_inv.to_csv(FILE_INV, index=False)

# --- CARGAR O CREAR VENTAS ---
if os.path.exists(FILE_VENTAS):
  df_ventas = pd.read_csv(FILE_VENTAS)
  if "ABONADO" not in df_ventas.columns:
    df_ventas["ABONADO"] = df_ventas["TOTAL"]
    df_ventas["SALDO_PENDIENTE"] = 0.0
    df_ventas["ESTADO"] = "Pagado y Entregado"
    df_ventas.to_csv(FILE_VENTAS, index=False)
  if "DIRECCION" not in df_ventas.columns:
    df_ventas["DIRECCION"] = "S/N"
    df_ventas.to_csv(FILE_VENTAS, index=False)
  if "FOTO" not in df_ventas.columns:
    df_ventas["FOTO"] = "Sin foto"
    df_ventas.to_csv(FILE_VENTAS, index=False)
else:
  df_ventas = pd.DataFrame(columns=[
      "FECHA",
      "CATEGORIA",
      "CANTIDAD",
      "PRECIO_UNITARIO",
      "TOTAL",
      "ABONADO",
      "SALDO_PENDIENTE",
      "METODO_PAGO",
      "CLIENTE",
      "CEDULA",
      "TELEFONO",
      "CORREO",
      "DIRECCION",
      "ESTADO",
      "FOTO",
  ])
  df_ventas.to_csv(FILE_VENTAS, index=False)

# --- ESTILOS VISUALES ---
st.markdown(
    """
    <style>
    .stApp { background-color: #f8fafc; font-family: 'Inter', 'Segoe UI', Roboto, sans-serif; font-size: 18px; }
    
    .header-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 45px;
        border-radius: 24px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 15px 30px rgba(15, 23, 42, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .card-resibo {
        background: white;
        padding: 35px;
        border-radius: 20px;
        border-left: 8px solid #3b82f6;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        border-top: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }

    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border-radius: 16px;
        font-weight: 700;
        font-size: 20px !important;
        height: 64px !important;
        width: 100%;
        border: none;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(37, 99, 235, 0.5);
    }

    div[data-baseweb="tab-list"] { gap: 12px; background-color: #e2e8f0; padding: 10px; border-radius: 18px; }
    div[data-baseweb="tab"] { border-radius: 14px; font-weight: 700; font-size: 18px !important; color: #334155; padding: 12px 24px !important; }
    
    input, select, textarea { font-size: 18px !important; }
    .stSelectbox label, .stTextInput label, .stNumberInput label, .stFileUploader label {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

col_title, col_logout = st.columns([6, 1])
with col_logout:
  if st.button("🔒 Salir"):
    st.session_state["autenticado"] = False
    st.rerun()

st.markdown(
    """
    <div class="header-box">
        <h1 style="color:white; margin:0; font-size: 42px; font-weight: 800; letter-spacing: -0.5px;">🏪 LOCAL MESITAS</h1>
        <p style="margin:12px 0 0 0; font-size: 20px; color: #94a3b8;">Sistema de POS, Apartados y Notificaciones</p>
    </div>
""",
    unsafe_allow_html=True,
)

stock_critico = df_inv[df_inv["STOCK"] <= 2]
if not stock_critico.empty:
  productos_bajos = ", ".join([
      f"**{row['CATEGORIA']}** ({row['STOCK']} ud.)"
      for _, row in stock_critico.iterrows()
  ])
  st.warning(
      f"🚨 **ATENCIÓN - STOCK BAJO:** {productos_bajos}. ¡Reabastece pronto!"
  )

tab_ops, tab_apartados, tab_inventario, tab_historial = st.tabs([
    "⚡ Venta Directa",
    "📦 Apartados y Abonos",
    "🛠️ Inventario",
    "📜 Historial y Caja",
])

# ================= TAB 1: VENTA DIRECTA =================
with tab_ops:
  st.markdown("### ⚡ Venta Rápida (Pago Total e Inmediato)")

  if df_inv.empty:
    st.info("No hay productos en el inventario.")
  else:
    cols = st.columns(len(df_inv) if len(df_inv) <= 6 else 6)
    iconos = {
        "Cama Tapizada": "🛏️",
        "Cama de Madera": "🪵",
        "Cama Mixta": "🛏️",
        "Cama King Size": "👑",  # <-- Icono para tu nueva opción
        "Colchones": "💤",
        "Armarios Grandes": "🚪",
        "Armarios Pequeños": "🚪",
        "Pajaritas": "🎀",
    }
    for idx, row in df_inv.iterrows():
      cat = row["CATEGORIA"]
      col_target = cols[idx % len(cols)]
      col_target.metric(
          label=f"{iconos.get(cat, '📦')} {cat}",
          value=f"{int(row['STOCK'])} ud",
          delta=f"${row['PRECIO']:,.2f}",
      )

    st.markdown("---")

    # --- SECCIÓN PARA AGREGAR NUEVO PRODUCTO DINÁMICAMENTE ---
    with st.expander("➕ Agregar nuevo producto / apartado manualmente"):
      nuevo_prod_input = st.text_input("Nombre del producto nuevo:")
      if st.button("Añadir producto a la lista"):
        if nuevo_prod_input.strip() != "":
          if (
              nuevo_prod_input.strip().capitalize()
              not in df_inv["CATEGORIA"].values
          ):
            nuevo_df_inv = pd.DataFrame([{
                "CATEGORIA": nuevo_prod_input.strip().capitalize(),
                "STOCK": 5,
                "PRECIO": 50.0,
            }])
            pd.concat([df_inv, nuevo_df_inv], ignore_index=True).to_csv(
                FILE_INV, index=False
            )
            st.success(
                f"¡Producto '{nuevo_prod_input.strip().capitalize()}' agregado"
                " con éxito!"
            )
            st.rerun()
          else:
            st.info("Ese producto ya existe en el inventario.")
        else:
          st.warning("Escribe el nombre del producto.")

    categoria_sel = st.selectbox(
        "Selecciona el Producto", df_inv["CATEGORIA"].tolist(), key="v_cat"
    )
    row_sel = df_inv[df_inv["CATEGORIA"] == categoria_sel].iloc[0]
    stock_disp = int(row_sel["STOCK"])
    precio_unit = float(row_sel["PRECIO"])

    with st.form("form_venta_rapida"):
      c1, c2 = st.columns(2)
      cant = c1.number_input("Cantidad", min_value=1, value=1, step=1)
      pago = c2.selectbox(
          "Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"]
      )

      descuento = st.number_input(
          "Descuento ($)", min_value=0.0, value=0.0, step=1.0
      )

      if descuento > 10.0:
        st.warning("No permitido no descuentes mucho")

      cliente = st.text_input("Nombre del Cliente", value="Cliente General")

      cc1, cc2 = st.columns(2)
      celda = cc1.text_input("Cédula / RUC", value="S/N")
      telefono = cc2.text_input("Teléfono del cliente (Opcional)", value="")

      correo = st.text_input("Correo electrónico del cliente", value="")
      direccion = st.text_input("Dirección de Entrega", value="")

      foto_subida = st.file_uploader(
          "📸 Subir Foto de la Cama o Producto (Opcional)",
          type=["jpg", "png", "jpeg"],
      )

      subtotal = cant * precio_unit
      total = max(0.0, subtotal - descuento)
      st.markdown(
          f"<h2 style='color:#1e293b; margin-top:20px;'>Total a Cobrar:"
          f" ${total:,.2f}</h2>",
          unsafe_allow_html=True,
      )

      submitted_venta = st.form_submit_button(
          "💰 COBRAR Y GENERAR RECIBO DE VENTA"
      )

      if submitted_venta:
        if descuento > 10.0:
          st.error(
              "❌ No se puede procesar la venta porque el descuento supera el"
              " límite permitido de $10."
          )
        elif cant > stock_disp:
          st.error(f"❌ Stock insuficiente. Solo hay {stock_disp} unidades.")
        else:
          ruta_foto_guardada = "Sin foto"
          if foto_subida is not None:
            nombre_archivo = (
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto_subida.name}"
            )
            ruta_foto_guardada = os.path.join(CARPETA_FOTOS, nombre_archivo)
            with open(ruta_foto_guardada, "wb") as f:
              f.write(foto_subida.getbuffer())

          df_inv.loc[df_inv["CATEGORIA"] == categoria_sel, "STOCK"] -= cant
          df_inv.to_csv(FILE_INV, index=False)

          df_actual_v = pd.read_csv(FILE_VENTAS)
          if "FOTO" not in df_actual_v.columns:
            df_actual_v["FOTO"] = "Sin foto"

          nueva = pd.DataFrame([{
              "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
              "CATEGORIA": categoria_sel,
              "CANTIDAD": cant,
              "PRECIO_UNITARIO": precio_unit,
              "TOTAL": total,
              "ABONADO": total,
              "SALDO_PENDIENTE": 0.0,
              "METODO_PAGO": pago,
              "CLIENTE": cliente,
              "CEDULA": celda,
              "TELEFONO": telefono,
              "CORREO": correo,
              "DIRECCION": direccion,
              "ESTADO": "Pagado y Entregado",
              "FOTO": ruta_foto_guardada,
          }])
          pd.concat([df_actual_v, nueva], ignore_index=True).to_csv(
              FILE_VENTAS, index=False
          )

          cuerpo_mail = (
              f"Nueva Venta Registrada:\n- Cliente: {cliente}\n- Producto:"
              f" {cant}x {categoria_sel}\n- Descuento: ${descuento:,.2f}\n-"
              f" Total: ${total:,.2f}\n- Método: {pago}\n- Dirección:"
              f" {direccion}"
          )
          enviar_correo_venta(
              correo,
              "🧾 Recibo de Compra - Local Mesitas",
              cuerpo_mail,
              ruta_foto_guardada,
          )

          st.session_state["ultima_venta_ws"] = {
              "mensaje": (
                  f"🚨 *NUEVA VENTA REGISTRADA* 🛏️\n\n👤 *Cliente*:"
                  f" {cliente}\n📞 *Tel*: {telefono if telefono else 'N/A'}\n📦"
                  f" *Producto*: {cant}x {categoria_sel}\n🏷️ *Descuento*:"
                  f" ${descuento:,.2f}\n💰 *Total*: ${total:,.2f}\n💳 *Pago*:"
                  f" {pago}\n📍 *Dirección*: {direccion}\n📅 *Fecha*:"
                  f" {datetime.now().strftime('%Y-%m-%d %H:%M')}"
              )
          }
          st.success("¡Venta procesada con éxito!")
          st.rerun()

  if "ultima_venta_ws" in st.session_state:
    uv = st.session_state["ultima_venta_ws"]
    link_ws_1 = generar_link_whatsapp(NUMERO_1, uv["mensaje"])
    link_ws_2 = generar_link_whatsapp(NUMERO_2, uv["mensaje"])

    st.markdown(
        f"""
            <div style="background: #f0fdf4; border: 3px solid #22c55e; padding: 25px; border-radius: 20px; text-align: center; margin-top: 25px;">
                <h2 style="color: #15803d; margin-top:0; font-size: 26px;">📱 Notificaciones de WhatsApp Listas</h2>
                <p style="font-size: 18px;">Haz clic en los botones para enviar el reporte a tus dos números personales:</p>
                <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 20px;">
                    <a href="{link_ws_1}" target="_blank" style="background-color: #25d366; color: white; padding: 16px 28px; border-radius: 14px; text-decoration: none; font-weight: bold; font-size: 18px; display: inline-block; box-shadow: 0 4px 12px rgba(37,211,102,0.4);">💬 Enviar a Número 1 (0990847819)</a>
                    <a href="{link_ws_2}" target="_blank" style="background-color: #128c7e; color: white; padding: 16px 28px; border-radius: 14px; text-decoration: none; font-weight: bold; font-size: 18px; display: inline-block; box-shadow: 0 4px 12px rgba(18,140,126,0.4);">💬 Enviar a Número 2 (0983576800)</a>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("✖️ Ocultar notificación"):
      del st.session_state["ultima_venta_ws"]
      st.rerun()

# ================= TAB 2: APARTADOS Y ABONOS =================
with tab_apartados:
  st.markdown("### 📦 Gestión de Apartados y Clientes")

  with st.expander(
      "➕ CREAR NUEVO APARTADO (Hacer clic para abrir formulario)",
      expanded=True,
  ):
    if not df_inv.empty:
      with st.form("form_nuevo_ap"):
        ap_cat = st.selectbox("Producto a Apartar", df_inv["CATEGORIA"].tolist())
        p_info = df_inv[df_inv["CATEGORIA"] == ap_cat].iloc[0]

        c_a1, c_a2 = st.columns(2)
        ap_cant = c_a1.number_input("Cantidad", min_value=1, value=1)
        ap_abono = c_a2.number_input(
            "Dinero que deja abonando hoy ($)",
            min_value=0.0,
            value=10.0,
            step=5.0,
        )

        ap_cliente = st.text_input("Nombre y Apellido del Cliente")

        c_inf1, c_inf2 = st.columns(2)
        ap_ced = c_inf1.text_input("Cédula / DNI")
        ap_tel = c_inf2.text_input("Teléfono del cliente")

        ap_corr = st.text_input("Correo electrónico del cliente")
        ap_dir = st.text_input("Dirección exacta")

        ap_foto = st.file_uploader(
            "📸 Subir Foto de la Cama o Producto Apartado (Opcional)",
            type=["jpg", "png", "jpeg"],
            key="foto_ap",
        )

        precio_p = float(p_info["PRECIO"])
        tot_p = ap_cant * precio_p
        saldo_p = tot_p - ap_abono

        st.info(
            f"💵 Valor Total: ${tot_p:,.2f} | 📥 Abono Hoy: ${ap_abono:,.2f} |"
            f" 🔴 **Falta por pagar: ${saldo_p:,.2f}**"
        )

        if st.form_submit_button("💾 GUARDAR APARTADO Y GENERAR RECIBO"):
          if ap_cliente.strip() == "":
            st.warning("Por favor ingresa el nombre del cliente.")
          else:
            ruta_foto_ap = "Sin foto"
            if ap_foto is not None:
              nombre_archivo = f"ap_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ap_foto.name}"
              ruta_foto_ap = os.path.join(CARPETA_FOTOS, nombre_archivo)
              with open(ruta_foto_ap, "wb") as f:
                f.write(ap_foto.getbuffer())

            df_actual_v = pd.read_csv(FILE_VENTAS)
            if "FOTO" not in df_actual_v.columns:
              df_actual_v["FOTO"] = "Sin foto"

            estado_ap = (
                "Pagado y Entregado"
                if saldo_p <= 0
                else "Apartado (Pendiente)"
            )
            nuevo_ap = pd.DataFrame([{
                "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "CATEGORIA": ap_cat,
                "CANTIDAD": ap_cant,
                "PRECIO_UNITARIO": precio_p,
                "TOTAL": tot_p,
                "ABONADO": ap_abono,
                "SALDO_PENDIENTE": max(0.0, saldo_p),
                "METODO_PAGO": "Efectivo",
                "CLIENTE": ap_cliente,
                "CEDULA": ap_ced,
                "TELEFONO": ap_tel,
                "CORREO": ap_corr,
                "DIRECCION": ap_dir,
                "ESTADO": estado_ap,
                "FOTO": ruta_foto_ap,
            }])

            if saldo_p <= 0:
              df_inv.loc[df_inv["CATEGORIA"] == ap_cat, "STOCK"] -= ap_cant
              df_inv.to_csv(FILE_INV, index=False)
              st.success("¡El cliente pagó el total de inmediato!")
            else:
              st.success(f"¡Apartado guardado correctamente para {ap_cliente}!")

            pd.concat([df_actual_v, nuevo_ap], ignore_index=True).to_csv(
                FILE_VENTAS, index=False
            )

            cuerpo_mail = (
                f"Nuevo Apartado:\nCliente: {ap_cliente}\nProducto: {ap_cant}x"
                f" {ap_cat}\nTotal: ${tot_p:,.2f}\nAbono:"
                f" ${ap_abono:,.2f}\nSaldo: ${saldo_p:,.2f}"
            )
            enviar_correo_venta(
                ap_corr,
                "🧾 Recibo de Apartado - Local Mesitas",
                cuerpo_mail,
                ruta_foto_ap,
            )

            st.session_state["ultima_venta_ws"] = {
                "mensaje": (
                    f"📦 *NUEVO APARTADO REGISTRADO* 🛏️\n\n👤 *Cliente*:"
                    f" {ap_cliente}\n📞 *Tel*: {ap_tel}\n📦 *Producto*:"
                    f" {ap_cant}x {ap_cat}\n💰 *Total*: ${tot_p:,.2f}\n📥"
                    f" *Abono*: ${ap_abono:,.2f}\n🔴 *Saldo Pendiente*:"
                    f" ${saldo_p:,.2f}\n📌 *Estado*: {estado_ap}"
                )
            }
            st.rerun()

  st.markdown("---")
  st.markdown("### 📋 Apartados Activos y Consulta de Recibos")

  df_v = pd.read_csv(FILE_VENTAS) if os.path.exists(FILE_VENTAS) else pd.DataFrame()
  if not df_v.empty and "ESTADO" in df_v.columns:
    if "DIRECCION" not in df_v.columns:
      df_v["DIRECCION"] = "S/N"
    if "FOTO" not in df_v.columns:
      df_v["FOTO"] = "Sin foto"

    pendientes = df_v[
        df_v["ESTADO"].str.contains("Apartado", case=False, na=False)
    ]

    if "msg_exito" in st.session_state:
      st.markdown(st.session_state["msg_exito"], unsafe_allow_html=True)
      if st.button("✖️ Cerrar aviso de pago completo"):
        del st.session_state["msg_exito"]
        st.rerun()

    if pendientes.empty:
      st.success("✨ ¡No hay apartados pendientes en este momento!")
    else:
      lista_recibos = [
          (
              f"Fila {i} ➔ Cliente: {r['CLIENTE']} | Producto:"
              f" {r['CATEGORIA']} | Debe: ${r['SALDO_PENDIENTE']:,.2f}"
          )
          for i, r in pendientes.iterrows()
      ]
      recibo_sel = st.selectbox(
          "🔍 Selecciona un apartado para ver su Recibo Detallado y abonar:",
          lista_recibos,
      )

      if recibo_sel:
        idx_sel = int(recibo_sel.split(" ➔ ")[0].replace("Fila ", ""))
        r_data = df_v.loc[idx_sel]

        col_recibo_txt, col_recibo_img = st.columns([1.5, 1])

        with col_recibo_txt:
          st.markdown(
              f"""
                        <div class="card-resibo">
                            <h2 style="color: #2563eb; margin-top: 0; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; font-weight: 700;">🧾 RECIBO DE APARTADO</h2>
                            <p style="font-size: 17px; margin: 8px 0; color: #334155;"><b>📅 Fecha:</b> {r_data['FECHA']}</p>
                            <p style="font-size: 17px; margin: 8px 0; color: #334155;"><b>👤 Cliente:</b> {r_data['CLIENTE']}</p>
                            <p style="font-size: 17px; margin: 8px 0; color: #334155;"><b>📞 Teléfono:</b> {r_data['TELEFONO']} | <b>🆔 Cédula:</b> {r_data['CEDULA']}</p>
                            <p style="font-size: 17px; margin: 8px 0; color: #334155;"><b>📍 Dirección:</b> {r_data['DIRECCION']}</p>
                            <hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 15px 0;">
                            <p style="font-size: 17px; margin: 8px 0; color: #334155;"><b>📦 Producto:</b> {r_data['CANTIDAD']}x {r_data['CATEGORIA']}</p>
                            <p style="font-size: 18px; margin: 8px 0; color: #334155;"><b>💰 Valor Total:</b> ${r_data['TOTAL']:,.2f}</p>
                            <p style="font-size: 18px; margin: 8px 0; color: #16a34a;"><b>✅ Abonado:</b> ${r_data['ABONADO']:,.2f}</p>
                            <p style="font-size: 20px; margin: 12px 0; color: #dc2626;"><b>🔴 SALDO: ${r_data['SALDO_PENDIENTE']:,.2f}</b></p>
                        </div>
                    """,
              unsafe_allow_html=True,
          )

        with col_recibo_img:
          st.markdown("#### 🖼️ Foto del Producto")
          foto_path = str(r_data.get("FOTO", "Sin foto"))
          if foto_path != "Sin foto" and os.path.exists(foto_path):
            st.image(
                foto_path,
                caption=f"{r_data['CATEGORIA']} - {r_data['CLIENTE']}",
                use_column_width=True,
            )
          else:
            st.info("Sin foto adjunta en este registro.")

        with st.form(f"form_abono_{idx_sel}"):
          st.markdown("#### 💸 Registrar nuevo abono a este recibo")
          cant_abonar = st.number_input(
              f"¿Cuánto dinero trae {r_data['CLIENTE']} hoy? ($)",
              min_value=0.0,
              max_value=float(r_data["SALDO_PENDIENTE"]),
              value=float(r_data["SALDO_PENDIENTE"]),
              step=5.0,
          )

          if st.form_submit_button("📥 REGISTRAR ABONO AL RECIBO"):
            nuevo_abonado = float(r_data["ABONADO"]) + cant_abonar
            nuevo_saldo = float(r_data["SALDO_PENDIENTE"]) - cant_abonar

            df_v.loc[idx_sel, "ABONADO"] = nuevo_abonado
            df_v.loc[idx_sel, "SALDO_PENDIENTE"] = max(0.0, nuevo_saldo)

            if nuevo_saldo <= 0:
              df_v.loc[idx_sel, "ESTADO"] = "Pagado y Entregado"
              cant_entregar = int(r_data["CANTIDAD"])
              c_prod = r_data["CATEGORIA"]

              if c_prod in df_inv["CATEGORIA"].values:
                df_inv.loc[df_inv["CATEGORIA"] == c_prod, "STOCK"] -= (
                    cant_entregar
                )
                df_inv.to_csv(FILE_INV, index=False)

              st.session_state["msg_exito"] = f"""
                                <div style="background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); padding: 35px; border-radius: 20px; text-align: center; color: white; margin: 15px 0;">
                                    <h1 style="margin:0; font-size: 30px;">🎉 ¡DEUDA SALDADA!</h1>
                                    <h3 style="margin:12px 0; font-size: 22px;">EL CLIENTE <b>{r_data['CLIENTE'].upper()}</b> TERMINÓ DE PAGAR.</h3>
                                    <p style="font-size: 22px; margin:0;">📦 <b>ENTREGUE EL PRODUCTO:</b> {cant_entregar}x {c_prod}</p>
                                </div>
                            """
            else:
              st.success(
                  f"¡Abono registrado! Nuevo saldo pendiente:"
                  f" ${nuevo_saldo:,.2f}"
              )

            df_v.to_csv(FILE_VENTAS, index=False)

            cuerpo_mail = (
                f"Abono registrado para {r_data['CLIENTE']}\nAbono:"
                f" ${cant_abonar:,.2f}\nSaldo Pendiente:"
                f" ${max(0.0, nuevo_saldo):,.2f}"
            )
            enviar_correo_venta(
                r_data["CORREO"],
                "🧾 Comprobante de Abono - Local Mesitas",
                cuerpo_mail,
                r_data["FOTO"],
            )

            st.session_state["ultima_venta_ws"] = {
                "mensaje": (
                    f"💵 *NUEVO ABONO REGISTRADO* 🛏️\n\n👤 *Cliente*:"
                    f" {r_data['CLIENTE']}\n📥 *Abono recibido*:"
                    f" ${cant_abonar:,.2f}\n🔴 *Nuevo Saldo Pendiente*:"
                    f" ${max(0.0, nuevo_saldo):,.2f}\n📌 *Estado*:"
                    f" {df_v.loc[idx_sel, 'ESTADO']}"
                )
            }
            st.rerun()

# ================= TAB 3: INVENTARIO =================
with tab_inventario:
  st.markdown("### 🛠️ Inventario (Protegido)")
  pass_inv = st.text_input("Clave de Administrador", type="password", key="p_inv")
  if pass_inv == CLAVE_ADMIN:
    st.success("Acceso concedido")
    c1, c2 = st.columns(2)
    with c1:
      st.markdown("#### Modificar Stock o Precio")
      if not df_inv.empty:
        prod_m = st.selectbox("Producto", df_inv["CATEGORIA"].tolist())
        act_s = st.number_input("Sumar / Restar stock (+ o -)", value=0, step=1)
        nue_p = st.number_input(
            "Nuevo Precio ($)",
            value=float(
                df_inv[df_inv["CATEGORIA"] == prod_m]["PRECIO"].values[0]
            ),
        )
        if st.button("Actualizar Stock/Precio"):
          idx = df_inv[df_inv["CATEGORIA"] == prod_m].index[0]
          df_inv.loc[idx, "STOCK"] = max(
              0, int(df_inv.loc[idx, "STOCK"]) + act_s
          )
          df_inv.loc[idx, "PRECIO"] = nue_p
          df_inv.to_csv(FILE_INV, index=False)
          st.success("¡Actualizado!")
          st.rerun()
    with c2:
      st.markdown("#### Añadir Producto Nuevo")
      n_nom = st.text_input("Nombre del producto")
      n_stk = st.number_input("Stock inicial", min_value=0, value=5)
      n_prc = st.number_input("Precio ($)", min_value=0.0, value=50.0)
      if st.button("Crear Producto"):
        if n_nom.strip() != "":
          nuevo_reg = pd.DataFrame([{
              "CATEGORIA": n_nom.capitalize(),
              "STOCK": n_stk,
              "PRECIO": n_prc,
          }])
          pd.concat([df_inv, nuevo_reg], ignore_index=True).to_csv(
              FILE_INV, index=False
          )
          st.success("¡Creado!")
          st.rerun()

    st.markdown("---")
    st.markdown("#### 🗑️ Eliminar Producto del Inventario")
    if not df_inv.empty:
      prod_a_borrar = st.selectbox(
          "Selecciona el producto que deseas eliminar por completo",
          df_inv["CATEGORIA"].tolist(),
          key="sel_borrar_prod",
      )
      if st.button("❌ ELIMINAR ESTE PRODUCTO PERMANENTEMENTE"):
        df_inv = df_inv[df_inv["CATEGORIA"] != prod_a_borrar].reset_index(
            drop=True
        )
        df_inv.to_csv(FILE_INV, index=False)
        st.success(
            f"¡El producto '{prod_a_borrar}' fue eliminado del inventario!"
        )
        st.rerun()

  elif pass_inv != "":
    st.error("Clave incorrecta")

# ================= TAB 4: HISTORIAL Y CAJA =================
with tab_historial:
  st.markdown("### 📜 Cierre de Caja y Registros")
  if os.path.exists(FILE_VENTAS):
    df_h = pd.read_csv(FILE_VENTAS)
    if not df_h.empty:
      total_caja = (
          df_h["ABONADO"].sum()
          if "ABONADO" in df_h.columns
          else df_h["TOTAL"].sum()
      )
      st.metric(
          "💵 Total Dinero Recibido (Ventas + Abonos)", f"${total_caja:,.2f}"
      )
      st.dataframe(df_h, use_container_width=True)

      st.markdown("---")
      st.markdown("#### 🔍 Ver Foto de un Registro del Historial")
      lista_hist = [
          (
              f"Fila {i} | Fecha: {r['FECHA']} | Cliente: {r['CLIENTE']} | Prod:"
              f" {r['CATEGORIA']}"
          )
          for i, r in df_h.iterrows()
      ]
      reg_foto_sel = st.selectbox(
          "Selecciona un registro para ver su foto guardada", lista_hist
      )
      if reg_foto_sel:
        idx_h = int(reg_foto_sel.split(" | ")[0].replace("Fila ", ""))
        path_f = str(df_h.loc[idx_h].get("FOTO", "Sin foto"))
        if path_f != "Sin foto" and os.path.exists(path_f):
          st.image(
              path_f,
              width=350,
              caption=f"Foto de {df_h.loc[idx_h]['CATEGORIA']}",
          )
        else:
          st.info("Este registro no tiene foto guardada.")

      st.markdown("---")
      st.markdown("#### 🗑️ Eliminar Registro Erróneo (Protegido)")
      pass_del = st.text_input(
          "Contraseña de Administrador para borrar",
          type="password",
          key="pass_del_reg",
      )

      if pass_del == CLAVE_ADMIN:
        lista_borrar = [
            (
                f"Fila {i} | Fecha: {r['FECHA']} | Cliente: {r['CLIENTE']} |"
                f" Total: ${r['TOTAL']}"
            )
            for i, r in df_h.iterrows()
        ]
        reg_a_borrar = st.selectbox(
            "Selecciona el registro que deseas eliminar",
            lista_borrar,
            key="sel_borrar",
        )

        if st.button("❌ BORRAR REGISTRO SELECCIONADO PERMANENTEMENTE"):
          idx_del = int(reg_a_borrar.split(" | ")[0].replace("Fila ", ""))
          foto_a_borrar = str(df_h.loc[idx_del].get("FOTO", "Sin foto"))
          if foto_a_borrar != "Sin foto" and os.path.exists(foto_a_borrar):
            try:
              os.remove(foto_a_borrar)
            except:
              pass

          df_h = df_h.drop(idx_del).reset_index(drop=True)
          df_h.to_csv(FILE_VENTAS, index=False)
          st.success("¡Registro eliminado correctamente!")
          st.rerun()
      elif pass_del != "":
        st.error("Clave incorrecta para borrar")

      st.markdown("---")
      if st.button("📥 Descargar Reporte CSV"):
        st.download_button(
            "Descargar",
            df_h.to_csv(index=False).encode("utf-8"),
            "reporte.csv",
            "text/csv",
        )
