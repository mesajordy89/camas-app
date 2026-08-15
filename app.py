from datetime import datetime
import io
import os
import textwrap
import urllib.parse
import pandas as pd
import streamlit as st

# Intentar cargar reportlab para los comprobantes PDF de manera segura
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

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"
CARPETA_FOTOS = "fotos_ventas"

NUMEROS_WHATSAPP = ["593990847819", "593983576800"]

os.makedirs(CARPETA_FOTOS, exist_ok=True)

COLUMNAS_VENTAS = [
    "FECHA", "CATEGORIA", "CANTIDAD", "PRECIO_UNITARIO", "TOTAL",
    "ABONADO", "SALDO_PENDIENTE", "METODO_PAGO", "CLIENTE", "CEDULA",
    "TELEFONO", "CORREO", "DIRECCION", "ESTADO", "FOTO"
]

# ============================================================
#            FUNCIONES AUXILIARES Y MANEJO DE DATOS
# ============================================================

def html(contenido):
    texto_limpio = textwrap.dedent(contenido).strip()
    texto_limpio = " ".join(line.strip() for line in texto_limpio.splitlines())
    return st.markdown(texto_limpio, unsafe_allow_html=True)

def guardar_csv(df, ruta):
    df.to_csv(ruta, index=False, encoding="utf-8-sig")

def normalizar_inventario(df_input):
    if df_input is None or df_input.empty:
        return pd.DataFrame(columns=["CATEGORIA", "STOCK", "PRECIO", "STOCK_MINIMO"])
    
    df = df_input.copy()
    
    if "CATEGORIA" not in df.columns:
        df["CATEGORIA"] = ""
    if "STOCK" not in df.columns:
        df["STOCK"] = 0
    if "PRECIO" not in df.columns:
        df["PRECIO"] = 0.0
    if "STOCK_MINIMO" not in df.columns:
        df["STOCK_MINIMO"] = 1

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
            if columna == "ABONADO":
                df[columna] = pd.to_numeric(df.get("TOTAL", 0), errors="coerce").fillna(0.0)
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

    for col in ["CANTIDAD", "PRECIO_UNITARIO", "TOTAL", "ABONADO", "SALDO_PENDIENTE"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["CANTIDAD"] = df["CANTIDAD"].astype(int).clip(lower=0)
    for col in ["PRECIO_UNITARIO", "TOTAL", "ABONADO", "SALDO_PENDIENTE"]:
        df[col] = df[col].clip(lower=0)

    for col in ["FECHA", "CATEGORIA", "METODO_PAGO", "CLIENTE", "CEDULA", "TELEFONO", "CORREO", "DIRECCION", "ESTADO", "FOTO"]:
        df[col] = df[col].fillna("").astype(str)

    return df[COLUMNAS_VENTAS]

def cargar_inventario():
    if os.path.exists(FILE_INV):
        try:
            df = pd.read_csv(FILE_INV, encoding="utf-8-sig")
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame([
            {"CATEGORIA": "Camas", "STOCK": 5, "PRECIO": 150.0, "STOCK_MINIMO": 2},
            {"CATEGORIA": "Colchones", "STOCK": 5, "PRECIO": 100.0, "STOCK_MINIMO": 2},
            {"CATEGORIA": "Armarios Grandes", "STOCK": 2, "PRECIO": 200.0, "STOCK_MINIMO": 1},
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

def generar_pdf_recibo(venta_dict):
    if not HAS_REPORTLAB:
        return None
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
📦 *Producto:* {venta_dict.get('CATEGORIA')} (x{venta_dict.get('CANTIDAD')})
💰 *Total:* ${venta_dict.get('TOTAL'):,.2f}
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
    if df.empty or "CATEGORIA" not in df.columns:
        return []
    return [nombre for nombre in df["CATEGORIA"].tolist() if producto_es_vendible(df, nombre)]

def existe_producto(df, nombre):
    if df.empty or "CATEGORIA" not in df.columns:
        return False
    return nombre.strip().lower() in df["CATEGORIA"].astype(str).str.strip().str.lower().values

# ============================================================
#                 INICIALIZACIÓN Y NORMALIZACIÓN DE SESIÓN
# ============================================================

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if "ultima_venta" not in st.session_state:
    st.session_state["ultima_venta"] = None

st.session_state["df_inv"] = cargar_inventario()
st.session_state["df_ventas"] = cargar_ventas()

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
            else:
                st.error("❌ Contraseña incorrecta.")
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
#                 NAVEGACIÓN PRINCIPAL
# ============================================================

tab_venta, tab_apartado, tab_inventario, tab_historial = st.tabs([
    "⚡ VENDER", "📦 APARTADOS", "🛠️ INVENTARIO", "📜 HISTORIAL Y REPORTES"
])

# ------------------------------------------------------------
# TAB 1: VENDER
# ------------------------------------------------------------
with tab_venta:
    if df_inv.empty:
        st.info("📦 No hay productos registrados en el inventario.")
    else:
        st.markdown("### 📦 Registro de Ventas Directas")
        lista_productos = obtener_productos_vendibles(df_inv)
        OPCION_COMBO = "🎁 Combo (Cama + Colchón)"
        opciones_venta = [OPCION_COMBO] + lista_productos

        producto_elegido = st.selectbox("👉 Seleccionar producto/combo a vender", opciones_venta, key="sel_venta_prod")
        es_combo = (producto_elegido == OPCION_COMBO)

        if es_combo:
            camas = [p for p in lista_productos if "cama" in p.lower()]
            colchones = [p for p in lista_productos if "colchon" in p.lower() or "colchón" in p.lower()]

            if not camas or not colchones:
                st.error("⚠️ Para vender un combo, debe existir al menos 1 Cama y 1 Colchón disponibles.")
            else:
                c1, c2 = st.columns(2)
                cama_combo = c1.selectbox("🛏️ Seleccionar Cama", camas)
                colchon_combo = c2.selectbox("💤 Seleccionar Colchón", colchones)

                stock_cama = int(df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]["STOCK"])
                stock_colchon = int(df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]["STOCK"])
                stock_disp = min(stock_cama, stock_colchon)

                sugerido = float(df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]["PRECIO"]) + float(df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]["PRECIO"])
                precio_unitario = st.number_input("🏷️ Precio Final Combo ($)", min_value=0.0, value=sugerido, step=5.0)
                nombre_venta = f"COMBO: {cama_combo} + {colchon_combo}"
                st.info(f"💡 Combos armables en stock: **{stock_disp}** unidades")
        else:
            fila = df_inv[df_inv["CATEGORIA"] == producto_elegido].iloc[0]
            stock_disp = int(fila["STOCK"])
            precio_unitario = float(fila["PRECIO"])
            nombre_venta = producto_elegido

        if not es_combo or (camas and colchones):
            if stock_disp <= 0:
                st.error(f"🔴 **{nombre_venta}** se encuentra totalmente agotado.")
            else:
                with st.form("form_venta"):
                    a1, a2, a3 = st.columns(3)
                    cantidad = 1 if es_combo else a1.number_input("🔢 Cantidad", min_value=1, max_value=stock_disp, value=1)
                    metodo_pago = a2.selectbox("💳 Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
                    # DESCUENTO MÁXIMO LIMITADO A $10 DÓLARES
                    descuento = a3.number_input("🏷️ Descuento ($ Máx $10)", min_value=0.0, max_value=10.0, value=0.0, step=1.0)

                    c_nom = st.text_input("👤 Nombre Cliente", value="Cliente General")
                    c_ced = st.text_input("🆔 Cédula/RUC", value="S/N")
                    c_tel = st.text_input("📞 Teléfono", value="")
                    c_dir = st.text_input("📍 Dirección Entrega", value="")

                    total_final = max(0.0, (cantidad * precio_unitario) - descuento)
                    st.markdown(f'<div class="total-card">TOTAL A COBRAR: ${total_final:,.2f}</div>', unsafe_allow_html=True)

                    if st.form_submit_button("💰 COMPLETAR VENTA", use_container_width=True):
                        if es_combo:
                            df_inv.loc[df_inv["CATEGORIA"] == cama_combo, "STOCK"] -= 1
                            df_inv.loc[df_inv["CATEGORIA"] == colchon_combo, "STOCK"] -= 1
                        else:
                            df_inv.loc[df_inv["CATEGORIA"] == producto_elegido, "STOCK"] -= cantidad

                        guardar_csv(df_inv, FILE_INV)
                        st.session_state["df_inv"] = df_inv

                        nueva_v_dict = {
                            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "CATEGORIA": nombre_venta, "CANTIDAD": cantidad,
                            "PRECIO_UNITARIO": precio_unitario, "TOTAL": total_final,
                            "ABONADO": total_final, "SALDO_PENDIENTE": 0.0,
                            "METODO_PAGO": metodo_pago, "CLIENTE": c_nom,
                            "CEDULA": c_ced, "TELEFONO": c_tel, "CORREO": "",
                            "DIRECCION": c_dir, "ESTADO": "Pagado y Entregado", "FOTO": "Sin foto"
                        }
                        df_v_actualizado = pd.concat([st.session_state["df_ventas"], pd.DataFrame([nueva_v_dict])], ignore_index=True)
                        guardar_csv(df_v_actualizado, FILE_VENTAS)
                        st.session_state["df_ventas"] = df_v_actualizado
                        st.session_state["ultima_venta"] = nueva_v_dict

                        st.success("✅ ¡Venta efectuada con éxito!")
                        st.rerun()

        # ÁREA DE ENVIAR RECIBO Y DESCARGAR TRAS FINALIZAR VENTA
        if st.session_state.get("ultima_venta"):
            st.markdown("---")
            st.markdown("### 📄 Opciones de Recibo y Envío")
            v_ult = st.session_state["ultima_venta"]

            c_w1, c_w2 = st.columns(2)
            with c_w1:
                link_w1 = generar_link_whatsapp("593990847819", v_ult)
                st.markdown(f'<a href="{link_w1}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📲 ENVIAR RECIBO A 0990847819</button></a>', unsafe_allow_html=True)

            with c_w2:
                link_w2 = generar_link_whatsapp("593983576800", v_ult)
                st.markdown(f'<a href="{link_w2}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📲 ENVIAR RECIBO A 0983576800</button></a>', unsafe_allow_html=True)

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
                        guardar_csv(df_inv, FILE_INV)
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
                        guardar_csv(df_v_act, FILE_VENTAS)
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
                
                guardar_csv(df_ventas, FILE_VENTAS)
                st.session_state["df_ventas"] = df_ventas
                st.success("✅ ¡Abono procesado con éxito!")
                st.rerun()

# ------------------------------------------------------------
# TAB 3: INVENTARIO Y ALERTAS DE STOCK
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
            nom = st.text_input("Nombre de la Categoría Principal (Ej: Camas)")
            if st.button("➕ CREAR REPOSITORIO"):
                if nom.strip() and not existe_producto(df_inv, nom.strip()):
                    nuevo_df = pd.DataFrame([{"CATEGORIA": nom.strip(), "STOCK": 0, "PRECIO": 0.0, "STOCK_MINIMO": 1}])
                    df_inv = pd.concat([df_inv, nuevo_df], ignore_index=True)
                    guardar_csv(df_inv, FILE_INV)
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
                    guardar_csv(df_inv, FILE_INV)
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
                    guardar_csv(df_inv, FILE_INV)
                    st.session_state["df_inv"] = df_inv
                    st.success("Subproducto creado.")
                    st.rerun()

        st.markdown("---")
        st.subheader("Tabla Completa de Inventario")
        st.dataframe(df_inv, use_container_width=True)

# ------------------------------------------------------------
# TAB 4: HISTORIAL Y REPORTES (CON ELIMINACIÓN ADMIN)
# ------------------------------------------------------------
with tab_historial:
    st.markdown("### 📜 Historial de Ventas y Filtros")
    if not df_ventas.empty:
        csv_data = df_ventas.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        
        st.download_button(
            label="📊 Descargar Historial (Abrir en Excel / CSV)",
            data=csv_data,
            file_name=f"ventas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.dataframe(df_ventas, use_container_width=True, hide_index=True)
    else:
        st.info("Sin registros de ventas.")

    st.markdown("---")
    st.markdown("### 🗑️ Zona de Seguridad - Borrar Historial")
    with st.expander("⚠️ Abrir Opciones de Eliminación de Ventas"):
        st.warning("⚠️ **ATENCIÓN:** Esta acción eliminará todo el historial de ventas y reiniciará el valor recaudado a $0.00.")
        clave_borrado = st.text_input("🔐 Ingrese Clave Administrador para autorizar el borrado", type="password", key="pwd_borrado")
        
        if st.button("🔥 ELIMINAR TODO EL HISTORIAL DE VENTAS", use_container_width=True):
            if clave_borrado == CLAVE_ADMIN:
                df_v_vacio = pd.DataFrame(columns=COLUMNAS_VENTAS)
                guardar_csv(df_v_vacio, FILE_VENTAS)
                st.session_state["df_ventas"] = df_v_vacio
                st.session_state["ultima_venta"] = None
                st.success("✅ El historial de ventas se ha borrado correctamente y los contadores han sido reiniciados.")
                st.rerun()
            else:
                st.error("❌ Clave de administrador incorrecta.")
