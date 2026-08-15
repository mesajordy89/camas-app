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
#            FUNCIÓN PARA HTML
# ============================================================

def html(contenido):
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
    df.to_csv(
        ruta,
        index=False,
        encoding="utf-utf-8-sig" if "utf-utf" in "" else "utf-8-sig",
    )


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
        df = pd.DataFrame([
            {"CATEGORIA": "Camas", "STOCK": 0, "PRECIO": 0.0},
            {"CATEGORIA": "Colchones", "STOCK": 0, "PRECIO": 0.0},
            {"CATEGORIA": "Armarios Grandes", "STOCK": 0, "PRECIO": 0.0},
            {"CATEGORIA": "Armarios Pequeños", "STOCK": 0, "PRECIO": 0.0},
            {"CATEGORIA": "Pajaritas", "STOCK": 0, "PRECIO": 0.0},
        ])

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
#                 FOTOS Y COMUNICACIONES
# ============================================================

def guardar_foto(archivo, prefijo=""):
    if archivo is None:
        return "Sin foto"
    nombre = f"{prefijo}{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{os.path.basename(archivo.name)}"
    ruta = os.path.join(CARPETA_FOTOS, nombre)
    try:
        with open(ruta, "wb") as f:
            f.write(archivo.getbuffer())
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
        return ("🔴 AGOTADO", "#dc2626")
    if stock <= 2:
        return ("🟠 POCO STOCK", "#ea580c")
    return ("🟢 DISPONIBLE", "#16a34a")


def contar_apartados(df):
    if df.empty or "ESTADO" not in df.columns:
        return 0
    return int(df["ESTADO"].astype(str).str.contains("Apartado", case=False, na=False).sum())


# ============================================================
#                 PRODUCTOS / SUBPRODUCTOS LÓGICA
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
        .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%); }
        .login-box { max-width:520px; margin:80px auto 25px auto; padding:45px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); border-radius:30px; text-align:center; box-shadow:0 25px 60px rgba(0,0,0,0.45); backdrop-filter:blur(15px); }
        .login-title { font-size:42px; color:white; font-weight:900; }
        .login-subtitle { font-size:18px; color:#cbd5e1; margin-top:8px; }
        </style>
        <div class="login-box">
            <div style="font-size:72px;">🛏️</div>
            <div class="login-title">LOCAL MESITAS</div>
            <div class="login-subtitle">Sistema de ventas y administración</div>
            <div style="font-size:48px; margin-top:25px;">🔐</div>
            <div style="color:#94a3b8; font-size:16px;">Escriba su contraseña y presione INGRESAR</div>
        </div>
        """
    )
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        clave = st.text_input("🔑 Contraseña", type="password", key="clave_login")
        if st.button("🚀 INGRESAR", use_container_width=True):
            if clave == CLAVE_ACCESO:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ La contraseña es incorrecta.")
    st.stop()


# ============================================================
#                 CARGAR INFORMACIÓN Y ESTILOS
# ============================================================

df_inv = cargar_inventario()
df_ventas = cargar_ventas()

html(
    """
    <style>
    .stApp { background:#f1f5f9; font-family: 'Segoe UI', 'Arial', sans-serif; }
    .header-box { background: linear-gradient(135deg, #0f172a, #1e3a8a); padding:30px; border-radius:25px; color:white; text-align:center; margin-bottom:20px; box-shadow:0 12px 30px rgba(15,23,42,0.18); }
    .info-card { background:white; padding:20px; border-radius:20px; text-align:center; border:1px solid #e2e8f0; box-shadow:0 6px 18px rgba(15,23,42,0.07); }
    .product-card { background:white; border:1px solid #e2e8f0; border-radius:22px; padding:20px 12px; text-align:center; min-height:220px; box-shadow:0 8px 25px rgba(15,23,42,0.08); margin-bottom:15px; }
    .total-card { background: linear-gradient(135deg, #eff6ff, #dbeafe); border:2px solid #3b82f6; border-radius:22px; padding:24px; text-align:center; }
    .receipt-card { background:white; padding:26px; border-radius:22px; border-left:7px solid #2563eb; box-shadow:0 8px 25px rgba(15,23,42,0.08); }
    .stButton > button { border-radius:14px; min-height:54px; font-weight:800; font-size:17px !important; }
    input, textarea, select { border-radius:12px !important; }
    </style>
    """
)

# ============================================================
#                 ENCABEZADO Y RESUMEN
# ============================================================

col_titulo, col_salir = st.columns([6, 1])
with col_salir:
    if st.button("🔒 SALIR", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

html(
    """
    <div class="header-box">
        <div style="font-size:44px; font-weight:900;">🛏️ LOCAL MESITAS</div>
        <div style="font-size:19px; color:#cbd5e1; margin-top:7px;">Sistema de Ventas • Apartados • Inventario • Caja</div>
    </div>
    """
)

dinero_recibido = float(df_ventas["ABONADO"].sum()) if not df_ventas.empty else 0.0
total_operaciones = len(df_ventas)
total_apartados = contar_apartados(df_ventas)
total_stock = int(df_inv["STOCK"].sum()) if not df_inv.empty else 0

r1, r2, r3, r4 = st.columns(4)
with r1:
    html(f'<div class="info-card"><div style="font-size:15px; color:#64748b; font-weight:800;">💰 DINERO RECIBIDO</div><div style="font-size:29px; font-weight:900; color:#0f172a;">${dinero_recibido:,.2f}</div></div>')
with r2:
    html(f'<div class="info-card"><div style="font-size:15px; color:#64748b; font-weight:800;">📦 PRODUCTOS EN STOCK</div><div style="font-size:29px; font-weight:900; color:#0f172a;">{total_stock}</div></div>')
with r3:
    html(f'<div class="info-card"><div style="font-size:15px; color:#64748b; font-weight:800;">🧾 OPERACIONES</div><div style="font-size:29px; font-weight:900; color:#0f172a;">{total_operaciones}</div></div>')
with r4:
    html(f'<div class="info-card"><div style="font-size:15px; color:#64748b; font-weight:800;">📦 APARTADOS ACTIVOS</div><div style="font-size:29px; font-weight:900; color:#0f172a;">{total_apartados}</div></div>')

st.write("")

# ============================================================
#                 MENÚ PRINCIPAL
# ============================================================

tab_venta, tab_apartado, tab_inventario, tab_historial = st.tabs([
    "⚡ VENDER",
    "📦 APARTADOS",
    "🛠️ INVENTARIO",
    "📜 HISTORIAL",
])

# ============================================================
#                 TAB 1 - VENDER
# ============================================================

with tab_venta:
    if df_inv.empty:
        st.info("📦 No hay productos registrados.")
    else:
        st.markdown("### 📦 1. Productos disponibles")
        categorias = [nombre for nombre in df_inv["CATEGORIA"].tolist() if " - " not in str(nombre)]

        for principal in categorias:
            subproductos = obtener_subproductos(df_inv, principal)

            if not subproductos.empty:
                html(f"""
                <div class="product-card" style="min-height:140px; background:#f8fafc;">
                    <div style="font-size:45px;">{obtener_icono(principal)}</div>
                    <div style="font-size:24px; font-weight:900; color:#0f172a;">{principal} (Repositorio)</div>
                    <div style="font-size:14px; color:#2563eb; font-weight:800;">👇 Seleccione un subproducto específico a continuación</div>
                </div>
                """)

                columnas = st.columns(min(max(len(subproductos), 1), 4))
                for idx_sub, (_, sub) in enumerate(subproductos.iterrows()):
                    with columnas[idx_sub % len(columnas)]:
                        stock_sub = max(0, int(sub["STOCK"]))
                        precio_sub = float(sub["PRECIO"])
                        estado_sub, color_sub = estado_stock(stock_sub)
                        nombre_completo = str(sub["CATEGORIA"])
                        nombre_mostrar = nombre_completo.replace(principal + " - ", "", 1)

                        html(f"""
                        <div class="product-card">
                            <div style="font-size:40px;">{obtener_icono(nombre_completo)}</div>
                            <div style="font-size:17px; font-weight:900; color:#0f172a;">{nombre_mostrar}</div>
                            <div style="font-size:26px; font-weight:900; color:#1e3a8a; margin-top:6px;">${precio_sub:,.2f}</div>
                            <div style="font-size:14px; color:#64748b;">📦 {stock_sub} unidades</div>
                            <div style="font-size:13px; font-weight:900; color:{color_sub}; margin-top:6px;">{estado_sub}</div>
                        </div>
                        """)
            else:
                fila_normal = df_inv[df_inv["CATEGORIA"] == principal]
                if not fila_normal.empty:
                    sub = fila_normal.iloc[0]
                    stock = max(0, int(sub["STOCK"]))
                    precio = float(sub["PRECIO"])
                    estado, color = estado_stock(stock)
                    html(f"""
                    <div class="product-card" style="max-width:300px;">
                        <div style="font-size:45px;">{obtener_icono(principal)}</div>
                        <div style="font-size:19px; font-weight:900; color:#0f172a;">{principal}</div>
                        <div style="font-size:26px; font-weight:900; color:#1e3a8a;">${precio:,.2f}</div>
                        <div style="font-size:15px; color:#64748b;">📦 {stock} unidades</div>
                        <div style="font-size:13px; font-weight:900; color:{color};">{estado}</div>
                    </div>
                    """)

        st.markdown("---")
        lista_productos = obtener_productos_vendibles(df_inv)
        OPCION_COMBO = "🎁 Combo (Cama + Colchón)"
        opciones_venta = [OPCION_COMBO] + lista_productos

        producto_elegido = st.selectbox("👉 Seleccione lo que desea vender", opciones_venta, key="venta_producto_final")
        es_combo = (producto_elegido == OPCION_COMBO)

        if es_combo:
            camas_disp = [p for p in df_inv["CATEGORIA"].tolist() if "cama" in p.lower() and producto_es_vendible(df_inv, p)]
            colchones_disp = [p for p in df_inv["CATEGORIA"].tolist() if ("colchon" in p.lower() or "colchón" in p.lower()) and producto_es_vendible(df_inv, p)]

            if not camas_disp or not colchones_disp:
                st.error("⚠️ Debe tener al menos una Cama y un Colchón registrados como subproductos para armar un combo.")
                st.stop()

            col_cama, col_colchon = st.columns(2)
            with col_cama:
                cama_combo = st.selectbox("🛏️ Seleccionar Cama del combo", camas_disp, key="combo_cama_sel")
                stock_cama = int(df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]["STOCK"])
            with col_colchon:
                colchon_combo = st.selectbox("💤 Seleccionar Colchón del combo", colchones_disp, key="combo_colchon_sel")
                stock_colchon = int(df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]["STOCK"])

            sugerido = float(df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]["PRECIO"]) + float(df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]["PRECIO"])
            precio_combo = st.number_input("🏷️ Precio del Combo ($)", min_value=0.0, value=sugerido, step=5.0)

            stock_disponible = min(stock_cama, stock_colchon)
            precio_producto = precio_combo
            nombre_producto_visible = f"Combo ({cama_combo} + {colchon_combo})"
        else:
            fila_p = df_inv[df_inv["CATEGORIA"] == producto_elegido].iloc[0]
            stock_disponible = max(0, int(fila_p["STOCK"]))
            precio_producto = float(fila_p["PRECIO"])
            nombre_producto_visible = producto_elegido

        if stock_disponible <= 0:
            st.error(f"🔴 **{nombre_producto_visible}** no tiene stock. Ingrese a INVENTARIO para actualizar las unidades.")
        else:
            with st.form("form_venta_principal"):
                st.markdown("### 🧾 Datos del Cobro")
                a1, a2, a3 = st.columns(3)
                with a1:
                    cantidad = 1 if es_combo else st.number_input("🔢 Cantidad", min_value=1, max_value=stock_disponible, value=1)
                with a2:
                    metodo_pago = st.selectbox("💳 Forma de pago", ["Efectivo", "Transferencia", "Tarjeta"])
                with a3:
                    descuento = st.number_input("🏷️ Descuento ($)", min_value=0.0, value=0.0)

                nombre_cliente = st.text_input("👤 Nombre Cliente", value="Cliente General")
                cedula_cliente = st.text_input("🆔 Cédula / RUC", value="S/N")
                telefono_cliente = st.text_input("📞 Teléfono", value="")
                correo_cliente = st.text_input("📧 Correo", value="")
                direccion_cliente = st.text_input("📍 Dirección", value="")
                foto_venta = st.file_uploader("📸 Foto comprobante / producto", type=["jpg", "jpeg", "png"])

                subtotal = cantidad * precio_producto
                total = max(0.0, subtotal - descuento)

                html(f'<div class="total-card"><div style="font-size:36px; font-weight:900; color:#1d4ed8;">Total: ${total:,.2f}</div></div>')

                if st.form_submit_button("💰 REGISTRAR VENTA", use_container_width=True):
                    ruta_foto = guardar_foto(foto_venta)

                    if es_combo:
                        idx_c = df_inv[df_inv["CATEGORIA"] == cama_combo].index[0]
                        idx_k = df_inv[df_inv["CATEGORIA"] == colchon_combo].index[0]
                        df_inv.loc[idx_c, "STOCK"] = max(0, int(df_inv.loc[idx_c, "STOCK"]) - 1)
                        df_inv.loc[idx_k, "STOCK"] = max(0, int(df_inv.loc[idx_k, "STOCK"]) - 1)
                        cat_guardar = f"COMBO: {cama_combo} + {colchon_combo}"
                    else:
                        idx_p = df_inv[df_inv["CATEGORIA"] == producto_elegido].index[0]
                        df_inv.loc[idx_p, "STOCK"] = max(0, int(df_inv.loc[idx_p, "STOCK"]) - cantidad)
                        cat_guardar = producto_elegido

                    guardar_csv(df_inv, FILE_INV)

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

                    st.success("🎉 Venta registrada con éxito.")
                    st.balloons()
                    st.rerun()

# ============================================================
#                 TAB 2 - APARTADOS
# ============================================================

with tab_apartado:
    st.markdown("### 📦 Registro de Apartados")
    productos_para_apartar = obtener_productos_vendibles(df_inv)

    if not productos_para_apartar:
        st.info("No hay subproductos vendibles disponibles para apartar.")
    else:
        producto_apartado = st.selectbox("📦 Producto a apartar", productos_para_apartar)
        fila_ap = df_inv[df_inv["CATEGORIA"] == producto_apartado].iloc[0]
        stock_ap = max(0, int(fila_ap["STOCK"]))
        precio_ap = float(fila_ap["PRECIO"])

        with st.form("form_nuevo_apartado"):
            cliente_ap = st.text_input("👤 Cliente")
            cedula_ap = st.text_input("🆔 Cédula")
            telefono_ap = st.text_input("📞 Teléfono")
            cant_ap = st.number_input("🔢 Cantidad", min_value=1, max_value=max(1, stock_ap), value=1)
            abono_ap = st.number_input("💵 Abono ($)", min_value=0.0, value=10.0)

            total_ap = cant_ap * precio_ap
            saldo_ap = max(0.0, total_ap - abono_ap)

            html(f'<div class="total-card"><div>Total: ${total_ap:,.2f}</div><div>Abono: ${abono_ap:,.2f}</div><div style="color:#dc2626; font-size:24px; font-weight:900;">Saldo Pendiente: ${saldo_ap:,.2f}</div></div>')

            if st.form_submit_button("💾 GUARDAR APARTADO", use_container_width=True):
                if not cliente_ap.strip():
                    st.warning("⚠️ Escriba el nombre del cliente.")
                elif abono_ap > total_ap:
                    st.error("❌ El abono no puede superar el total.")
                else:
                    estado_ap = "Pagado y Entregado" if saldo_ap <= 0 else "Apartado (Pendiente)"
                    fecha_ap = datetime.now().strftime("%Y-%m-%d %H:%M")

                    nuevo_ap = pd.DataFrame([{
                        "FECHA": fecha_ap, "CATEGORIA": producto_apartado, "CANTIDAD": cant_ap,
                        "PRECIO_UNITARIO": precio_ap, "TOTAL": total_ap, "ABONADO": abono_ap,
                        "SALDO_PENDIENTE": saldo_ap, "METODO_PAGO": "Efectivo", "CLIENTE": cliente_ap,
                        "CEDULA": cedula_ap, "TELEFONO": telefono_ap, "CORREO": "", "DIRECCION": "",
                        "ESTADO": estado_ap, "FOTO": "Sin foto"
                    }])

                    if saldo_ap <= 0:
                        idx_ap = df_inv[df_inv["CATEGORIA"] == producto_apartado].index[0]
                        df_inv.loc[idx_ap, "STOCK"] = max(0, int(df_inv.loc[idx_ap, "STOCK"]) - cant_ap)
                        guardar_csv(df_inv, FILE_INV)

                    df_ventas = pd.concat([df_ventas, nuevo_ap], ignore_index=True)
                    guardar_csv(df_ventas, FILE_VENTAS)
                    st.success("✅ Apartado registrado correctamente.")
                    st.rerun()

# ============================================================
#                 TAB 3 - INVENTARIO
# ============================================================

with tab_inventario:
    st.markdown("### 🛠️ Administración de Inventario")
    clave_admin = st.text_input("🔐 Clave Admin", type="password", key="clave_inv")

    if clave_admin == CLAVE_ADMIN:
        st.markdown("#### ➕ Crear Repositorio, Producto o Subproducto")

        principales = [n for n in df_inv["CATEGORIA"].tolist() if " - " not in str(n)]

        opciones_creacion = [
            "✨ CREAR NUEVO REPOSITORIO / CATEGORÍA (Sin precio)",
            "📦 CREAR PRODUCTO SIMPLE (Con precio y stock)",
        ] + principales

        opcion_padre = st.selectbox("📂 Seleccione Acción o Categoría Padre", opciones_creacion)

        # OPCIÓN 1: Crear Categoría Principal / Repositorio
        if opcion_padre == "✨ CREAR NUEVO REPOSITORIO / CATEGORÍA (Sin precio)":
            nuevo_nombre_cat = st.text_input("📦 Nombre de la nueva Categoría Principal (Ej. Camas)")
            if st.button("➕ CREAR REPOSITORIO PRINCIPAL", use_container_width=True):
                nombre_limpio = nuevo_nombre_cat.strip()
                if not nombre_limpio:
                    st.warning("⚠️ Escriba el nombre de la categoría.")
                elif existe_producto(df_inv, nombre_limpio):
                    st.error("❌ La categoría ya existe.")
                else:
                    nuevo_reg = pd.DataFrame([{"CATEGORIA": nombre_limpio, "STOCK": 0, "PRECIO": 0.0}])
                    df_inv = pd.concat([df_inv, nuevo_reg], ignore_index=True)
                    guardar_csv(df_inv, FILE_INV)
                    st.success(f"📂 Repositorio '{nombre_limpio}' creado con éxito.")
                    st.rerun()

        # OPCIÓN 2: Crear Producto Simple (Sin subproductos)
        elif opcion_padre == "📦 CREAR PRODUCTO SIMPLE (Con precio y stock)":
            nom_simple = st.text_input("📦 Nombre del Producto (Ej. Velador)")
            st_simple = st.number_input("📦 Stock Inicial", min_value=0, value=1, key="st_sim")
            pr_simple = st.number_input("💰 Precio ($)", min_value=0.0, value=25.0, step=5.0, key="pr_sim")

            if st.button("➕ CREAR PRODUCTO SIMPLE", use_container_width=True):
                nombre_limpio = nom_simple.strip()
                if not nombre_limpio:
                    st.warning("⚠️ Escriba el nombre del producto.")
                elif pr_simple <= 0:
                    st.warning("⚠️ Ingrese un precio válido mayor a $0.")
                elif existe_producto(df_inv, nombre_limpio):
                    st.error("❌ El producto ya existe.")
                else:
                    nuevo_reg = pd.DataFrame([{"CATEGORIA": nombre_limpio, "STOCK": st_simple, "PRECIO": pr_simple}])
                    df_inv = pd.concat([df_inv, nuevo_reg], ignore_index=True)
                    guardar_csv(df_inv, FILE_INV)
                    st.success(f"🎉 Producto '{nombre_limpio}' creado con éxito.")
                    st.rerun()

        # OPCIÓN 3: Crear Subproducto dentro de un Repositorio Existente
        else:
            sub_nombre = st.text_input(f"🛏️ Subproducto para '{opcion_padre}' (Ej. Cama 3 Plazas)")
            st_sub = st.number_input("📦 Stock Inicial", min_value=0, value=1, key="st_sub")
            pr_sub = st.number_input("💰 Precio ($)", min_value=0.0, value=50.0, step=5.0, key="pr_sub")

            if st.button("➕ CREAR SUBPRODUCTO", use_container_width=True):
                nombre_limpio = sub_nombre.strip()
                nombre_final = f"{opcion_padre} - {nombre_limpio}"

                if not nombre_limpio:
                    st.warning("⚠️ Escriba el nombre del subproducto.")
                elif pr_sub <= 0:
                    st.warning("⚠️ Los subproductos deben tener un precio mayor a $0.")
                elif existe_producto(df_inv, nombre_final):
                    st.error("❌ El subproducto ya existe.")
                else:
                    nuevo_reg = pd.DataFrame([{"CATEGORIA": nombre_final, "STOCK": st_sub, "PRECIO": pr_sub}])
                    df_inv = pd.concat([df_inv, nuevo_reg], ignore_index=True)
                    guardar_csv(df_inv, FILE_INV)
                    st.success(f"🎉 Subproducto '{nombre_final}' guardado exitosamente.")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### 📊 Listado de Inventario")
        if df_inv.empty:
            st.info("No hay productos en el inventario.")
        else:
            for _, fila in df_inv.iterrows():
                nom = str(fila["CATEGORIA"])
                stk = max(0, int(fila["STOCK"]))
                prc = float(fila["PRECIO"])
                es_p = es_categoria_principal(df_inv, nom)

                c1, c2, c3 = st.columns([3, 1.5, 1.5])
                with c1:
                    st.write(f"**{nom}** {'📂 *(Repositorio)*' if es_p else ''}")
                with c2:
                    st.write(f"Stock: {stk} ud.")
                with c3:
                    st.write("—" if es_p else f"${prc:,.2f}")

# ============================================================
#                 TAB 4 - HISTORIAL
# ============================================================

with tab_historial:
    st.markdown("### 📜 Historial de Ventas")
    if not df_ventas.empty:
        st.dataframe(df_ventas, use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros disponibles.")
