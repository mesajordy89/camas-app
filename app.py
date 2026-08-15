from datetime import datetime
from email.message import EmailMessage
import mimetypes
import os
import smtplib
import textwrap
import urllib.parse

import pandas as pd
import streamlit as st


# ============================================================
#                 LOCAL MESITAS - SISTEMA POS
#                     VERSIÓN DINÁMICA & POS
# ============================================================

st.set_page_config(
    page_title="Local Mesitas - Sistema POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
#                 CONFIGURACIÓN
# ============================================================

CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1234"

NUMERO_1 = "593990847819"
NUMERO_2 = "593983576800"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"
CARPETA_FOTOS = "fotos_ventas"

os.makedirs(CARPETA_FOTOS, exist_ok=True)

COLUMNAS_VENTAS = [
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


# ============================================================
#            FUNCIÓN PARA HTML & ESTILOS DINÁMICOS
# ============================================================

def html(contenido):
    """Permite renderizar HTML limpio en Streamlit."""
    texto_limpio = textwrap.dedent(contenido).strip()
    texto_limpio = " ".join(line.strip() for line in texto_limpio.splitlines())
    return st.markdown(
        texto_limpio,
        unsafe_allow_html=True,
    )


# ============================================================
#                 FUNCIONES DE DATOS
# ============================================================

def guardar_csv(df, ruta):
    df.to_csv(ruta, index=False, encoding="utf-8-sig")


def normalizar_inventario(df):
    if "CATEGORIA" not in df.columns:
        df["CATEGORIA"] = ""
    if "STOCK" not in df.columns:
        df["STOCK"] = 0
    if "PRECIO" not in df.columns:
        df["PRECIO"] = 0.0

    df["CATEGORIA"] = df["CATEGORIA"].fillna("").astype(str).str.strip()
    df["STOCK"] = pd.to_numeric(df["STOCK"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    df["PRECIO"] = pd.to_numeric(df["PRECIO"], errors="coerce").fillna(0.0).clip(lower=0)

    df = df[df["CATEGORIA"] != ""].reset_index(drop=True)
    return df[["CATEGORIA", "STOCK", "PRECIO"]]


def normalizar_ventas(df):
    for columna in COLUMNAS_VENTAS:
        if columna in df.columns:
            continue
        if columna == "ABONADO":
            df[columna] = pd.to_numeric(df["TOTAL"], errors="coerce").fillna(0.0) if "TOTAL" in df.columns else 0.0
        elif columna == "SALDO_PENDIENTE":
            df[columna] = 0.0
        elif columna == "ESTADO":
            df[columna] = "Pagado y Entregado"
        elif columna == "DIRECCION":
            df[columna] = "S/N"
        elif columna == "FOTO":
            df[columna] = "Sin foto"
        else:
            df[columna] = ""

    for columna in ["CANTIDAD", "PRECIO_UNITARIO", "TOTAL", "ABONADO", "SALDO_PENDIENTE"]:
        df[columna] = pd.to_numeric(df[columna], errors="coerce").fillna(0.0)

    df["CANTIDAD"] = df["CANTIDAD"].astype(int).clip(lower=0)
    for columna in ["PRECIO_UNITARIO", "TOTAL", "ABONADO", "SALDO_PENDIENTE"]:
        df[columna] = df[columna].clip(lower=0)

    for columna in ["FECHA", "CATEGORIA", "METODO_PAGO", "CLIENTE", "CEDULA", "TELEFONO", "CORREO", "DIRECCION", "ESTADO", "FOTO"]:
        df[columna] = df[columna].fillna("").astype(str)

    return df[COLUMNAS_VENTAS]


def cargar_inventario():
    if os.path.exists(FILE_INV):
        try:
            df = pd.read_csv(FILE_INV, encoding="utf-8-sig")
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    df = normalizar_inventario(df)
    guardar_csv(df, FILE_INV)
    return df


def cargar_ventas():
    if os.path.exists(FILE_VENTAS):
        try:
            df = pd.read_csv(FILE_VENTAS, encoding="utf-8-sig")
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    df = normalizar_ventas(df)
    guardar_csv(df, FILE_VENTAS)
    return df


# ============================================================
#                 FOTOS & WHATSAPP & CORREO
# ============================================================

def guardar_foto(archivo, prefijo=""):
    if archivo is None:
        return "Sin foto"
    nombre = f"{prefijo}{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{os.path.basename(archivo.name)}"
    ruta = os.path.join(CARPETA_FOTOS, nombre)
    try:
        with open(ruta, "wb") as archivo_salida:
            archivo_salida.write(archivo.getbuffer())
        return ruta
    except Exception:
        return "Sin foto"


def generar_link_whatsapp(numero, mensaje):
    texto = urllib.parse.quote(mensaje)
    return f"https://wa.me/{numero}?text={texto}"


def enviar_correo_venta(destinatario, asunto, cuerpo, ruta_foto=None):
    if not destinatario or "@" not in str(destinatario):
        return
    try:
        remitente = st.secrets["EMAIL_USER"]
        password = st.secrets["EMAIL_PASS"]
    except Exception:
        return

    try:
        mensaje = EmailMessage()
        mensaje["Subject"] = asunto
        mensaje["From"] = remitente
        mensaje["To"] = destinatario
        mensaje.set_content(cuerpo)

        if ruta_foto and ruta_foto != "Sin foto" and os.path.exists(ruta_foto):
            with open(ruta_foto, "rb") as f:
                datos = f.read()
            tipo_mime, _ = mimetypes.guess_type(ruta_foto)
            if not tipo_mime:
                tipo_mime = "image/jpeg"
            maintype, subtype = tipo_mime.split("/", 1)
            mensaje.add_attachment(datos, maintype=maintype, subtype=subtype, filename=os.path.basename(ruta_foto))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(mensaje)
    except Exception as error:
        print(f"Error al enviar correo: {error}")


# ============================================================
#                 FUNCIONES VISUALES
# ============================================================

def obtener_icono(categoria):
    texto = str(categoria).lower()
    if "combo" in texto:
        return "🎁"
    if "cama" in texto:
        return "🛏️"
    if "colchon" in texto or "colchón" in texto:
        return "💤"
    if "armario" in texto:
        return "🚪"
    if "pajarita" in texto:
        return "🎀"
    return "📦"


def estado_stock(stock):
    stock = max(0, int(stock))
    if stock == 0:
        return ("🔴 AGOTADO", "#ef4444")
    if stock <= 2:
        return ("🟠 POCO STOCK", "#f97316")
    return ("🟢 DISPONIBLE", "#10b981")


def contar_apartados(df):
    if df.empty or "ESTADO" not in df.columns:
        return 0
    return int(df["ESTADO"].astype(str).str.contains("Apartado", case=False, na=False).sum())


# ============================================================
#                 PRODUCTOS / SUBPRODUCTOS
# ============================================================

def es_subproducto(nombre):
    return " - " in str(nombre)


def base_producto(categoria):
    return str(categoria).split(" - ")[0].strip()


def obtener_subproductos(df, principal):
    prefijo = str(principal).strip() + " - "
    return df[df["CATEGORIA"].astype(str).str.startswith(prefijo, na=False)].copy()


def es_categoria_principal(df, nombre):
    nombre = str(nombre).strip()
    return not obtener_subproductos(df, nombre).empty


def producto_es_vendible(df, nombre):
    nombre = str(nombre).strip()
    if es_subproducto(nombre):
        return True
    return not es_categoria_principal(df, nombre)


def obtener_productos_vendibles(df):
    return [nombre for nombre in df["CATEGORIA"].tolist() if producto_es_vendible(df, nombre)]


def existe_producto(df, nombre):
    return nombre.strip().lower() in df["CATEGORIA"].astype(str).str.strip().str.lower().values


# ============================================================
#                 LOGIN
# ============================================================

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    html(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311b92 100%);
        }
        .login-box {
            max-width:480px;
            margin:60px auto 20px auto;
            padding:40px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 28px;
            text-align:center;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            backdrop-filter: blur(16px);
        }
        .login-title {
            font-size: 38px;
            color: white;
            font-weight: 900;
            letter-spacing: 1px;
        }
        .login-subtitle {
            font-size: 16px;
            color: #cbd5e1;
            margin-top: 6px;
        }
        </style>
        """
    )

    html(
        """
        <div class="login-box">
            <div style="font-size:75px; transform: scale(1); transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.15)'" onmouseout="this.style.transform='scale(1)'">
                🛏️
            </div>
            <div class="login-title">LOCAL MESITAS</div>
            <div class="login-subtitle">Sistema POS Móvil & Administración</div>
            <div style="font-size:42px; margin-top:20px;">🔐</div>
            <div style="color:#94a3b8; font-size:15px; margin-top:5px;">Escriba su clave de acceso para continuar</div>
        </div>
        """
    )

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        clave = st.text_input("🔑 Contraseña", type="password", key="clave_login")
        if st.button("🚀 INGRESAR AL SISTEMA", use_container_width=True):
            if clave == CLAVE_ACCESO:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")
    st.stop()


# ============================================================
#                 CARGAR INFORMACIÓN
# ============================================================

df_inv = cargar_inventario()
df_ventas = cargar_ventas()


# ============================================================
#                 ESTILOS GENERALES
# ============================================================

html(
    """
    <style>
    .stApp {
        background: #f8fafc;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Encabezado principal */
    .header-box {
        background: linear-gradient(135deg, #1e293b, #3b82f6);
        padding: 28px;
        border-radius: 24px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(30, 41, 59, 0.25);
    }

    /* Tarjetas de Métricas */
    .metric-card {
        background: white;
        padding: 18px;
        border-radius: 18px;
        text-align: center;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }

    /* Tarjetas de Producto */
    .product-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 20px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 6px 16px rgba(0,0,0,0.04);
        margin-bottom: 12px;
        transition: all 0.2s ease-in-out;
    }
    .product-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 10px 22px rgba(59, 130, 246, 0.15);
        transform: scale(1.02);
    }

    /* Botones dinámicos globales */
    div.stButton > button {
        border-radius: 14px !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        padding: 12px 20px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.15) !important;
    }
    div.stButton > button:active {
        transform: translateY(1px) !important;
    }

    /* Pestañas (Tabs) estilo moderno */
    div[data-baseweb="tab-list"] {
        gap: 8px;
        background: #e2e8f0;
        padding: 8px;
        border-radius: 18px;
    }

    div[data-baseweb="tab"] {
        border-radius: 12px;
        font-weight: 800;
        padding: 10px 18px !important;
        font-size: 15px !important;
        color: #475569;
    }

    div[aria-selected="true"] {
        background: white !important;
        color: #2563eb !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    </style>
    """
)


# ============================================================
#                 ENCABEZADO Y SALIR
# ============================================================

col_titulo, col_salir = st.columns([6, 1])

with col_salir:
    if st.button("🔒 SALIR", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

html(
    """
    <div class="header-box">
        <div style="font-size:42px; font-weight:900;">🛏️ LOCAL MESITAS</div>
        <div style="font-size:18px; color:#e2e8f0; margin-top:4px;">Sistema Móvil POS • Ventas • Apartados • Caja</div>
    </div>
    """
)


# ============================================================
#                 RESUMEN Y MÉTRICAS
# ============================================================

dinero_recibido = float(df_ventas["ABONADO"].sum()) if not df_ventas.empty else 0.0
total_operaciones = len(df_ventas)
total_apartados = contar_apartados(df_ventas)
total_stock = int(df_inv["STOCK"].sum()) if not df_inv.empty else 0

r1, r2, r3, r4 = st.columns(4)

with r1:
    html(f"""
    <div class="metric-card">
        <div style="font-size:13px; color:#64748b; font-weight:800;">💰 DINERO RECIBIDO</div>
        <div style="font-size:26px; font-weight:900; color:#10b981;">${dinero_recibido:,.2f}</div>
    </div>
    """)

with r2:
    html(f"""
    <div class="metric-card">
        <div style="font-size:13px; color:#64748b; font-weight:800;">📦 EN STOCK</div>
        <div style="font-size:26px; font-weight:900; color:#3b82f6;">{total_stock} ud.</div>
    </div>
    """)

with r3:
    html(f"""
    <div class="metric-card">
        <div style="font-size:13px; color:#64748b; font-weight:800;">🧾 OPERACIONES</div>
        <div style="font-size:26px; font-weight:900; color:#8b5cf6;">{total_operaciones}</div>
    </div>
    """)

with r4:
    html(f"""
    <div class="metric-card">
        <div style="font-size:13px; color:#64748b; font-weight:800;">📌 APARTADOS</div>
        <div style="font-size:26px; font-weight:900; color:#f97316;">{total_apartados}</div>
    </div>
    """)

st.write("")


# ============================================================
#                 PESTAÑAS PRINCIPALES
# ============================================================

tab_venta, tab_apartado, tab_inventario, tab_historial = st.tabs(
    ["⚡ VENDER", "📦 APARTADOS", "🛠️ INVENTARIO", "📜 HISTORIAL"]
)


# ============================================================
#                 TAB 1 - VENDER
# ============================================================

with tab_venta:
    html(
        """
        <div style="background:linear-gradient(135deg, #ffffff, #eff6ff); padding:20px; border-radius:20px; border:1px solid #bfdbfe; margin-bottom:15px;">
            <div style="font-size:26px; font-weight:900; color:#1e40af;">⚡ NUEVA VENTA</div>
            <div style="font-size:15px; color:#64748b;">Selecciona un producto o un Combo especial (Cama + Colchón)</div>
        </div>
        """
    )

    if df_inv.empty:
        st.info("📦 No hay productos registrados en el inventario.")
    else:
        st.markdown("### 📦 1. Galería de Productos")

        categorias = [nombre for nombre in df_inv["CATEGORIA"].tolist() if " - " not in str(nombre)]

        for principal in categorias:
            subproductos = obtener_subproductos(df_inv, principal)

            if not subproductos.empty:
                html(f"""
                <div class="product-card" style="background:#f8fafc; border-color:#cbd5e1;">
                    <div style="font-size:45px;">{obtener_icono(principal)}</div>
                    <div style="font-size:22px; font-weight:900; color:#0f172a;">{principal}</div>
                    <div style="font-size:14px; color:#64748b;">{len(subproductos)} variaciones disponibles</div>
                </div>
                """)

                columnas = st.columns(min(max(len(subproductos), 1), 4))
                for indice_sub, (_, sub) in enumerate(subproductos.iterrows()):
                    with columnas[indice_sub % len(columnas)]:
                        stock_sub = max(0, int(sub["STOCK"]))
                        precio_sub = float(sub["PRECIO"])
                        estado_sub, color_sub = estado_stock(stock_sub)
                        nombre_completo = str(sub["CATEGORIA"])
                        nombre_mostrar = nombre_completo.replace(principal + " - ", "", 1)

                        html(f"""
                        <div class="product-card">
                            <div style="font-size:35px;">{obtener_icono(nombre_completo)}</div>
                            <div style="font-size:16px; font-weight:900; color:#0f172a; min-height:40px;">{nombre_mostrar}</div>
                            <div style="font-size:22px; font-weight:900; color:#2563eb; margin-top:4px;">${precio_sub:,.2f}</div>
                            <div style="font-size:13px; color:#64748b;">Stock: {stock_sub}</div>
                            <div style="font-size:12px; font-weight:900; color:{color_sub}; margin-top:4px;">{estado_sub}</div>
                        </div>
                        """)
            else:
                fila_normal = df_inv[df_inv["CATEGORIA"] == principal]
                if not fila_normal.empty:
                    fila_normal = fila_normal.iloc[0]
                    stock = max(0, int(fila_normal["STOCK"]))
                    precio = float(fila_normal["PRECIO"])
                    estado, color = estado_stock(stock)

                    html(f"""
                    <div class="product-card" style="max-width:300px;">
                        <div style="font-size:45px;">{obtener_icono(principal)}</div>
                        <div style="font-size:18px; font-weight:900; color:#0f172a;">{principal}</div>
                        <div style="font-size:24px; font-weight:900; color:#2563eb; margin-top:4px;">${precio:,.2f}</div>
                        <div style="font-size:14px; color:#64748b;">Stock: {stock} unidades</div>
                        <div style="font-size:12px; font-weight:900; color:{color}; margin-top:4px;">{estado}</div>
                    </div>
                    """)

        st.markdown("---")

        lista_productos = obtener_productos_vendibles(df_inv)
        OPCION_COMBO = "🎁 Combo (Cama + Colchón)"
        opciones_venta = [OPCION_COMBO] + lista_productos

        producto_elegido = st.selectbox(
            "👉 Seleccione lo que desea vender:",
            opciones_venta,
            key="venta_producto_final",
        )

        es_combo = (producto_elegido == OPCION_COMBO)

        if es_combo:
            camas_disp = [p for p in df_inv["CATEGORIA"].tolist() if "cama" in p.lower() and producto_es_vendible(df_inv, p)]
            colchones_disp = [p for p in df_inv["CATEGORIA"].tolist() if ("colchon" in p.lower() or "colchón" in p.lower()) and producto_es_vendible(df_inv, p)]

            if not camas_disp or not colchones_disp:
                st.error("⚠️ Debe tener al menos una Cama y un Colchón en inventario para un Combo.")
                st.stop()

            col_cama, col_colchon = st.columns(2)
            with col_cama:
                cama_combo = st.selectbox("🛏️ Cama del combo", camas_disp, key="combo_cama_sel")
                fila_cama = df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]
                stock_cama = int(fila_cama["STOCK"])

            with col_colchon:
                colchon_combo = st.selectbox("💤 Colchón del combo", colchones_disp, key="combo_colchon_sel")
                fila_colchon = df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]
                stock_colchon = int(fila_colchon["STOCK"])

            sugerido = float(fila_cama["PRECIO"]) + float(fila_colchon["PRECIO"])
            precio_combo = st.number_input("🏷️ Precio especial del Combo ($)", min_value=0.0, value=sugerido, step=5.0)

            stock_disponible = min(stock_cama, stock_colchon)
            precio_producto = precio_combo
            nombre_producto_visible = f"Combo ({cama_combo} + {colchon_combo})"
        else:
            fila_producto = df_inv[df_inv["CATEGORIA"] == producto_elegido].iloc[0]
            stock_disponible = max(0, int(fila_producto["STOCK"]))
            precio_producto = float(fila_producto["PRECIO"])
            nombre_producto_visible = producto_elegido.split(" - ", 1)[1] if " - " in producto_elegido else producto_elegido

        if stock_disponible <= 0:
            st.error(f"🔴 **{nombre_producto_visible} no tiene suficiente stock.**")
        else:
            with st.form("form_venta_principal"):
                st.markdown("### 🧾 2. Formulario de Pago")

                a1, a2, a3 = st.columns(3)
                with a1:
                    cantidad = 1 if es_combo else st.number_input("🔢 Cantidad", min_value=1, max_value=stock_disponible, value=1, step=1)
                with a2:
                    metodo_pago = st.selectbox("💳 Forma de pago", ["Efectivo", "Transferencia", "Tarjeta"])
                with a3:
                    descuento = st.number_input("🏷️ Descuento ($)", min_value=0.0, value=0.0, step=1.0)

                st.markdown("### 👤 3. Datos del Cliente")
                nombre_cliente = st.text_input("👤 Nombre Completo", value="Cliente General")

                b1, b2 = st.columns(2)
                with b1:
                    cedula_cliente = st.text_input("🆔 Cédula / RUC", value="S/N")
                with b2:
                    telefono_cliente = st.text_input("📞 Teléfono", value="")

                correo_cliente = st.text_input("📧 Correo electrónico", value="")
                direccion_cliente = st.text_input("📍 Dirección de entrega", value="")
                foto_venta = st.file_uploader("📸 Foto comprobante / producto (opcional)", type=["jpg", "jpeg", "png"])

                subtotal = cantidad * precio_producto
                total = max(0.0, subtotal - descuento)

                html(f"""
                <div style="background: linear-gradient(135deg, #2563eb, #1d4ed8); color:white; padding:20px; border-radius:18px; text-align:center; margin:15px 0;">
                    <div style="font-size:14px; text-transform:uppercase; letter-spacing:1px;">TOTAL A COBRAR</div>
                    <div style="font-size:38px; font-weight:900;">${total:,.2f}</div>
                    <div style="font-size:13px; opacity:0.9;">{cantidad}x {nombre_producto_visible}</div>
                </div>
                """)

                confirmar_venta = st.form_submit_button("💰 REGISTRAR Y COBRAR VENTA", use_container_width=True)

                if confirmar_venta:
                    if not nombre_cliente.strip():
                        st.warning("⚠️ Ingrese el nombre del cliente.")
                    else:
                        ruta_foto = guardar_foto(foto_venta)

                        if es_combo:
                            idx_cama = df_inv[df_inv["CATEGORIA"] == cama_combo].index[0]
                            idx_colchon = df_inv[df_inv["CATEGORIA"] == colchon_combo].index[0]
                            df_inv.loc[idx_cama, "STOCK"] = max(0, int(df_inv.loc[idx_cama, "STOCK"]) - 1)
                            df_inv.loc[idx_colchon, "STOCK"] = max(0, int(df_inv.loc[idx_colchon, "STOCK"]) - 1)
                            guardar_csv(df_inv, FILE_INV)
                            cat_guardar = f"COMBO: {cama_combo} + {colchon_combo}"
                            msj_exito = f"🎉 Venta de Combo registrada a ${precio_producto:,.2f}."
                        else:
                            idx = df_inv[df_inv["CATEGORIA"] == producto_elegido].index[0]
                            nuevo_stock = max(0, int(df_inv.loc[idx, "STOCK"]) - cantidad)
                            df_inv.loc[idx, "STOCK"] = nuevo_stock
                            guardar_csv(df_inv, FILE_INV)
                            cat_guardar = producto_elegido
                            msj_exito = f"🎉 Venta guardada. Quedan {nuevo_stock} unidades."

                        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
                        nueva_venta = pd.DataFrame([{
                            "FECHA": fecha, "CATEGORIA": cat_guardar, "CANTIDAD": cantidad,
                            "PRECIO_UNITARIO": precio_producto, "TOTAL": total, "ABONADO": total,
                            "SALDO_PENDIENTE": 0.0, "METODO_PAGO": metodo_pago, "CLIENTE": nombre_cliente,
                            "CEDULA": cedula_cliente, "TELEFONO": telefono_cliente, "CORREO": correo_cliente,
                            "DIRECCION": direccion_cliente, "ESTADO": "Pagado y Entregado", "FOTO": ruta_foto
                        }])

                        df_ventas = pd.concat([df_ventas, nueva_venta], ignore_index=True)
                        guardar_csv(df_ventas, FILE_VENTAS)

                        st.session_state["ultima_operacion_whatsapp"] = {
                            "mensaje": f"🚨 *NUEVA VENTA* 🛏️\n👤 *Cliente:* {nombre_cliente}\n📦 *Producto:* {cantidad}x {cat_guardar}\n💰 *Total:* ${total:,.2f}\n💳 *Pago:* {metodo_pago}"
                        }
                        st.session_state["mensaje_exito"] = msj_exito
                        st.balloons()
                        st.rerun()


# ============================================================
#                 NOTIFICACIONES DE WHATSAPP / ÉXITO
# ============================================================

if "ultima_operacion_whatsapp" in st.session_state:
    mensaje_ws = st.session_state["ultima_operacion_whatsapp"]["mensaje"]
    enlace1 = generar_link_whatsapp(NUMERO_1, mensaje_ws)
    enlace2 = generar_link_whatsapp(NUMERO_2, mensaje_ws)

    html(f"""
    <div style="background:#ecfdf5; border:2px solid #10b981; padding:20px; border-radius:18px; text-align:center; margin-top:15px;">
        <div style="font-size:22px; font-weight:900; color:#047857;">📱 NOTIFICAR VENTA POR WHATSAPP</div>
        <div style="margin:10px 0;">
            <a href="{enlace1}" target="_blank" style="background:#25d366; color:white; padding:12px 20px; border-radius:12px; text-decoration:none; font-weight:900; display:inline-block; margin:4px;">💬 Enviar por WhatsApp 1</a>
            <a href="{enlace2}" target="_blank" style="background:#059669; color:white; padding:12px 20px; border-radius:12px; text-decoration:none; font-weight:900; display:inline-block; margin:4px;">💬 Enviar por WhatsApp 2</a>
        </div>
    </div>
    """)

    if st.button("✖️ CERRAR NOTIFICACIÓN", key="cerrar_ws"):
        del st.session_state["ultima_operacion_whatsapp"]
        st.rerun()

if "mensaje_exito" in st.session_state:
    st.success(st.session_state["mensaje_exito"])
    if st.button("✖️ Cerrar mensaje", key="cerrar_exito"):
        del st.session_state["mensaje_exito"]
        st.rerun()


# ============================================================
#                 TAB 2 - APARTADOS
# ============================================================

with tab_apartado:
    html(
        """
        <div style="background:linear-gradient(135deg, #ffffff, #f0fdf4); padding:20px; border-radius:20px; border:1px solid #bbf7d0; margin-bottom:15px;">
            <div style="font-size:26px; font-weight:900; color:#15803d;">📦 APARTADOS Y ABONOS</div>
            <div style="font-size:15px; color:#64748b;">Gestione las reservaciones y abonos de clientes</div>
        </div>
        """
    )

    with st.expander("➕ CREAR NUEVO APARTADO", expanded=True):
        productos_para_apartar = obtener_productos_vendibles(df_inv)

        if not productos_para_apartar:
            st.info("No hay productos disponibles.")
        else:
            producto_apartado = st.selectbox("📦 Producto a apartar", productos_para_apartar)
            fila_ap = df_inv[df_inv["CATEGORIA"] == producto_apartado].iloc[0]
            stock_ap = max(0, int(fila_ap["STOCK"]))
            precio_ap = float(fila_ap["PRECIO"])

            with st.form("form_nuevo_apartado"):
                cliente_ap = st.text_input("👤 Nombre del Cliente")
                c1, c2 = st.columns(2)
                with c1:
                    cedula_ap = st.text_input("🆔 Cédula")
                with c2:
                    telefono_ap = st.text_input("📞 Teléfono")

                a1, a2 = st.columns(2)
                with a1:
                    cantidad_ap = st.number_input("🔢 Cantidad", min_value=1, max_value=max(1, stock_ap), value=1)
                with a2:
                    abono_inicial = st.number_input("💵 Abono inicial ($)", min_value=0.0, value=10.0, step=5.0)

                total_ap = cantidad_ap * precio_ap
                saldo_ap = max(0.0, total_ap - abono_inicial)

                html(f"""
                <div style="background:#f8fafc; border:1px solid #cbd5e1; padding:15px; border-radius:14px; text-align:center; margin:10px 0;">
                    <div>Total: <b>${total_ap:,.2f}</b> | Abono: <b style="color:#10b981;">${abono_inicial:,.2f}</b></div>
                    <div style="font-size:20px; font-weight:900; color:#ef4444;">Saldo Pendiente: ${saldo_ap:,.2f}</div>
                </div>
                """)

                if st.form_submit_button("💾 GUARDAR APARTADO", use_container_width=True):
                    if not cliente_ap.strip():
                        st.warning("⚠️ Ingrese el nombre del cliente.")
                    else:
                        estado_ap = "Pagado y Entregado" if saldo_ap <= 0 else "Apartado (Pendiente)"
                        fecha_ap = datetime.now().strftime("%Y-%m-%d %H:%M")

                        nuevo_ap = pd.DataFrame([{
                            "FECHA": fecha_ap, "CATEGORIA": producto_apartado, "CANTIDAD": cantidad_ap,
                            "PRECIO_UNITARIO": precio_ap, "TOTAL": total_ap, "ABONADO": abono_inicial,
                            "SALDO_PENDIENTE": saldo_ap, "METODO_PAGO": "Efectivo", "CLIENTE": cliente_ap,
                            "CEDULA": cedula_ap, "TELEFONO": telefono_ap, "CORREO": "", "DIRECCION": "",
                            "ESTADO": estado_ap, "FOTO": "Sin foto"
                        }])

                        df_ventas = pd.concat([df_ventas, nuevo_ap], ignore_index=True)
                        guardar_csv(df_ventas, FILE_VENTAS)

                        st.session_state["mensaje_exito"] = "✅ Apartado guardado con éxito."
                        st.rerun()


# ============================================================
#                 TAB 3 - INVENTARIO
# ============================================================

with tab_inventario:
    html(
        """
        <div style="background:linear-gradient(135deg, #ffffff, #fff7ed); padding:20px; border-radius:20px; border:1px solid #fed7aa; margin-bottom:15px;">
            <div style="font-size:26px; font-weight:900; color:#c2410c;">🛠️ CONTROL DE INVENTARIO</div>
            <div style="font-size:15px; color:#64748b;">Administración de existencias y precios</div>
        </div>
        """
    )

    clave_admin = st.text_input("🔐 Clave Admin", type="password", key="clave_inv")

    if clave_admin == CLAVE_ADMIN:
        st.success("✅ Modo Administrador Activo")

        st.markdown("### ✏️ Modificar Stock / Precio")
        if not df_inv.empty:
            prod_mod = st.selectbox("📦 Producto a editar", df_inv["CATEGORIA"].tolist())
            fila_m = df_inv[df_inv["CATEGORIA"] == prod_mod].iloc[0]

            col1, col2 = st.columns(2)
            with col1:
                cambio_stock = st.number_input("Añadir / Restar Stock", value=0, step=1)
            with col2:
                precio_nuevo = st.number_input("Nuevo Precio ($)", min_value=0.0, value=float(fila_m["PRECIO"]), step=5.0)

            if st.button("💾 ACTUALIZAR PRODUCTO", use_container_width=True):
                idx = df_inv[df_inv["CATEGORIA"] == prod_mod].index[0]
                df_inv.loc[idx, "STOCK"] = max(0, int(df_inv.loc[idx, "STOCK"]) + cambio_stock)
                df_inv.loc[idx, "PRECIO"] = precio_nuevo
                guardar_csv(df_inv, FILE_INV)
                st.success("✅ Guardado correctamente")
                st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Listado Completo")
        st.dataframe(df_inv, use_container_width=True)


# ============================================================
#                 TAB 4 - HISTORIAL DE CAJA
# ============================================================

with tab_historial:
    html(
        """
        <div style="background:linear-gradient(135deg, #ffffff, #f8fafc); padding:20px; border-radius:20px; border:1px solid #e2e8f0; margin-bottom:15px;">
            <div style="font-size:26px; font-weight:900; color:#334155;">📜 HISTORIAL Y REPORTE DE CAJA</div>
        </div>
        """
    )

    if df_ventas.empty:
        st.info("📭 Aún no se han realizado ventas.")
    else:
        st.dataframe(df_ventas, use_container_width=True)

        st.download_button(
            "📥 DESCARGAR REPORTE EXCEL / CSV",
            df_ventas.to_csv(index=False).encode("utf-8-sig"),
            "reporte_ventas.csv",
            "text/csv",
            use_container_width=True,
        )
