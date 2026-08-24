from datetime import datetime
import io
import os
import textwrap
import urllib.parse
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Cargar reportlab para comprobantes PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ============================================================
#                 CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Local Mesitas - Sistema POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1234"

CARPETA_FOTOS = "fotos_ventas"

NUMEROS_WHATSAPP = {
    "Vendedor 1 (0990847819)": "593990847819",
    "Vendedor 2 (0983576800)": "593983576800",
}

os.makedirs(CARPETA_FOTOS, exist_ok=True)

COLUMNAS_VENTAS = [
    "FECHA", "CATEGORIA", "CANTIDAD", "PRECIO_UNITARIO", "TOTAL",
    "ABONADO", "SALDO_PENDIENTE", "METODO_PAGO", "CLIENTE", "CEDULA",
    "TELEFONO", "CORREO", "DIRECCION", "ESTADO", "FOTO"
]

# ============================================================
#       CONEXIÓN PERMANENTE CON GOOGLE SHEETS (CORRECCIÓN)
# ============================================================

conn = st.connection("gsheets", type=GSheetsConnection)

def html(contenido):
    texto_limpio = textwrap.dedent(contenido).strip()
    texto_limpio = " ".join(line.strip() for line in texto_limpio.splitlines())
    return st.markdown(texto_limpio, unsafe_allow_html=True)

def normalizar_inventario(df_input):
    if df_input is None or df_input.empty:
        return pd.DataFrame(columns=["CATEGORIA", "STOCK", "PRECIO", "STOCK_MINIMO"])
    
    df = df_input.copy()
    if "CATEGORIA" not in df.columns: df["CATEGORIA"] = ""
    if "STOCK" not in df.columns: df["STOCK"] = 0
    if "PRECIO" not in df.columns: df["PRECIO"] = 0.0
    if "STOCK_MINIMO" not in df.columns: df["STOCK_MINIMO"] = 1

    df["CATEGORIA"] = df["CATEGORIA"].fillna("").astype(str).str.strip()
    df["STOCK"] = pd.to_numeric(df["STOCK"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    df["STOCK_MINIMO"] = pd.to_numeric(df["STOCK_MINIMO"], errors="coerce").fillna(1).astype(int).clip(lower=0)
    df["PRECIO"] = pd.to_numeric(df["PRECIO"], errors="coerce").fillna(0.0).clip(lower=0)
    
    return df[df["CATEGORIA"] != ""].reset_index(drop=True)[["CATEGORIA", "STOCK", "PRECIO", "STOCK_MINIMO"]]

def normalizar_ventas(df_input):
    if df_input is None or df_input.empty:
        return pd.DataFrame(columns=COLUMNAS_VENTAS)
    
    df = df_input.copy()
    for columna in COLUMNAS_VENTAS:
        if columna not in df.columns:
            if columna == "ABONADO": df[columna] = pd.to_numeric(df.get("TOTAL", 0), errors="coerce").fillna(0.0)
            elif columna == "SALDO_PENDIENTE": df[columna] = 0.0
            elif columna == "ESTADO": df[columna] = "Pagado y Entregado"
            elif columna == "DIRECCION": df[columna] = "S/N"
            elif columna == "FOTO": df[columna] = "Sin foto"
            else: df[columna] = ""

    for col in ["CANTIDAD", "PRECIO_UNITARIO", "TOTAL", "ABONADO", "SALDO_PENDIENTE"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["CANTIDAD"] = df["CANTIDAD"].astype(int).clip(lower=0)
    for col in ["PRECIO_UNITARIO", "TOTAL", "ABONADO", "SALDO_PENDIENTE"]:
        df[col] = df[col].clip(lower=0)

    for col in ["FECHA", "CATEGORIA", "METODO_PAGO", "CLIENTE", "CEDULA", "TELEFONO", "CORREO", "DIRECCION", "ESTADO", "FOTO"]:
        df[col] = df[col].fillna("").astype(str)

    return df[COLUMNAS_VENTAS]

def cargar_inventario():
    try:
        df = conn.read(worksheet="Inventario", ttl=0)
    except Exception:
        df = pd.DataFrame([
            {"CATEGORIA": "CAMAS - CAMA TAPIZADA DE LUCES 2PLZ", "STOCK": 5, "PRECIO": 150.0, "STOCK_MINIMO": 2},
            {"CATEGORIA": "COLCHONES - COLCHON SUEÑO TOTAL 2PLZS", "STOCK": 5, "PRECIO": 100.0, "STOCK_MINIMO": 2},
        ])
    df = normalizar_inventario(df)
    return df

def guardar_inventario(df):
    df_norm = normalizar_inventario(df)
    conn.update(worksheet="Inventario", data=df_norm)

def cargar_ventas():
    try:
        df = conn.read(worksheet="Ventas", ttl=0)
    except Exception:
        df = pd.DataFrame()
    df = normalizar_ventas(df)
    return df

def guardar_ventas(df):
    df_norm = normalizar_ventas(df)
    conn.update(worksheet="Ventas", data=df_norm)

def generar_pdf_recibo(venta_dict):
    if not HAS_REPORTLAB: return None
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "LOCAL MESITAS - COMPROBANTE DE VENTA")
    p.setFont("Helvetica", 10)
    p.drawString(100, 735, f"Fecha: {venta_dict.get('FECHA', '')}")
    p.line(100, 725, 500, 725)
    
    y = 700
    p.drawString(100, y, f"Cliente: {venta_dict.get('CLIENTE', 'N/A')}")
    p.drawString(300, y, f"Cédula/RUC: {venta_dict.get('CEDULA', 'N/A')}")
    y -= 20
    p.drawString(100, y, f"Teléfono: {venta_dict.get('TELEFONO', 'N/A')}")
    p.drawString(300, y, f"Estado: {venta_dict.get('ESTADO', 'N/A')}")
    y -= 30
    
    p.setFont("Helvetica-Bold", 11)
    p.drawString(100, y, "Producto / Detalle")
    p.drawString(300, y, "Cant.")
    p.drawString(380, y, "Total")
    y -= 15
    p.setFont("Helvetica", 10)
    p.drawString(100, y, str(venta_dict.get('CATEGORIA', '')))
    p.drawString(300, y, str(venta_dict.get('CANTIDAD', '1')))
    p.drawString(380, y, f"${float(venta_dict.get('TOTAL', 0)):,.2f}")
    
    y -= 40
    p.line(100, y, 500, y)
    y -= 20
    p.drawString(300, y, f"Abonado: ${float(venta_dict.get('ABONADO', 0)):,.2f}")
    y -= 15
    p.drawString(300, y, f"Saldo Pendiente: ${float(venta_dict.get('SALDO_PENDIENTE', 0)):,.2f}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def generar_link_whatsapp(numero, venta_dict):
    mensaje = f"""🛏️ *LOCAL MESITAS - RECIBO DE VENTA*
📅 *Fecha:* {venta_dict.get('FECHA')}
👤 *Cliente:* {venta_dict.get('CLIENTE')}
🆔 *Cédula:* {venta_dict.get('CEDULA')}
📦 *Detalle:* {venta_dict.get('CATEGORIA')}
💰 *Total:* ${float(venta_dict.get('TOTAL', 0)):,.2f}
💳 *Pago:* {venta_dict.get('METODO_PAGO')}
📌 *Estado:* {venta_dict.get('ESTADO')}

¡Gracias por su compra!"""
    mensaje_enc = urllib.parse.quote(mensaje)
    return f"https://wa.me/{numero}?text={mensaje_enc}"

def es_subproducto(nombre): return " - " in str(nombre)

def obtener_subproductos(df, principal):
    prefijo = str(principal).strip() + " - "
    return df[df["CATEGORIA"].astype(str).str.startswith(prefijo, na=False)].copy()

def es_categoria_principal(df, nombre):
    return not obtener_subproductos(df, str(nombre).strip()).empty

def producto_es_vendible(df, nombre):
    nombre = str(nombre).strip()
    if es_subproducto(nombre): return True
    return not es_categoria_principal(df, nombre)

def obtener_productos_vendibles(df):
    if df.empty or "CATEGORIA" not in df.columns: return []
    return [nombre for nombre in df["CATEGORIA"].tolist() if producto_es_vendible(df, nombre)]

def existe_producto(df, nombre):
    if df.empty or "CATEGORIA" not in df.columns: return False
    return nombre.strip().lower() in df["CATEGORIA"].astype(str).str.strip().str.lower().values

def agregar_combo_al_carrito(cama_nombre, colchon_nombre, precio_combo):
    df_inv_local = st.session_state["df_inv"]
    stk_cama = int(df_inv_local[df_inv_local["CATEGORIA"] == cama_nombre]["STOCK"].values[0]) if cama_nombre in df_inv_local["CATEGORIA"].values else 0
    stk_colchon = int(df_inv_local[df_inv_local["CATEGORIA"] == colchon_nombre]["STOCK"].values[0]) if colchon_nombre in df_inv_local["CATEGORIA"].values else 0

    if stk_cama < 1 or stk_colchon < 1:
        st.error("❌ No hay suficiente stock disponible de uno de los productos para armar el combo.")
        return False

    st.session_state["carrito"].append({
        "producto": cama_nombre,
        "cantidad": 1,
        "precio": float(precio_combo / 2)
    })
    st.session_state["carrito"].append({
        "producto": colchon_nombre,
        "cantidad": 1,
        "precio": float(precio_combo / 2)
    })
    return True

# ============================================================
#                 INICIALIZACIÓN DE SESIÓN
# ============================================================

if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "ultima_venta" not in st.session_state: st.session_state["ultima_venta"] = None
if "carrito" not in st.session_state: st.session_state["carrito"] = []
if "redirect_url" not in st.session_state: st.session_state["redirect_url"] = None

if "df_inv" not in st.session_state: st.session_state["df_inv"] = cargar_inventario()
if "df_ventas" not in st.session_state: st.session_state["df_ventas"] = cargar_ventas()

# ============================================================
#                 LOGIN DE ACCESO
# ============================================================

if not st.session_state["autenticado"]:
    html("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%); }
    .login-box { max-width:520px; margin:80px auto 25px auto; padding:45px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); border-radius:30px; text-align:center; box-shadow:0 25px 60px rgba(0,0,0,0.45); backdrop-filter:blur(15px); }
    .login-title { font-size:42px; color:white; font-weight:900; }
    .login-subtitle { font-size:18px; color:#cbd5e1; margin-top:8px; }
    </style>
    <div class="login-box">
        <div style="font-size:72px;">🛏️</div>
        <div class="login-title">LOCAL MESITAS</div>
        <div class="login-subtitle">Sistema POS y Administración</div>
        <div style="font-size:48px; margin-top:25px;">🔐</div>
    </div>
    """)
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        clave = st.text_input("🔑 Contraseña", type="password", key="clave_login")
        if st.button("🚀 INGRESAR", use_container_width=True):
            if clave == CLAVE_ACCESO:
                st.session_state["autenticado"] = True
                st.rerun()
            else: st.error("❌ Contraseña incorrecta.")
    st.stop()

# ============================================================
#                 ESTILOS VISUALES Y HEADER
# ============================================================

html("""
<style>
.stApp { background:#f1f5f9; font-family: 'Segoe UI', sans-serif; }
.header-box { background: linear-gradient(135deg, #0f172a, #1e3a8a); padding:25px; border-radius:20px; color:white; text-align:center; margin-bottom:15px; }
.info-card { background:white; padding:15px; border-radius:15px; text-align:center; border:1px solid #e2e8f0; }
.total-card { background: #eff6ff; border:2px solid #3b82f6; border-radius:15px; padding:15px; text-align:center; font-weight:bold; }
.card-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.badge-ok { background-color: #dcfce7; color: #15803d; }
.badge-low { background-color: #fef3c7; color: #b45309; }
.badge-out { background-color: #fee2e2; color: #b91c1c; }
.prod-card-v2 { background: white; border-radius: 18px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 4px 15px rgba(0,0,0,0.04); height: 100%; }
.prod-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 8px; margin-bottom: 4px; min-height: 44px; }
.prod-price { font-size: 24px; font-weight: 900; color: #2563eb; margin: 6px 0; }
</style>
""")

col_t, col_s = st.columns([6, 1])
with col_s:
    if st.button("🔒 SALIR", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

html("""
<div class="header-box">
    <div style="font-size:38px; font-weight:900;">🛏️ LOCAL MESITAS</div>
    <div style="font-size:16px; color:#cbd5e1;">Sistema POS • Control de Inventarios y Ventas</div>
</div>
""")

df_inv = st.session_state["df_inv"]
df_ventas = st.session_state["df_ventas"]

dinero_recibido = float(df_ventas["ABONADO"].sum()) if not df_ventas.empty else 0.0
total_operaciones = len(df_ventas)
total_apartados = int(df_ventas["ESTADO"].str.contains("Apartado", case=False, na=False).sum()) if not df_ventas.empty else 0
total_stock = int(df_inv["STOCK"].sum()) if not df_inv.empty else 0

r1, r2, r3, r4 = st.columns(4)
r1.markdown(f'<div class="info-card">💰 Recaudado<br><b>${dinero_recibido:,.2f}</b></div>', unsafe_allow_html=True)
r2.markdown(f'<div class="info-card">📦 Stock Total<br><b>{total_stock} uds</b></div>', unsafe_allow_html=True)
r3.markdown(f'<div class="info-card">🧾 Ventas Totales<br><b>{total_operaciones}</b></div>', unsafe_allow_html=True)
r4.markdown(f'<div class="info-card">⏳ Apartados Pendientes<br><b>{total_apartados}</b></div>', unsafe_allow_html=True)

st.write("")

# ============================================================
#                 VENTANA MODAL DE VENTA (DIALOG)
# ============================================================

@st.dialog("🛒 Procesar Venta / Carrito de Compras")
def abrir_modal_venta():
    st.write("Agrega los productos que el cliente desea comprar:")

    df_inv_local = st.session_state["df_inv"]
    lista_prods = obtener_productos_vendibles(df_inv_local)

    if not lista_prods:
        st.warning("No hay productos disponibles para agregar.")
        return

    col_add1, col_add2, col_add3 = st.columns([3, 1, 1])
    prod_sel = col_add1.selectbox("Producto", lista_prods, key="modal_sel_prod")
    
    if prod_sel:
        prod_row = df_inv_local[df_inv_local["CATEGORIA"] == prod_sel]
        stk_max = int(prod_row.iloc[0]["STOCK"]) if not prod_row.empty else 0
        prc_unit = float(prod_row.iloc[0]["PRECIO"]) if not prod_row.empty else 0.0
    else:
        stk_max = 1
        prc_unit = 0.0

    cant_sel = col_add2.number_input("Cant.", min_value=1, max_value=max(1, stk_max), value=1, key="modal_cant_prod")
    
    st.write("")
    if col_add3.button("➕ AGREGAR", use_container_width=True):
        if stk_max <= 0:
            st.error("Producto agotado.")
        else:
            encontrado = False
            for item in st.session_state["carrito"]:
                if item["producto"] == prod_sel:
                    if item["cantidad"] + cant_sel <= stk_max:
                        item["cantidad"] += cant_sel
                        encontrado = True
                    else:
                        st.error(f"No hay suficiente stock. Máximo disponible: {stk_max}")
                        encontrado = True
                    break
            if not encontrado:
                st.session_state["carrito"].append({
                    "producto": prod_sel,
                    "cantidad": cant_sel,
                    "precio": prc_unit
                })
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Resumen del Carrito")

    if not st.session_state["carrito"]:
        st.info("El carrito está vacío. Agrega al menos un producto.")
    else:
        subtotal = 0.0
        for i, item in enumerate(st.session_state["carrito"]):
            tot_item = item["cantidad"] * item["precio"]
            subtotal += tot_item
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.write(f"**{item['producto']}**")
            c2.write(f"x{item['cantidad']}")
            c3.write(f"${tot_item:,.2f}")
            if c4.button("❌", key=f"del_cart_{i}"):
                st.session_state["carrito"].pop(i)
                st.rerun()

        st.markdown("---")
        descuento = st.number_input("🏷️ Descuento General ($)", min_value=0.0, max_value=float(subtotal), value=0.0)
        total_final = max(0.0, subtotal - descuento)
        st.markdown(f'<div class="total-card">TOTAL A PAGAR: ${total_final:,.2f}</div>', unsafe_allow_html=True)

        with st.form("form_finalizar_venta"):
            m_pago = st.selectbox("💳 Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
            c_nom = st.text_input("👤 Nombre Cliente", value="Cliente General")
            c_ced = st.text_input("🆔 Cédula/RUC", value="S/N")
            c_tel = st.text_input("📞 Teléfono", value="")
            c_dir = st.text_input("📍 Dirección Entrega", value="")

            destino_recibo = st.selectbox(
                "📲 Enviar Recibo por WhatsApp",
                ["Vendedor 1 (0990847819)", "Vendedor 2 (0983576800)"]
            )

            if st.form_submit_button("💰 FINALIZAR VENTA Y RECIBO", use_container_width=True):
                for item in st.session_state["carrito"]:
                    df_inv_local.loc[df_inv_local["CATEGORIA"] == item["producto"], "STOCK"] -= item["cantidad"]
                
                guardar_inventario(df_inv_local)
                st.session_state["df_inv"] = df_inv_local

                resumen_prods = " + ".join([f"{it['producto']} (x{it['cantidad']})" for it in st.session_state["carrito"]])
                cant_total = sum([it['cantidad'] for it in st.session_state["carrito"]])

                nueva_v_dict = {
                    "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "CATEGORIA": resumen_prods,
                    "CANTIDAD": cant_total,
                    "PRECIO_UNITARIO": total_final,
                    "TOTAL": total_final,
                    "ABONADO": total_final,
                    "SALDO_PENDIENTE": 0.0,
                    "METODO_PAGO": m_pago,
                    "CLIENTE": c_nom,
                    "CEDULA": c_ced,
                    "TELEFONO": c_tel,
                    "CORREO": "",
                    "DIRECCION": c_dir,
                    "ESTADO": "Pagado y Entregado",
                    "FOTO": "Sin foto"
                }

                df_v_act = pd.concat([st.session_state["df_ventas"], pd.DataFrame([nueva_v_dict])], ignore_index=True)
                guardar_ventas(df_v_act)
                st.session_state["df_ventas"] = df_v_act
                st.session_state["ultima_venta"] = nueva_v_dict
                st.session_state["carrito"] = []

                num_dest = NUMEROS_WHATSAPP[destino_recibo]
                st.session_state["redirect_url"] = generar_link_whatsapp(num_dest, nueva_v_dict)
                st.rerun()

# ============================================================
#                 NAVEGACIÓN PRINCIPAL
# ============================================================

tab_venta, tab_apartado, tab_inventario, tab_historial = st.tabs([
    "⚡ VENDER", "📦 APARTADOS", "🛠️ INVENTARIO", "📜 HISTORIAL Y GESTIÓN"
])

# ------------------------------------------------------------
# TAB 1: VENDER
# ------------------------------------------------------------
with tab_venta:
    if df_inv.empty:
        st.info("📦 No hay productos registrados en el inventario.")
    else:
        st.markdown("### 🎁 Promoción: Armar Combo (Cama + Colchón)")
        
        camas_disponibles = df_inv[
            df_inv["CATEGORIA"].str.contains("CAMA", case=False, na=False) & (df_inv["STOCK"] > 0)
        ]["CATEGORIA"].tolist()
        
        colchones_disponibles = df_inv[
            df_inv["CATEGORIA"].str.contains("COLCHON|COLCHÓN", case=False, na=False) & (df_inv["STOCK"] > 0)
        ]["CATEGORIA"].tolist()

        if camas_disponibles and colchones_disponibles:
            html("""
            <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); padding: 20px; border-radius: 18px; color: white; margin-bottom: 20px; border: 1px solid #6366f1;">
                <h4 style="margin:0; color:#a5b4fc;">🔥 Arma tu Combo Especial</h4>
                <p style="margin:5px 0 0 0; font-size:14px; color:#c7d2fe;">Selecciona una Cama y un Colchón. Al comprarlos, se descontará automático 1 unidad de stock a cada uno.</p>
            </div>
            """)

            c_combo1, c_combo2, c_combo3, c_combo4 = st.columns([3, 3, 2, 2])
            
            sel_cama = c_combo1.selectbox("🛏️ Seleccionar Cama", camas_disponibles, key="combo_cama_sel")
            sel_colchon = c_combo2.selectbox("💤 Seleccionar Colchón", colchones_disponibles, key="combo_colchon_sel")

            prc_c = float(df_inv[df_inv["CATEGORIA"] == sel_cama]["PRECIO"].values[0]) if sel_cama else 0.0
            prc_m = float(df_inv[df_inv["CATEGORIA"] == sel_colchon]["PRECIO"].values[0]) if sel_colchon else 0.0
            precio_sugerido = prc_c + prc_m

            precio_combo = c_combo3.number_input("💵 Precio Combo ($)", min_value=0.0, value=precio_sugerido, key="combo_precio_input")

            st.write("")
            if c_combo4.button("⚡ AGREGAR COMBO", use_container_width=True, type="primary"):
                if agregar_combo_al_carrito(sel_cama, sel_colchon, precio_combo):
                    st.success(f"✅ Combo agregado al carrito: {sel_cama} + {sel_colchon}")
                    abrir_modal_venta()
        else:
            st.warning("⚠️ Se requiere tener disponible al menos 1 Cama y 1 Colchón en stock para habilitar la creación de combos.")

        st.markdown("---")
        st.markdown("### 🛍️ Catálogo de Productos")
        
        cols_grid = st.columns(3)
        vendibles = df_inv[df_inv["CATEGORIA"].apply(lambda x: producto_es_vendible(df_inv, x))].copy()

        for i, (_, row) in enumerate(vendibles.iterrows()):
            stk = int(row['STOCK'])
            stk_min = int(row['STOCK_MINIMO'])
            
            if stk <= 0: badge_class, badge_text = "badge-out", "Agotado"
            elif stk <= stk_min: badge_class, badge_text = "badge-low", f"Últimas {stk} uds"
            else: badge_class, badge_text = "badge-ok", f"Stock: {stk} uds"

            with cols_grid[i % 3]:
                st.markdown(f"""
                <div class="prod-card-v2">
                    <span class="card-badge {badge_class}">{badge_text}</span>
                    <div class="prod-title">🛏️ {row['CATEGORIA']}</div>
                    <div class="prod-price">${row['PRECIO']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if stk > 0:
                    if st.button(f"🛒 Agregar al Carrito", key=f"btn_add_cart_{i}", use_container_width=True):
                        encontrado = False
                        for item in st.session_state["carrito"]:
                            if item["producto"] == row['CATEGORIA']:
                                if item["cantidad"] + 1 <= stk:
                                    item["cantidad"] += 1
                                    encontrado = True
                                break
                        if not encontrado:
                            st.session_state["carrito"].append({
                                "producto": row['CATEGORIA'],
                                "cantidad": 1,
                                "precio": float(row['PRECIO'])
                            })
                        abrir_modal_venta()
                else:
                    st.button("❌ Sin Stock", key=f"btn_select_dis_{i}", disabled=True, use_container_width=True)

        st.markdown("---")
        
        cant_items_cart = sum([item['cantidad'] for item in st.session_state["carrito"]])
        if st.button(f"🛒 VER CARRITO DE COMPRAS ({cant_items_cart} productos)", use_container_width=True, type="primary"):
            abrir_modal_venta()

        if st.session_state.get("redirect_url"):
            link_red = st.session_state["redirect_url"]
            st.success("✅ Venta procesada correctamente. Haz clic en el botón a continuación para abrir WhatsApp:")
            st.markdown(f'<a href="{link_red}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; font-weight:bold; cursor:pointer;">📲 ENVIAR RECIBO POR WHATSAPP</button></a>', unsafe_allow_html=True)

        if st.session_state.get("ultima_venta"):
            st.markdown("---")
            st.markdown("### 📄 Opciones de Recibo y Envío Manual")
            v_ult = st.session_state["ultima_venta"]

            c_w1, c_w2 = st.columns(2)
            with c_w1:
                link_w1 = generar_link_whatsapp("593990847819", v_ult)
                st.markdown(f'<a href="{link_w1}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📲 REENVIAR A 0990847819</button></a>', unsafe_allow_html=True)

            with c_w2:
                link_w2 = generar_link_whatsapp("593983576800", v_ult)
                st.markdown(f'<a href="{link_w2}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📲 REENVIAR A 0983576800</button></a>', unsafe_allow_html=True)

            if HAS_REPORTLAB:
                pdf_buf = generar_pdf_recibo(v_ult)
                st.write("")
                st.download_button("📄 Descargar Recibo PDF", data=pdf_buf, file_name=f"recibo_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf", use_container_width=True)

# ------------------------------------------------------------
# TAB 2: APARTADOS Y ABONOS
# ------------------------------------------------------------
with tab_apartado:
    col_ap1, col_ap2 = st.columns([1, 1])

    with col_ap1:
        st.markdown("### 📦 Crear Nuevo Apartado")
        prods_apartado = obtener_productos_vendibles(df_inv)

        if prods_apartado:
            prod_ap = st.selectbox("📦 Seleccionar Producto", prods_apartado, key="sel_ap_prod")
            fila_ap = df_inv[df_inv["CATEGORIA"] == prod_ap].iloc[0]
            stk_ap = int(fila_ap["STOCK"])
            prc_ap = float(fila_ap["PRECIO"])

            with st.form("form_apartado"):
                cli_ap = st.text_input("👤 Nombre Cliente")
                ced_ap = st.text_input("🆔 Cédula")
                tel_ap = st.text_input("📞 Teléfono")
                cant_ap = st.number_input("🔢 Cantidad", min_value=1, max_value=max(1, stk_ap), value=1)
                abono_ap = st.number_input("💵 Abono Inicial ($)", min_value=0.0, value=10.0)

                tot_ap = cant_ap * prc_ap
                saldo_ap = max(0.0, tot_ap - abono_ap)

                st.markdown(f'<div class="total-card">Total: ${tot_ap:,.2f} | Abono: ${abono_ap:,.2f} | Saldo: ${saldo_ap:,.2f}</div>', unsafe_allow_html=True)

                if st.form_submit_button("💾 GUARDAR APARTADO", use_container_width=True):
                    if not cli_ap.strip():
                        st.warning("⚠️ Ingrese el nombre del cliente.")
                    elif abono_ap > tot_ap:
                        st.error("❌ El abono no puede superar el total.")
                    else:
                        est_ap = "Pagado y Entregado" if saldo_ap <= 0 else "Apartado (Pendiente)"
                        
                        df_inv.loc[df_inv["CATEGORIA"] == prod_ap, "STOCK"] -= cant_ap
                        guardar_inventario(df_inv)
                        st.session_state["df_inv"] = df_inv

                        nuevo_ap = {
                            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "CATEGORIA": prod_ap, "CANTIDAD": cant_ap,
                            "PRECIO_UNITARIO": prc_ap, "TOTAL": tot_ap,
                            "ABONADO": abono_ap, "SALDO_PENDIENTE": saldo_ap,
                            "METODO_PAGO": "Efectivo", "CLIENTE": cli_ap,
                            "CEDULA": ced_ap, "TELEFONO": tel_ap, "CORREO": "",
                            "DIRECCION": "", "ESTADO": est_ap, "FOTO": "Sin foto"
                        }

                        df_v_act = pd.concat([st.session_state["df_ventas"], pd.DataFrame([nuevo_ap])], ignore_index=True)
                        guardar_ventas(df_v_act)
                        st.session_state["df_ventas"] = df_v_act
                        st.session_state["ultima_venta"] = nuevo_ap

                        st.success("✅ Apartado registrado.")
                        st.rerun()

    with col_ap2:
        st.markdown("### 💵 Gestión de Abonos de Pendientes")
        df_pending = df_ventas[df_ventas["SALDO_PENDIENTE"] > 0].copy()

        if df_pending.empty:
            st.info("🎉 No hay apartados pendientes de pago.")
        else:
            opciones_p = [f"ID {idx}: {row['CLIENTE']} - {row['CATEGORIA']} (Saldo: ${row['SALDO_PENDIENTE']:,.2f})" for idx, row in df_pending.iterrows()]
            sel_p = st.selectbox("👉 Seleccionar Cliente/Apartado", opciones_p)
            
            idx_real = int(sel_p.split(":")[0].replace("ID ", "").strip())
            row_sel = df_pending.loc[idx_real]

            st.write(f"**Cliente:** {row_sel['CLIENTE']} | **Teléfono:** {row_sel['TELEFONO']}")
            st.write(f"**Total Deuda:** ${row_sel['TOTAL']:,.2f} | **Saldo Restante:** ${row_sel['SALDO_PENDIENTE']:,.2f}")

            nuevo_abono = st.number_input("💵 Monto a Abonar ($)", min_value=0.01, max_value=float(row_sel['SALDO_PENDIENTE']), value=float(row_sel['SALDO_PENDIENTE']))

            if st.button("🤝 REGISTRAR ABONO", use_container_width=True):
                df_ventas.loc[idx_real, "ABONADO"] += nuevo_abono
                df_ventas.loc[idx_real, "SALDO_PENDIENTE"] -= nuevo_abono
                
                if df_ventas.loc[idx_real, "SALDO_PENDIENTE"] <= 0:
                    df_ventas.loc[idx_real, "ESTADO"] = "Pagado y Entregado"
                
                guardar_ventas(df_ventas)
                st.session_state["df_ventas"] = df_ventas
                st.success("✅ ¡Abono procesado con éxito!")
                st.rerun()

# ------------------------------------------------------------
# TAB 3: INVENTARIO (CREACIÓN Y EDICIÓN RÁPIDA)
# ------------------------------------------------------------
with tab_inventario:
    st.markdown("### 🛠️ Gestión y Reabastecimiento de Inventario")
    
    if not df_inv.empty and "STOCK_MINIMO" in df_inv.columns and "STOCK" in df_inv.columns:
        agotados = df_inv[df_inv["STOCK"] <= df_inv["STOCK_MINIMO"]]
        if not agotados.empty:
            st.warning("⚠️ **Atención: Productos bajo el Stock Mínimo Recomendado**")
            st.dataframe(agotados[["CATEGORIA", "STOCK", "STOCK_MINIMO"]], hide_index=True, use_container_width=True)

    if st.text_input("🔐 Clave Administrador", type="password", key="pwd_inv") == CLAVE_ADMIN:
        principales = [n for n in df_inv["CATEGORIA"].tolist() if " - " not in str(n)]
        opciones = ["✨ Crear Repositorio Principal", "📦 Crear Producto Simple"] + principales
        opc = st.selectbox("Acción / Categoría Padre", opciones)

        if opc == "✨ Crear Repositorio Principal":
            nom = st.text_input("Nombre de la Categoría Principal (Ej: CAMAS)")
            if st.button("➕ CREAR REPOSITORIO"):
                if nom.strip() and not existe_producto(df_inv, nom.strip()):
                    nuevo_df = pd.DataFrame([{"CATEGORIA": nom.strip(), "STOCK": 0, "PRECIO": 0.0, "STOCK_MINIMO": 1}])
                    df_inv = pd.concat([df_inv, nuevo_df], ignore_index=True)
                    guardar_inventario(df_inv)
                    st.session_state["df_inv"] = df_inv
                    st.success("Creado correctamente.")
                    st.rerun()

        elif opc == "📦 Crear Producto Simple":
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombre del Producto")
            stk = c2.number_input("Stock Inicial", min_value=0, value=1)
            prc = c3.number_input("Precio ($)", min_value=0.0, value=10.0)
            if st.button("➕ CREAR PRODUCTO"):
                if nom.strip() and not existe_producto(df_inv, nom.strip()):
                    nuevo_df = pd.DataFrame([{"CATEGORIA": nom.strip(), "STOCK": stk, "PRECIO": prc, "STOCK_MINIMO": 1}])
                    df_inv = pd.concat([df_inv, nuevo_df], ignore_index=True)
                    guardar_inventario(df_inv)
                    st.session_state["df_inv"] = df_inv
                    st.success("Creado correctamente.")
                    st.rerun()
        else:
            sub_nom = st.text_input(f"Subproducto para '{opc}'")
            stk = st.number_input("Stock Subproducto", min_value=0, value=1)
            prc = st.number_input("Precio Subproducto", min_value=0.0, value=10.0)
            if st.button("➕ CREAR SUBPRODUCTO"):
                full_nom = f"{opc} - {sub_nom.strip()}"
                if sub_nom.strip() and not existe_producto(df_inv, full_nom):
                    nuevo_df = pd.DataFrame([{"CATEGORIA": full_nom, "STOCK": stk, "PRECIO": prc, "STOCK_MINIMO": 1}])
                    df_inv = pd.concat([df_inv, nuevo_df], ignore_index=True)
                    guardar_inventario(df_inv)
                    st.session_state["df_inv"] = df_inv
                    st.success("Subproducto creado.")
                    st.rerun()

        st.markdown("---")
        st.subheader("Tabla Completa de Inventario")
        st.dataframe(df_inv, use_container_width=True)

# ------------------------------------------------------------
# TAB 4: HISTORIAL Y BORRADO SELECCIONABLE
# ------------------------------------------------------------
with tab_historial:
    st.markdown("### 📜 Historial de Ventas y Eliminación Seleccionable")
    
    if not df_ventas.empty:
        csv_data = df_ventas.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📊 Descargar Historial Completo (Excel / CSV)",
            data=csv_data,
            file_name=f"ventas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("#### 🔍 Selecciona con el check (☑️) las ventas que deseas eliminar:")
        
        df_display = df_ventas.copy()
        df_display.insert(0, "SELECCIONAR", False)

        df_editado = st.data_editor(
            df_display,
            hide_index=True,
            use_container_width=True,
            column_config={
                "SELECCIONAR": st.column_config.CheckboxColumn("Eliminar", default=False),
                "TOTAL": st.column_config.NumberColumn("Total", format="$%.2f"),
                "ABONADO": st.column_config.NumberColumn("Abonado", format="$%.2f"),
                "SALDO_PENDIENTE": st.column_config.NumberColumn("Saldo", format="$%.2f"),
            },
            disabled=[col for col in COLUMNAS_VENTAS],
            key="editor_ventas"
        )

        filas_seleccionadas = df_editado[df_editado["SELECCIONAR"] == True]
        cant_seleccionada = len(filas_seleccionadas)

        st.markdown("---")
        st.markdown("### 🗑️ Panel de Borrado de Registros")
        
        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            st.info(f"📌 Registros marcados para eliminar: **{cant_seleccionada}**")
        
        with col_b2:
            pwd_borrado = st.text_input("🔐 Clave Administrador para borrar", type="password", key="pwd_borrar_sel")

        c_btn1, c_btn2 = st.columns(2)
        
        with c_btn1:
            if st.button("🗑️ ELIMINAR VENTAS SELECCIONADAS", use_container_width=True, disabled=(cant_seleccionada == 0)):
                if pwd_borrado == CLAVE_ADMIN:
                    df_filtrado = df_editado[df_editado["SELECCIONAR"] == False].drop(columns=["SELECCIONAR"])
                    guardar_ventas(df_filtrado)
                    st.session_state["df_ventas"] = df_filtrado
                    st.session_state["ultima_venta"] = None
                    st.success(f"✅ Se eliminaron {cant_seleccionada} registro(s) correctamente.")
                    st.rerun()
                else:
                    st.error("❌ Clave de administrador incorrecta.")

        with c_btn2:
            if st.button("🔥 BORRAR TODO EL HISTORIAL COMPLETO", use_container_width=True):
                if pwd_borrado == CLAVE_ADMIN:
                    df_v_vacio = pd.DataFrame(columns=COLUMNAS_VENTAS)
                    guardar_ventas(df_v_vacio)
                    st.session_state["df_ventas"] = df_v_vacio
                    st.session_state["ultima_venta"] = None
                    st.success("✅ Se ha vaciado todo el historial de ventas.")
                    st.rerun()
                else:
                    st.error("❌ Clave de administrador incorrecta.")
    else:
        st.info("Sin registros de ventas.")
