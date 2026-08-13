from datetime import datetime
from email.message import EmailMessage
import mimetypes
import os
import smtplib
import urllib.parse

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Local Mesitas - Sistema POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1234"

NUMERO_1 = "593990847819"
NUMERO_2 = "593983576800"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"
CARPETA_FOTOS = "fotos_ventas"

os.makedirs(CARPETA_FOTOS, exist_ok=True)


# ============================================================
# FUNCIONES
# ============================================================

def guardar_csv_seguro(df, ruta):
    """Guarda un DataFrame sin índices."""
    df.to_csv(ruta, index=False)


def normalizar_inventario(df):
    """Asegura columnas y evita stock negativo."""
    if "CATEGORIA" not in df.columns:
        df["CATEGORIA"] = ""

    if "STOCK" not in df.columns:
        df["STOCK"] = 0

    if "PRECIO" not in df.columns:
        df["PRECIO"] = 0.0

    df["CATEGORIA"] = df["CATEGORIA"].fillna("").astype(str).str.strip()

    df["STOCK"] = pd.to_numeric(
        df["STOCK"], errors="coerce"
    ).fillna(0).astype(int).clip(lower=0)

    df["PRECIO"] = pd.to_numeric(
        df["PRECIO"], errors="coerce"
    ).fillna(0.0).clip(lower=0)

    df = df[df["CATEGORIA"] != ""].reset_index(drop=True)

    return df


def normalizar_ventas(df):
    """Asegura que ventas.csv tenga todas las columnas necesarias."""
    columnas = [
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
    ]

    for col in columnas:
        if col not in df.columns:
            if col == "ABONADO":
                df[col] = (
                    pd.to_numeric(
                        df["TOTAL"], errors="coerce"
                    ).fillna(0)
                    if "TOTAL" in df.columns
                    else 0.0
                )
            elif col == "SALDO_PENDIENTE":
                df[col] = 0.0
            elif col == "ESTADO":
                df[col] = "Pagado y Entregado"
            elif col == "DIRECCION":
                df[col] = "S/N"
            elif col == "FOTO":
                df[col] = "Sin foto"
            else:
                df[col] = ""

    df["CANTIDAD"] = pd.to_numeric(
        df["CANTIDAD"], errors="coerce"
    ).fillna(0).astype(int).clip(lower=0)

    for col in [
        "PRECIO_UNITARIO",
        "TOTAL",
        "ABONADO",
        "SALDO_PENDIENTE",
    ]:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).fillna(0.0).clip(lower=0)

    for col in [
        "FECHA",
        "CATEGORIA",
        "METODO_PAGO",
        "CLIENTE",
        "CEDULA",
        "TELEFONO",
        "CORREO",
        "DIRECCION",
        "ESTADO",
        "FOTO",
    ]:
        df[col] = df[col].fillna("").astype(str)

    return df[columnas]


def cargar_inventario():
    if os.path.exists(FILE_INV):
        df = pd.read_csv(FILE_INV)
    else:
        df = pd.DataFrame(
            [
                {"CATEGORIA": "Camas", "STOCK": 10, "PRECIO": 150.0},
                {"CATEGORIA": "Colchones", "STOCK": 5, "PRECIO": 100.0},
                {"CATEGORIA": "Armarios Grandes", "STOCK": 3, "PRECIO": 200.0},
                {"CATEGORIA": "Armarios Pequeños", "STOCK": 3, "PRECIO": 120.0},
                {"CATEGORIA": "Pajaritas", "STOCK": 10, "PRECIO": 15.0},
            ]
        )

    df = normalizar_inventario(df)
    guardar_csv_seguro(df, FILE_INV)
    return df


def cargar_ventas():
    if os.path.exists(FILE_VENTAS):
        df = pd.read_csv(FILE_VENTAS)
    else:
        df = pd.DataFrame()

    df = normalizar_ventas(df)
    guardar_csv_seguro(df, FILE_VENTAS)
    return df


def guardar_foto(archivo, prefijo=""):
    if archivo is None:
        return "Sin foto"

    nombre = (
        f"{prefijo}"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_"
        f"{os.path.basename(archivo.name)}"
    )

    ruta = os.path.join(CARPETA_FOTOS, nombre)

    with open(ruta, "wb") as f:
        f.write(archivo.getbuffer())

    return ruta


def enviar_correo_venta(destinatario, asunto, cuerpo, ruta_foto=None):
    if not destinatario or "@" not in str(destinatario):
        return

    try:
        remitente = st.secrets["EMAIL_USER"]
        password = st.secrets["EMAIL_PASS"]
    except Exception:
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = remitente
        msg["To"] = destinatario
        msg.set_content(cuerpo)

        if (
            ruta_foto
            and ruta_foto != "Sin foto"
            and os.path.exists(ruta_foto)
        ):
            with open(ruta_foto, "rb") as f:
                datos = f.read()

            tipo_mime, _ = mimetypes.guess_type(ruta_foto)
            if not tipo_mime:
                tipo_mime = "image/jpeg"

            maintype, subtype = tipo_mime.split("/", 1)

            msg.add_attachment(
                datos,
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(ruta_foto),
            )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)

    except Exception as e:
        print(f"Error al enviar correo: {e}")


def generar_link_whatsapp(numero, mensaje):
    texto = urllib.parse.quote(mensaje)
    return f"https://wa.me/{numero}?text={texto}"


def estado_stock(stock):
    stock = max(0, int(stock))

    if stock == 0:
        return "🔴 AGOTADO", "#dc2626"
    if stock <= 2:
        return "🟠 STOCK BAJO", "#ea580c"
    return "🟢 DISPONIBLE", "#16a34a"


def icono_producto(categoria):
    texto = str(categoria).lower()

    if "cama" in texto:
        return "🛏️"
    if "colchón" in texto or "colchon" in texto:
        return "💤"
    if "armario" in texto:
        return "🚪"
    if "pajarita" in texto:
        return "🎀"

    return "📦"


def base_categoria(categoria):
    return str(categoria).split(" - ")[0].strip()


def contar_apartados(df):
    if df.empty or "ESTADO" not in df.columns:
        return 0

    return int(
        df["ESTADO"]
        .astype(str)
        .str.contains("Apartado", case=False, na=False)
        .sum()
    )


# ============================================================
# LOGIN
# ============================================================

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False


if not st.session_state["autenticado"]:

    st.markdown(
        """
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
}

.login-box {
    max-width: 500px;
    margin: 90px auto 25px auto;
    padding: 45px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 28px;
    text-align: center;
    box-shadow: 0 25px 60px rgba(0,0,0,0.40);
}
</style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="login-box">
    <div style="font-size:70px;">🛏️</div>
    <div style="font-size:40px;font-weight:900;color:white;">
        LOCAL MESITAS
    </div>
    <div style="font-size:18px;color:#cbd5e1;margin-top:8px;">
        Sistema de ventas y administración
    </div>
    <div style="font-size:45px;margin-top:22px;">🔐</div>
    <div style="color:#94a3b8;">
        Ingrese su contraseña para continuar
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        clave = st.text_input(
            "🔑 Contraseña",
            type="password",
            key="login_password",
        )

        if st.button(
            "🚀 INGRESAR AL SISTEMA",
            use_container_width=True,
        ):
            if clave == CLAVE_ACCESO:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")

    st.stop()


# ============================================================
# CARGAR DATOS
# ============================================================

df_inv = cargar_inventario()
df_ventas = cargar_ventas()


# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    """
<style>
.stApp {
    background: #f1f5f9;
    font-family: 'Segoe UI', Arial, sans-serif;
}

.header-box {
    background: linear-gradient(135deg, #0f172a, #1e3a8a);
    padding: 32px;
    border-radius: 25px;
    color: white;
    text-align: center;
    margin-bottom: 22px;
    box-shadow: 0 12px 30px rgba(15,23,42,0.18);
}

.info-card {
    background: white;
    padding: 20px;
    border-radius: 20px;
    text-align: center;
    border: 1px solid #e2e8f0;
    box-shadow: 0 6px 18px rgba(15,23,42,0.07);
}

.product-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    padding: 20px 12px;
    text-align: center;
    min-height: 245px;
    box-shadow: 0 8px 25px rgba(15,23,42,0.08);
}

.receipt-card {
    background: white;
    padding: 28px;
    border-radius: 22px;
    border-left: 7px solid #2563eb;
    box-shadow: 0 8px 25px rgba(15,23,42,0.08);
}

.total-card {
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border: 2px solid #3b82f6;
    border-radius: 22px;
    padding: 24px;
    text-align: center;
}

.stButton > button {
    border-radius: 14px;
    min-height: 50px;
    font-weight: 700;
}

div[data-baseweb="tab-list"] {
    gap: 8px;
    background: #e2e8f0;
    padding: 8px;
    border-radius: 16px;
}

div[data-baseweb="tab"] {
    border-radius: 12px;
    font-weight: 700;
    padding: 10px 18px !important;
}

input, textarea {
    border-radius: 12px !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ENCABEZADO
# ============================================================

c_titulo, c_salir = st.columns([6, 1])

with c_salir:
    if st.button("🔒 Salir", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

st.markdown(
    """
<div class="header-box">
    <div style="font-size:44px;font-weight:900;">
        🛏️ LOCAL MESITAS
    </div>
    <div style="font-size:19px;color:#cbd5e1;margin-top:7px;">
        Sistema POS • Apartados • Inventario • Caja
    </div>
</div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# RESUMEN
# ============================================================

dinero_recibido = (
    float(df_ventas["ABONADO"].sum())
    if not df_ventas.empty
    else 0.0
)

operaciones = len(df_ventas)
apartados = contar_apartados(df_ventas)
stock_total = int(df_inv["STOCK"].sum()) if not df_inv.empty else 0

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        f"""
<div class="info-card">
    <div style="color:#64748b;font-weight:700;">💰 DINERO RECIBIDO</div>
    <div style="font-size:28px;font-weight:900;">${dinero_recibido:,.2f}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
<div class="info-card">
    <div style="color:#64748b;font-weight:700;">📦 STOCK TOTAL</div>
    <div style="font-size:28px;font-weight:900;">{stock_total}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
<div class="info-card">
    <div style="color:#64748b;font-weight:700;">🧾 OPERACIONES</div>
    <div style="font-size:28px;font-weight:900;">{operaciones}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f"""
<div class="info-card">
    <div style="color:#64748b;font-weight:700;">📦 APARTADOS ACTIVOS</div>
    <div style="font-size:28px;font-weight:900;">{apartados}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

st.write("")


# ============================================================
# ALERTA DE STOCK
# ============================================================

stock_critico = df_inv[df_inv["STOCK"] <= 2]

if not stock_critico.empty:
    lista_bajos = ", ".join(
        f"{r['CATEGORIA']} ({int(r['STOCK'])} ud.)"
        for _, r in stock_critico.iterrows()
    )

    st.warning(
        f"⚠️ **STOCK BAJO:** {lista_bajos}"
    )


# ============================================================
# PESTAÑAS
# ============================================================

tab_ops, tab_apartados, tab_inventario, tab_historial = st.tabs(
    [
        "⚡ Venta Directa",
        "📦 Apartados y Abonos",
        "🛠️ Inventario",
        "📜 Historial y Caja",
    ]
)


# ============================================================
# TAB 1 - VENTA DIRECTA
# ============================================================

with tab_ops:

    st.markdown(
        """
<div style="
background:linear-gradient(135deg,#ffffff,#eff6ff);
padding:25px;
border-radius:22px;
border:1px solid #dbeafe;
margin-bottom:20px;
">
<div style="font-size:32px;font-weight:900;color:#0f172a;">
⚡ Venta Directa
</div>
<div style="color:#64748b;font-size:16px;margin-top:5px;">
Selecciona un producto y registra la venta rápidamente.
</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    if df_inv.empty:
        st.info("📦 No hay productos en el inventario.")
    else:

        st.markdown("### 📦 Productos")

        columnas = st.columns(min(5, max(1, len(df_inv))))

        for idx, row in df_inv.iterrows():

            with columnas[idx % len(columnas)]:

                stock = max(0, int(row["STOCK"]))
                precio = float(row["PRECIO"])
                estado, color = estado_stock(stock)
                icono = icono_producto(row["CATEGORIA"])

                st.markdown(
                    f"""
<div class="product-card">
<div style="font-size:52px;">{icono}</div>

<div style="
font-size:18px;
font-weight:800;
color:#0f172a;
min-height:48px;
">
{row["CATEGORIA"]}
</div>

<div style="
font-size:32px;
font-weight:900;
color:#1e3a8a;
margin:8px 0;
">
{stock}
<span style="font-size:14px;color:#64748b;">ud.</span>
</div>

<div style="
font-size:20px;
font-weight:800;
">
${precio:,.2f}
</div>

<div style="
color:{color};
font-weight:800;
font-size:13px;
margin-top:10px;
">
{estado}
</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        st.markdown("### 🛒 Seleccionar producto")

        categorias = df_inv["CATEGORIA"].tolist()

        categoria_sel = st.selectbox(
            "📦 Producto",
            categorias,
            key="venta_producto",
        )

        fila = df_inv[
            df_inv["CATEGORIA"] == categoria_sel
        ].iloc[0]

        stock_disp = max(0, int(fila["STOCK"]))
        precio_unit = float(fila["PRECIO"])

        categoria_final = categoria_sel

        if "cama" in categoria_sel.lower():
            tipo_cama = st.selectbox(
                "🛏️ Tipo de cama",
                [
                    "Cama de 3 plazas tapizada",
                    "Cama de dos plazas tapizada",
                ],
                key="venta_tipo_cama",
            )

            categoria_final = (
                f"{categoria_sel} - {tipo_cama}"
            )

        if stock_disp <= 0:

            st.error(
                f"🔴 **{categoria_sel} está agotado.** "
                "Ingresa stock desde Inventario antes de vender."
            )

        else:

            with st.form("form_venta_rapida"):

                st.markdown("### 🧾 Datos de la venta")

                c1, c2, c3 = st.columns(3)

                with c1:
                    cant = st.number_input(
                        "🔢 Cantidad",
                        min_value=1,
                        max_value=stock_disp,
                        value=1,
                        step=1,
                    )

                with c2:
                    pago = st.selectbox(
                        "💳 Método de pago",
                        [
                            "Efectivo",
                            "Transferencia",
                            "Tarjeta",
                        ],
                    )

                with c3:
                    descuento = st.number_input(
                        "🏷️ Descuento ($)",
                        min_value=0.0,
                        max_value=10.0,
                        value=0.0,
                        step=1.0,
                    )

                st.markdown("### 👤 Datos del cliente")

                cliente = st.text_input(
                    "👤 Nombre del cliente",
                    value="Cliente General",
                )

                c4, c5 = st.columns(2)

                with c4:
                    cedula = st.text_input(
                        "🆔 Cédula / RUC",
                        value="S/N",
                    )

                with c5:
                    telefono = st.text_input(
                        "📞 Teléfono",
                        value="",
                    )

                correo = st.text_input(
                    "📧 Correo electrónico",
                    value="",
                )

                direccion = st.text_input(
                    "📍 Dirección de entrega",
                    value="",
                )

                foto = st.file_uploader(
                    "📸 Foto del producto (opcional)",
                    type=["jpg", "jpeg", "png"],
                    key="foto_venta",
                )

                subtotal = cant * precio_unit
                total = max(0.0, subtotal - descuento)

                st.markdown(
                    f"""
<div class="total-card">
<div style="font-size:15px;color:#64748b;font-weight:700;">
🧾 RESUMEN
</div>

<div style="
font-size:20px;
font-weight:800;
margin-top:8px;
">
{cant} × {categoria_final}
</div>

<div style="color:#64748b;margin-top:8px;">
Subtotal: ${subtotal:,.2f}
</div>

<div style="color:#dc2626;">
Descuento: -${descuento:,.2f}
</div>

<div style="
font-size:42px;
font-weight:900;
color:#1d4ed8;
margin-top:7px;
">
${total:,.2f}
</div>

<div style="color:#475569;">
💳 {pago}
</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

                st.write("")

                cobrar = st.form_submit_button(
                    "💰 COBRAR Y GENERAR RECIBO",
                    use_container_width=True,
                )

                if cobrar:

                    if cant > stock_disp:
                        st.error(
                            "❌ La cantidad supera el stock disponible."
                        )

                    elif descuento > 10:
                        st.error(
                            "❌ El descuento máximo permitido es $10."
                        )

                    elif not cliente.strip():
                        st.warning(
                            "⚠️ Ingresa el nombre del cliente."
                        )

                    else:

                        ruta_foto = guardar_foto(foto)

                        indice = df_inv[
                            df_inv["CATEGORIA"] == categoria_sel
                        ].index[0]

                        nuevo_stock = max(
                            0,
                            int(df_inv.loc[indice, "STOCK"]) - cant,
                        )

                        df_inv.loc[indice, "STOCK"] = nuevo_stock
                        guardar_csv_seguro(df_inv, FILE_INV)

                        nueva_venta = pd.DataFrame(
                            [
                                {
                                    "FECHA": datetime.now().strftime(
                                        "%Y-%m-%d %H:%M"
                                    ),
                                    "CATEGORIA": categoria_final,
                                    "CANTIDAD": cant,
                                    "PRECIO_UNITARIO": precio_unit,
                                    "TOTAL": total,
                                    "ABONADO": total,
                                    "SALDO_PENDIENTE": 0.0,
                                    "METODO_PAGO": pago,
                                    "CLIENTE": cliente,
                                    "CEDULA": cedula,
                                    "TELEFONO": telefono,
                                    "CORREO": correo,
                                    "DIRECCION": direccion,
                                    "ESTADO": "Pagado y Entregado",
                                    "FOTO": ruta_foto,
                                }
                            ]
                        )

                        df_ventas = pd.concat(
                            [df_ventas, nueva_venta],
                            ignore_index=True,
                        )

                        guardar_csv_seguro(
                            df_ventas,
                            FILE_VENTAS,
                        )

                        fecha = datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        )

                        cuerpo_mail = (
                            "Nueva Venta Registrada\n\n"
                            f"Cliente: {cliente}\n"
                            f"Producto: {cant}x {categoria_final}\n"
                            f"Descuento: ${descuento:,.2f}\n"
                            f"Total: ${total:,.2f}\n"
                            f"Método: {pago}\n"
                            f"Dirección: {direccion}\n"
                            f"Fecha: {fecha}"
                        )

                        enviar_correo_venta(
                            correo,
                            "🧾 Recibo de Compra - Local Mesitas",
                            cuerpo_mail,
                            ruta_foto,
                        )

                        st.session_state["ultima_venta_ws"] = {
                            "mensaje": (
                                "🚨 *NUEVA VENTA REGISTRADA* 🛏️\n\n"
                                f"👤 *Cliente:* {cliente}\n"
                                f"📞 *Tel:* {telefono or 'N/A'}\n"
                                f"📦 *Producto:* {cant}x {categoria_final}\n"
                                f"🏷️ *Descuento:* ${descuento:,.2f}\n"
                                f"💰 *Total:* ${total:,.2f}\n"
                                f"💳 *Pago:* {pago}\n"
                                f"📍 *Dirección:* {direccion}\n"
                                f"📅 *Fecha:* {fecha}"
                            )
                        }

                        st.session_state["mensaje_exito"] = (
                            f"🎉 Venta registrada correctamente. "
                            f"Stock restante: {nuevo_stock} unidades."
                        )

                        st.rerun()


# ============================================================
# WHATSAPP
# ============================================================

if "ultima_venta_ws" in st.session_state:

    mensaje = st.session_state["ultima_venta_ws"]["mensaje"]

    link1 = generar_link_whatsapp(NUMERO_1, mensaje)
    link2 = generar_link_whatsapp(NUMERO_2, mensaje)

    st.markdown(
        f"""
<div style="
background:#ecfdf5;
border:2px solid #22c55e;
padding:25px;
border-radius:20px;
text-align:center;
margin-top:20px;
">
<div style="
font-size:27px;
font-weight:900;
color:#15803d;
">
📱 Notificación lista
</div>

<div style="color:#475569;margin:8px 0 20px 0;">
La operación fue registrada. Puedes enviar el reporte.
</div>

<a href="{link1}" target="_blank"
style="
background:#25d366;
color:white;
padding:14px 20px;
border-radius:12px;
text-decoration:none;
font-weight:800;
display:inline-block;
margin:5px;
">
💬 WhatsApp 1
</a>

<a href="{link2}" target="_blank"
style="
background:#128c7e;
color:white;
padding:14px 20px;
border-radius:12px;
text-decoration:none;
font-weight:800;
display:inline-block;
margin:5px;
">
💬 WhatsApp 2
</a>
</div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("✖️ Ocultar notificación", key="ocultar_ws"):
        del st.session_state["ultima_venta_ws"]
        st.rerun()


if "mensaje_exito" in st.session_state:
    st.success(st.session_state["mensaje_exito"])

    if st.button("✖️ Cerrar mensaje", key="cerrar_exito"):
        del st.session_state["mensaje_exito"]
        st.rerun()


# ============================================================
# TAB 2 - APARTADOS Y ABONOS
# ============================================================

with tab_apartados:

    st.markdown("## 📦 Apartados y Abonos")

    st.caption(
        "Registra clientes, abonos, saldo pendiente y recibos."
    )

    with st.expander(
        "➕ CREAR NUEVO APARTADO",
        expanded=True,
    ):

        if df_inv.empty:
            st.info("No hay productos.")
        else:

            ap_cat = st.selectbox(
                "📦 Producto",
                df_inv["CATEGORIA"].tolist(),
                key="apartado_producto",
            )

            fila_ap = df_inv[
                df_inv["CATEGORIA"] == ap_cat
            ].iloc[0]

            ap_stock = max(
                0,
                int(fila_ap["STOCK"])
            )

            ap_precio = float(
                fila_ap["PRECIO"]
            )

            ap_categoria_final = ap_cat

            if "cama" in ap_cat.lower():
                tipo_ap = st.selectbox(
                    "🛏️ Tipo de cama",
                    [
                        "Cama de 3 plazas tapizada",
                        "Cama de dos plazas tapizada",
                    ],
                    key="apartado_tipo_cama",
                )

                ap_categoria_final = (
                    f"{ap_cat} - {tipo_ap}"
                )

            with st.form("form_nuevo_apartado"):

                c1, c2 = st.columns(2)

                with c1:
                    ap_cant = st.number_input(
                        "🔢 Cantidad",
                        min_value=1,
                        max_value=max(1, ap_stock),
                        value=1,
                        step=1,
                    )

                with c2:
                    ap_abono = st.number_input(
                        "💵 Abono inicial ($)",
                        min_value=0.0,
                        value=10.0,
                        step=5.0,
                    )

                ap_cliente = st.text_input(
                    "👤 Nombre y apellido"
                )

                c3, c4 = st.columns(2)

                with c3:
                    ap_ced = st.text_input(
                        "🆔 Cédula / DNI"
                    )

                with c4:
                    ap_tel = st.text_input(
                        "📞 Teléfono"
                    )

                ap_corr = st.text_input(
                    "📧 Correo electrónico"
                )

                ap_dir = st.text_input(
                    "📍 Dirección"
                )

                ap_foto = st.file_uploader(
                    "📸 Foto del producto",
                    type=["jpg", "jpeg", "png"],
                    key="foto_apartado",
                )

                total_ap = ap_cant * ap_precio
                saldo_ap = max(
                    0.0,
                    total_ap - ap_abono
                )

                st.markdown(
                    f"""
<div class="total-card">
<div style="font-weight:800;color:#64748b;">
RESUMEN DEL APARTADO
</div>
<div style="font-size:28px;font-weight:900;">
${total_ap:,.2f}
</div>
<div style="color:#16a34a;">
Abono: ${ap_abono:,.2f}
</div>
<div style="
color:#dc2626;
font-size:22px;
font-weight:900;
">
Saldo: ${saldo_ap:,.2f}
</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

                guardar_ap = st.form_submit_button(
                    "💾 GUARDAR APARTADO",
                    use_container_width=True,
                )

                if guardar_ap:

                    if not ap_cliente.strip():
                        st.warning(
                            "⚠️ Ingresa el nombre del cliente."
                        )

                    elif ap_abono > total_ap:
                        st.error(
                            "❌ El abono no puede superar el total."
                        )

                    elif ap_cant > ap_stock:
                        st.error(
                            "❌ No hay suficiente stock."
                        )

                    else:

                        ruta_foto_ap = guardar_foto(
                            ap_foto,
                            "ap_",
                        )

                        if saldo_ap <= 0:
                            estado_ap = "Pagado y Entregado"
                        else:
                            estado_ap = "Apartado (Pendiente)"

                        nueva_ap = pd.DataFrame(
                            [
                                {
                                    "FECHA": datetime.now().strftime(
                                        "%Y-%m-%d %H:%M"
                                    ),
                                    "CATEGORIA": ap_categoria_final,
                                    "CANTIDAD": ap_cant,
                                    "PRECIO_UNITARIO": ap_precio,
                                    "TOTAL": total_ap,
                                    "ABONADO": ap_abono,
                                    "SALDO_PENDIENTE": saldo_ap,
                                    "METODO_PAGO": "Efectivo",
                                    "CLIENTE": ap_cliente,
                                    "CEDULA": ap_ced,
                                    "TELEFONO": ap_tel,
                                    "CORREO": ap_corr,
                                    "DIRECCION": ap_dir,
                                    "ESTADO": estado_ap,
                                    "FOTO": ruta_foto_ap,
                                }
                            ]
                        )

                        # Si paga todo al crear el apartado,
                        # se descuenta inmediatamente.
                        if saldo_ap <= 0:

                            indice = df_inv[
                                df_inv["CATEGORIA"] == ap_cat
                            ].index[0]

                            df_inv.loc[
                                indice,
                                "STOCK"
                            ] = max(
                                0,
                                int(
                                    df_inv.loc[
                                        indice,
                                        "STOCK"
                                    ]
                                ) - ap_cant,
                            )

                            guardar_csv_seguro(
                                df_inv,
                                FILE_INV,
                            )

                        df_ventas = pd.concat(
                            [df_ventas, nueva_ap],
                            ignore_index=True,
                        )

                        guardar_csv_seguro(
                            df_ventas,
                            FILE_VENTAS,
                        )

                        cuerpo = (
                            "Nuevo Apartado\n\n"
                            f"Cliente: {ap_cliente}\n"
                            f"Producto: {ap_cant}x {ap_categoria_final}\n"
                            f"Total: ${total_ap:,.2f}\n"
                            f"Abono: ${ap_abono:,.2f}\n"
                            f"Saldo: ${saldo_ap:,.2f}"
                        )

                        enviar_correo_venta(
                            ap_corr,
                            "🧾 Recibo de Apartado - Local Mesitas",
                            cuerpo,
                            ruta_foto_ap,
                        )

                        st.session_state["ultima_venta_ws"] = {
                            "mensaje": (
                                "📦 *NUEVO APARTADO REGISTRADO*\n\n"
                                f"👤 *Cliente:* {ap_cliente}\n"
                                f"📞 *Tel:* {ap_tel or 'N/A'}\n"
                                f"📦 *Producto:* {ap_cant}x {ap_categoria_final}\n"
                                f"💰 *Total:* ${total_ap:,.2f}\n"
                                f"📥 *Abono:* ${ap_abono:,.2f}\n"
                                f"🔴 *Saldo:* ${saldo_ap:,.2f}\n"
                                f"📌 *Estado:* {estado_ap}"
                            )
                        }

                        st.success(
                            "✅ Apartado guardado correctamente."
                        )

                        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Apartados activos")

    df_v = cargar_ventas()

    if df_v.empty:

        st.info("📭 No existen registros todavía.")

    else:

        pendientes = df_v[
            df_v["ESTADO"]
            .astype(str)
            .str.contains(
                "Apartado",
                case=False,
                na=False,
            )
        ]

        if pendientes.empty:

            st.success(
                "✨ No hay apartados pendientes."
            )

        else:

            opciones = [
                (
                    f"Fila {i} | "
                    f"{r['CLIENTE']} | "
                    f"{r['CATEGORIA']} | "
                    f"Saldo: ${float(r['SALDO_PENDIENTE']):,.2f}"
                )
                for i, r in pendientes.iterrows()
            ]

            seleccion = st.selectbox(
                "🔍 Selecciona un apartado",
                opciones,
                key="apartado_consulta",
            )

            idx = int(
                seleccion.split(" | ")[0]
                .replace("Fila ", "")
            )

            r = df_v.loc[idx]

            col_info, col_foto = st.columns([1.5, 1])

            with col_info:

                st.markdown(
                    f"""
<div class="receipt-card">
<div style="
font-size:27px;
font-weight:900;
color:#2563eb;
margin-bottom:15px;
">
🧾 RECIBO DE APARTADO
</div>

<div><b>📅 Fecha:</b> {r["FECHA"]}</div>
<div><b>👤 Cliente:</b> {r["CLIENTE"]}</div>
<div><b>📞 Teléfono:</b> {r["TELEFONO"]}</div>
<div><b>🆔 Cédula:</b> {r["CEDULA"]}</div>
<div><b>📍 Dirección:</b> {r["DIRECCION"]}</div>

<hr>

<div><b>📦 Producto:</b> {r["CANTIDAD"]}x {r["CATEGORIA"]}</div>
<div><b>💰 Total:</b> ${float(r["TOTAL"]):,.2f}</div>
<div style="color:#16a34a;">
<b>✅ Abonado:</b> ${float(r["ABONADO"]):,.2f}
</div>
<div style="
color:#dc2626;
font-size:24px;
font-weight:900;
margin-top:8px;
">
🔴 Saldo: ${float(r["SALDO_PENDIENTE"]):,.2f}
</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_foto:

                st.markdown("### 🖼️ Producto")

                foto_path = str(
                    r.get("FOTO", "Sin foto")
                )

                if (
                    foto_path != "Sin foto"
                    and os.path.exists(foto_path)
                ):
                    st.image(
                        foto_path,
                        caption=str(r["CATEGORIA"]),
                        use_container_width=True,
                    )
                else:
                    st.info("📷 Sin foto.")

            saldo_actual = float(
                r["SALDO_PENDIENTE"]
            )

            with st.form(
                f"form_abono_{idx}"
            ):

                st.markdown(
                    "### 💸 Registrar abono"
                )

                abono_hoy = st.number_input(
                    "💵 Dinero recibido",
                    min_value=0.0,
                    max_value=saldo_actual,
                    value=saldo_actual,
                    step=5.0,
                )

                registrar = st.form_submit_button(
                    "📥 REGISTRAR ABONO",
                    use_container_width=True,
                )

                if registrar:

                    nuevo_abonado = (
                        float(r["ABONADO"])
                        + abono_hoy
                    )

                    nuevo_saldo = max(
                        0.0,
                        saldo_actual - abono_hoy,
                    )

                    df_v.loc[
                        idx,
                        "ABONADO"
                    ] = nuevo_abonado

                    df_v.loc[
                        idx,
                        "SALDO_PENDIENTE"
                    ] = nuevo_saldo

                    if nuevo_saldo <= 0:

                        df_v.loc[
                            idx,
                            "ESTADO"
                        ] = "Pagado y Entregado"

                        producto_base = base_categoria(
                            r["CATEGORIA"]
                        )

                        if producto_base in df_inv["CATEGORIA"].values:

                            indice_prod = df_inv[
                                df_inv["CATEGORIA"]
                                == producto_base
                            ].index[0]

                            cantidad_entregar = int(
                                r["CANTIDAD"]
                            )

                            stock_nuevo = max(
                                0,
                                int(
                                    df_inv.loc[
                                        indice_prod,
                                        "STOCK"
                                    ]
                                )
                                - cantidad_entregar,
                            )

                            df_inv.loc[
                                indice_prod,
                                "STOCK"
                            ] = stock_nuevo

                            guardar_csv_seguro(
                                df_inv,
                                FILE_INV,
                            )

                        mensaje_estado = (
                            "🎉 DEUDA SALDADA. "
                            "Producto listo para entregar."
                        )

                    else:

                        df_v.loc[
                            idx,
                            "ESTADO"
                        ] = "Apartado (Pendiente)"

                        mensaje_estado = (
                            f"✅ Abono registrado. "
                            f"Nuevo saldo: ${nuevo_saldo:,.2f}"
                        )

                    guardar_csv_seguro(
                        df_v,
                        FILE_VENTAS,
                    )

                    cuerpo = (
                        f"Abono registrado para {r['CLIENTE']}\n"
                        f"Abono: ${abono_hoy:,.2f}\n"
                        f"Saldo pendiente: ${nuevo_saldo:,.2f}\n"
                        f"Estado: {df_v.loc[idx, 'ESTADO']}"
                    )

                    enviar_correo_venta(
                        r["CORREO"],
                        "🧾 Comprobante de Abono - Local Mesitas",
                        cuerpo,
                        r["FOTO"],
                    )

                    st.session_state["ultima_venta_ws"] = {
                        "mensaje": (
                            "💵 *NUEVO ABONO REGISTRADO*\n\n"
                            f"👤 *Cliente:* {r['CLIENTE']}\n"
                            f"📥 *Abono:* ${abono_hoy:,.2f}\n"
                            f"🔴 *Nuevo saldo:* ${nuevo_saldo:,.2f}\n"
                            f"📌 *Estado:* {df_v.loc[idx, 'ESTADO']}"
                        )
                    }

                    st.session_state["mensaje_exito"] = mensaje_estado

                    st.rerun()


# ============================================================
# TAB 3 - INVENTARIO
# ============================================================

with tab_inventario:

    st.markdown("## 🛠️ Inventario")

    st.caption(
        "Área protegida para modificar productos, stock y precios."
    )

    clave_admin = st.text_input(
        "🔐 Clave de administrador",
        type="password",
        key="clave_inventario",
    )

    if clave_admin == CLAVE_ADMIN:

        st.success("✅ Acceso de administrador concedido.")

        c1, c2 = st.columns(2)

        with c1:

            st.markdown("### ✏️ Modificar producto")

            if not df_inv.empty:

                producto_mod = st.selectbox(
                    "📦 Producto",
                    df_inv["CATEGORIA"].tolist(),
                    key="producto_modificar",
                )

                fila_mod = df_inv[
                    df_inv["CATEGORIA"]
                    == producto_mod
                ].iloc[0]

                st.info(
                    f"Stock actual: **{int(fila_mod['STOCK'])}** | "
                    f"Precio: **${float(fila_mod['PRECIO']):,.2f}**"
                )

                cambio_stock = st.number_input(
                    "📦 Sumar / restar stock",
                    value=0,
                    step=1,
                    key="cambio_stock",
                )

                nuevo_precio = st.number_input(
                    "💰 Nuevo precio",
                    min_value=0.0,
                    value=float(fila_mod["PRECIO"]),
                    step=1.0,
                    key="nuevo_precio",
                )

                if st.button(
                    "💾 ACTUALIZAR",
                    use_container_width=True,
                ):

                    indice = df_inv[
                        df_inv["CATEGORIA"]
                        == producto_mod
                    ].index[0]

                    df_inv.loc[
                        indice,
                        "STOCK"
                    ] = max(
                        0,
                        int(
                            df_inv.loc[
                                indice,
                                "STOCK"
                            ]
                        ) + cambio_stock,
                    )

                    df_inv.loc[
                        indice,
                        "PRECIO"
                    ] = max(
                        0.0,
                        nuevo_precio,
                    )

                    guardar_csv_seguro(
                        df_inv,
                        FILE_INV,
                    )

                    st.success(
                        "✅ Inventario actualizado."
                    )

                    st.rerun()

        with c2:

            st.markdown("### ➕ Agregar producto")

            opciones_base = (
                df_inv["CATEGORIA"].tolist()
                if not df_inv.empty
                else []
            )

            opciones_base.append(
                "✨ [Crear categoría nueva]"
            )

            categoria_base = st.selectbox(
                "📂 Categoría",
                opciones_base,
                key="categoria_base",
            )

            if (
                categoria_base
                == "✨ [Crear categoría nueva]"
            ):

                nombre_producto = st.text_input(
                    "Nombre del producto"
                )

            else:

                nombre_sub = st.text_input(
                    "Nombre del subproducto",
                    placeholder="Ej: De 3 plazas",
                )

                if nombre_sub.strip():

                    nombre_producto = (
                        f"{categoria_base} - "
                        f"{nombre_sub.strip()}"
                    )

                else:

                    nombre_producto = categoria_base

            stock_inicial = st.number_input(
                "📦 Stock inicial",
                min_value=0,
                value=5,
                step=1,
                key="stock_inicial",
            )

            precio_inicial = st.number_input(
                "💰 Precio",
                min_value=0.0,
                value=50.0,
                step=1.0,
                key="precio_inicial",
            )

            if st.button(
                "➕ CREAR PRODUCTO",
                use_container_width=True,
            ):

                nombre_producto = nombre_producto.strip()

                if not nombre_producto:

                    st.warning(
                        "⚠️ Ingresa un nombre."
                    )

                elif (
                    nombre_producto
                    in df_inv["CATEGORIA"].values
                ):

                    st.error(
                        "❌ Ese producto ya existe."
                    )

                else:

                    nuevo = pd.DataFrame(
                        [
                            {
                                "CATEGORIA": nombre_producto,
                                "STOCK": stock_inicial,
                                "PRECIO": precio_inicial,
                            }
                        ]
                    )

                    df_inv = pd.concat(
                        [df_inv, nuevo],
                        ignore_index=True,
                    )

                    guardar_csv_seguro(
                        df_inv,
                        FILE_INV,
                    )

                    st.success(
                        "🎉 Producto creado."
                    )

                    st.rerun()

        st.markdown("---")

        st.markdown("### 📊 Inventario actual")

        if df_inv.empty:

            st.info("No hay productos.")

        else:

            for _, row in df_inv.iterrows():

                estado, color = estado_stock(
                    row["STOCK"]
                )

                c1, c2, c3, c4 = st.columns(
                    [3, 1, 1, 2]
                )

                with c1:
                    st.write(
                        f"{icono_producto(row['CATEGORIA'])} "
                        f"**{row['CATEGORIA']}**"
                    )

                with c2:
                    st.write(
                        f"{int(row['STOCK'])} ud."
                    )

                with c3:
                    st.write(
                        f"${float(row['PRECIO']):,.2f}"
                    )

                with c4:
                    st.markdown(
                        f"<span style='color:{color};font-weight:800;'>{estado}</span>",
                        unsafe_allow_html=True,
                    )

        st.markdown("---")

        st.markdown("### 🗑️ Eliminar producto")

        if not df_inv.empty:

            borrar_producto = st.selectbox(
                "📦 Producto a eliminar",
                df_inv["CATEGORIA"].tolist(),
                key="borrar_producto",
            )

            confirmar = st.checkbox(
                "⚠️ Confirmo que quiero eliminar este producto.",
                key="confirmar_producto",
            )

            if st.button(
                "❌ ELIMINAR PRODUCTO",
                use_container_width=True,
            ):

                if not confirmar:

                    st.warning(
                        "Debes confirmar la eliminación."
                    )

                else:

                    df_inv = df_inv[
                        df_inv["CATEGORIA"]
                        != borrar_producto
                    ].reset_index(drop=True)

                    guardar_csv_seguro(
                        df_inv,
                        FILE_INV,
                    )

                    st.success(
                        f"✅ Producto eliminado: {borrar_producto}"
                    )

                    st.rerun()

    elif clave_admin:

        st.error("❌ Clave incorrecta.")


# ============================================================
# TAB 4 - HISTORIAL Y CAJA
# ============================================================

with tab_historial:

    st.markdown("## 📜 Historial y Caja")

    df_h = cargar_ventas()

    if df_h.empty:

        st.info("📭 No existen operaciones todavía.")

    else:

        total_caja = float(
            df_h["ABONADO"].sum()
        )

        total_operaciones = len(df_h)
        total_apartados = contar_apartados(df_h)

        h1, h2, h3 = st.columns(3)

        with h1:
            st.metric(
                "💰 Dinero recibido",
                f"${total_caja:,.2f}",
            )

        with h2:
            st.metric(
                "🧾 Operaciones",
                total_operaciones,
            )

        with h3:
            st.metric(
                "📦 Apartados activos",
                total_apartados,
            )

        st.markdown("---")

        st.markdown("### 🔎 Buscar")

        f1, f2 = st.columns(2)

        with f1:
            buscar_cliente = st.text_input(
                "👤 Cliente",
                key="buscar_cliente",
            )

        with f2:
            buscar_producto = st.text_input(
                "📦 Producto",
                key="buscar_producto",
            )

        df_filtrado = df_h.copy()

        if buscar_cliente.strip():

            df_filtrado = df_filtrado[
                df_filtrado["CLIENTE"]
                .str.contains(
                    buscar_cliente,
                    case=False,
                    na=False,
                )
            ]

        if buscar_producto.strip():

            df_filtrado = df_filtrado[
                df_filtrado["CATEGORIA"]
                .str.contains(
                    buscar_producto,
                    case=False,
                    na=False,
                )
            ]

        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        st.markdown("### 🖼️ Ver foto")

        opciones_fotos = [
            (
                f"Fila {i} | "
                f"{r['FECHA']} | "
                f"{r['CLIENTE']} | "
                f"{r['CATEGORIA']}"
            )
            for i, r in df_h.iterrows()
        ]

        if opciones_fotos:

            foto_sel = st.selectbox(
                "Selecciona un registro",
                opciones_fotos,
                key="foto_historial",
            )

            idx_foto = int(
                foto_sel.split(" | ")[0]
                .replace("Fila ", "")
            )

            ruta_foto_hist = str(
                df_h.loc[idx_foto].get(
                    "FOTO",
                    "Sin foto",
                )
            )

            if (
                ruta_foto_hist != "Sin foto"
                and os.path.exists(ruta_foto_hist)
            ):

                st.image(
                    ruta_foto_hist,
                    caption=str(
                        df_h.loc[idx_foto]["CATEGORIA"]
                    ),
                    width=400,
                )

            else:

                st.info(
                    "📷 Este registro no tiene foto."
                )

        st.markdown("---")

        st.markdown("### 📥 Descargar reporte")

        st.download_button(
            "📥 DESCARGAR CSV",
            df_h.to_csv(index=False).encode("utf-8"),
            "reporte_local_mesitas.csv",
            "text/csv",
            use_container_width=True,
        )

        st.markdown("---")

        st.markdown(
            "### 🗑️ Eliminar registro "
            "(solo para corregir errores)"
        )

        clave_borrar = st.text_input(
            "🔐 Clave de administrador",
            type="password",
            key="clave_borrar",
        )

        if clave_borrar == CLAVE_ADMIN:

            opciones_borrar = [
                (
                    f"Fila {i} | "
                    f"{r['FECHA']} | "
                    f"{r['CLIENTE']} | "
                    f"Total: ${float(r['TOTAL']):,.2f}"
                )
                for i, r in df_h.iterrows()
            ]

            registro_borrar = st.selectbox(
                "Selecciona el registro",
                opciones_borrar,
                key="registro_borrar",
            )

            confirmar_borrar = st.checkbox(
                "⚠️ Confirmo que deseo eliminar este registro.",
                key="confirmar_borrar",
            )

            if st.button(
                "❌ BORRAR REGISTRO",
                use_container_width=True,
            ):

                if not confirmar_borrar:

                    st.warning(
                        "Debes confirmar la eliminación."
                    )

                else:

                    idx_borrar = int(
                        registro_borrar.split(" | ")[0]
                        .replace("Fila ", "")
                    )

                    foto_borrar = str(
                        df_h.loc[idx_borrar].get(
                            "FOTO",
                            "Sin foto",
                        )
                    )

                    if (
                        foto_borrar != "Sin foto"
                        and os.path.exists(foto_borrar)
                    ):
                        try:
                            os.remove(foto_borrar)
                        except Exception:
                            pass

                    df_h = df_h.drop(
                        idx_borrar
                    ).reset_index(drop=True)

                    guardar_csv_seguro(
                        df_h,
                        FILE_VENTAS,
                    )

                    st.success(
                        "✅ Registro eliminado correctamente."
                    )

                    st.rerun()

        elif clave_borrar:

            st.error("❌ Clave incorrecta.")


# ============================================================
# PIE DE PÁGINA
# ============================================================

st.markdown(
    """
<div style="
text-align:center;
margin-top:40px;
padding:20px;
color:#64748b;
border-top:1px solid #e2e8f0;
">
<b>🛏️ LOCAL MESITAS</b><br>
Sistema POS • Inventario • Apartados • Caja
</div>
    """,
    unsafe_allow_html=True,
)
