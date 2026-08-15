from datetime import datetime
import os
import textwrap
import urllib.parse
import pandas as pd
import streamlit as st

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
#            FUNCIONES AUXILIARES Y MANEJO DE DATOS
# ============================================================

def html(contenido):
    texto_limpio = textwrap.dedent(contenido).strip()
    texto_limpio = " ".join(line.strip() for line in texto_limpio.splitlines())
    return st.markdown(texto_limpio, unsafe_allow_html=True)

def guardar_csv(df, ruta):
    df.to_csv(ruta, index=False, encoding="utf-8-sig")

def normalizar_inventario(df):
    for col in ["CATEGORIA", "STOCK", "PRECIO"]:
        if col not in df.columns:
            df[col] = "" if col == "CATEGORIA" else 0
    df["CATEGORIA"] = df["CATEGORIA"].fillna("").astype(str).str.strip()
    df["STOCK"] = pd.to_numeric(df["STOCK"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    df["PRECIO"] = pd.to_numeric(df["PRECIO"], errors="coerce").fillna(0.0).clip(lower=0)
    return df[df["CATEGORIA"] != ""].reset_index(drop=True)[["CATEGORIA", "STOCK", "PRECIO"]]

def normalizar_ventas(df):
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

def obtener_icono(categoria):
    texto = str(categoria).lower()
    if "combo" in texto: return "🎁"
    if "cama" in texto: return "🛏️"
    if "colchon" in texto or "colchón" in texto: return "💤"
    if "armario" in texto: return "🚪"
    if "pajarita" in texto: return "🎀"
    return "📦"

def estado_stock(stock):
    stock = max(0, int(stock))
    if stock == 0: return ("🔴 AGOTADO", "#dc2626")
    if stock <= 2: return ("🟠 POCO STOCK", "#ea580c")
    return ("🟢 DISPONIBLE", "#16a34a")

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
    return [nombre for nombre in df["CATEGORIA"].tolist() if producto_es_vendible(df, nombre)]

def existe_producto(df, nombre):
    return nombre.strip().lower() in df["CATEGORIA"].astype(str).str.strip().str.lower().values

# ============================================================
#                 INICIALIZACIÓN DE SESIÓN
# ============================================================

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if "df_inv" not in st.session_state:
    st.session_state["df_inv"] = cargar_inventario()

if "df_ventas" not in st.session_state:
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
.product-card { background:white; border:1px solid #e2e8f0; border-radius:18px; padding:15px; text-align:center; margin-bottom:10px; }
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

# Carga de estado global actualizado
df_inv = st.session_state["df_inv"]
df_ventas = st.session_state["df_ventas"]

dinero_recibido = float(df_ventas["ABONADO"].sum()) if not df_ventas.empty else 0.0
total_operaciones = len(df_ventas)
total_apartados = int(df_ventas["ESTADO"].str.contains("Apartado", case=False, na=False).sum()) if not df_ventas.empty else 0
total_stock = int(df_inv["STOCK"].sum()) if not df_inv.empty else 0

r1, r2, r3, r4 = st.columns(4)
r1.markdown(f'<div class="info-card">💰 Ventas<br><b>${dinero_recibido:,.2f}</b></div>', unsafe_allow_html=True)
r2.markdown(f'<div class="info-card">📦 Stock Total<br><b>{total_stock} uds</b></div>', unsafe_allow_html=True)
r3.markdown(f'<div class="info-card">🧾 Operaciones<br><b>{total_operaciones}</b></div>', unsafe_allow_html=True)
r4.markdown(f'<div class="info-card">📦 Apartados<br><b>{total_apartados}</b></div>', unsafe_allow_html=True)

st.write("")

# ============================================================
#                 Navegación
# ============================================================

tab_venta, tab_apartado, tab_inventario, tab_historial = st.tabs([
    "⚡ VENDER", "📦 APARTADOS", "🛠️ INVENTARIO", "📜 HISTORIAL"
])

# ------------------------------------------------------------
# TAB 1: VENDER
# ------------------------------------------------------------
with tab_venta:
    if df_inv.empty:
        st.info("📦 No hay productos registrados en el inventario.")
    else:
        st.markdown("### 📦 Productos Disponibles")
        lista_productos = obtener_productos_vendibles(df_inv)
        OPCION_COMBO = "🎁 Combo (Cama + Colchón)"
        opciones_venta = [OPCION_COMBO] + lista_productos

        producto_elegido = st.selectbox("👉 Seleccionar producto/combo a vender", opciones_venta, key="sel_venta_prod")
        es_combo = (producto_elegido == OPCION_COMBO)

        if es_combo:
            camas = [p for p in lista_productos if "cama" in p.lower()]
            colchones = [p for p in lista_productos if "colchon" in p.lower() or "colchón" in p.lower()]

            if not camas or not colchones:
                st.error("⚠️ Para vender un combo, debe tener al menos 1 Cama y 1 Colchón registrados.")
            else:
                c1, c2 = st.columns(2)
                cama_combo = c1.selectbox("🛏️ Seleccionar Cama", camas)
                colchon_combo = c2.selectbox("💤 Seleccionar Colchón", colchones)

                stock_cama = int(df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]["STOCK"])
                stock_colchon = int(df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]["STOCK"])
                stock_disp = min(stock_cama, stock_colchon)

                sugerido = float(df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]["PRECIO"]) + float(df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]["PRECIO"])
                precio_unitario = st.number_input("🏷️ Precio Final del Combo ($)", min_value=0.0, value=sugerido, step=5.0)
                nombre_venta = f"COMBO: {cama_combo} + {colchon_combo}"
        else:
            fila = df_inv[df_inv["CATEGORIA"] == producto_elegido].iloc[0]
            stock_disp = int(fila["STOCK"])
            precio_unitario = float(fila["PRECIO"])
            nombre_venta = producto_elegido

        if not es_combo or (camas and colchones):
            if stock_disp <= 0:
                st.error(f"🔴 **{nombre_venta}** se encuentra agotado.")
            else:
                with st.form("form_venta"):
                    st.markdown("### 🧾 Registrar Transacción")
                    a1, a2, a3 = st.columns(3)
                    cantidad = 1 if es_combo else a1.number_input("🔢 Cantidad", min_value=1, max_value=stock_disp, value=1)
                    metodo_pago = a2.selectbox("💳 Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
                    descuento = a3.number_input("🏷️ Descuento ($)", min_value=0.0, value=0.0)

                    c_nom = st.text_input("👤 Cliente", value="Cliente General")
                    c_ced = st.text_input("🆔 Cédula/RUC", value="S/N")
                    c_tel = st.text_input("📞 Teléfono", value="")
                    c_dir = st.text_input("📍 Dirección", value="")
                    foto = st.file_uploader("📸 Comprobante/Foto", type=["jpg", "png", "jpeg"])

                    total_final = max(0.0, (cantidad * precio_unitario) - descuento)
                    st.markdown(f'<div class="total-card">TOTAL A COBRAR: ${total_final:,.2f}</div>', unsafe_allow_html=True)

                    if st.form_submit_button("💰 COMPLETAR VENTA", use_container_width=True):
                        ruta_foto = guardar_foto(foto)
                        # Descontar inventario
                        if es_combo:
                            df_inv.loc[df_inv["CATEGORIA"] == cama_combo, "STOCK"] -= 1
                            df_inv.loc[df_inv["CATEGORIA"] == colchon_combo, "STOCK"] -= 1
                        else:
                            df_inv.loc[df_inv["CATEGORIA"] == producto_elegido, "STOCK"] -= cantidad

                        # Guardar cambios
                        guardar_csv(df_inv, FILE_INV)
                        st.session_state["df_inv"] = df_inv

                        # Guardar Venta
                        nueva_v = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "CATEGORIA": nombre_venta, "CANTIDAD": cantidad,
                            "PRECIO_UNITARIO": precio_unitario, "TOTAL": total_final,
                            "ABONADO": total_final, "SALDO_PENDIENTE": 0.0,
                            "METODO_PAGO": metodo_pago, "CLIENTE": c_nom,
                            "CEDULA": c_ced, "TELEFONO": c_tel, "CORREO": "",
                            "DIRECCION": c_dir, "ESTADO": "Pagado y Entregado", "FOTO": ruta_foto
                        }])
                        df_v_actualizado = pd.concat([st.session_state["df_ventas"], nueva_v], ignore_index=True)
                        guardar_csv(df_v_actualizado, FILE_VENTAS)
                        st.session_state["df_ventas"] = df_v_actualizado

                        st.success("✅ ¡Venta efectuada con éxito!")
                        st.rerun()

# ------------------------------------------------------------
# TAB 2: APARTADOS
# ------------------------------------------------------------
with tab_apartado:
    st.markdown("### 📦 Crear Nuevo Apartado")
    prods_apartado = obtener_productos_vendibles(df_inv)

    if not prods_apartado:
        st.info("No hay productos para apartar.")
    else:
        prod_ap = st.selectbox("📦 Seleccionar Producto", prods_apartado, key="sel_ap_prod")
        fila_ap = df_inv[df_inv["CATEGORIA"] == prod_ap].iloc[0]
        stk_ap = int(fila_ap["STOCK"])
        prc_ap = float(fila_ap["PRECIO"])

        with st.form("form_apartado"):
            cli_ap = st.text_input("👤 Cliente")
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
                    st.error("❌ El abono no puede ser superior al total.")
                else:
                    est_ap = "Pagado y Entregado" if saldo_ap <= 0 else "Apartado (Pendiente)"
                    if saldo_ap <= 0:
                        df_inv.loc[df_inv["CATEGORIA"] == prod_ap, "STOCK"] -= cant_ap
                        guardar_csv(df_inv, FILE_INV)
                        st.session_state["df_inv"] = df_inv

                    nuevo_ap = pd.DataFrame([{
                        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "CATEGORIA": prod_ap, "CANTIDAD": cant_ap,
                        "PRECIO_UNITARIO": prc_ap, "TOTAL": tot_ap,
                        "ABONADO": abono_ap, "SALDO_PENDIENTE": saldo_ap,
                        "METODO_PAGO": "Efectivo", "CLIENTE": cli_ap,
                        "CEDULA": ced_ap, "TELEFONO": tel_ap, "CORREO": "",
                        "DIRECCION": "", "ESTADO": est_ap, "FOTO": "Sin foto"
                    }])

                    df_v_act = pd.concat([st.session_state["df_ventas"], nuevo_ap], ignore_index=True)
                    guardar_csv(df_v_act, FILE_VENTAS)
                    st.session_state["df_ventas"] = df_v_act

                    st.success("✅ Apartado guardado con éxito.")
                    st.rerun()

# ------------------------------------------------------------
# TAB 3: INVENTARIO
# ------------------------------------------------------------
with tab_inventario:
    st.markdown("### 🛠️ Administración de Inventario")
    if st.text_input("🔐 Clave Administrador", type="password", key="pwd_inv") == CLAVE_ADMIN:
        principales = [n for n in df_inv["CATEGORIA"].tolist() if " - " not in str(n)]
        opciones = ["✨ Crear Repositorio Principal", "📦 Crear Producto Simple"] + principales
        opc = st.selectbox("Acción / Categoría Padre", opciones)

        if opc == "✨ Crear Repositorio Principal":
            nom = st.text_input("Nombre de la Categoría Principal (Ej: Camas)")
            if st.button("➕ CREAR REPOSITORIO"):
                if nom.strip() and not existe_producto(df_inv, nom.strip()):
                    df_inv = pd.concat([df_inv, pd.DataFrame([{"CATEGORIA": nom.strip(), "STOCK": 0, "PRECIO": 0.0}])], ignore_index=True)
                    guardar_csv(df_inv, FILE_INV)
                    st.session_state["df_inv"] = df_inv
                    st.success("Creado correctamente.")
                    st.rerun()

        elif opc == "📦 Crear Producto Simple":
            nom = st.text_input("Nombre del Producto")
            stk = st.number_input("Stock", min_value=0, value=1)
            prc = st.number_input("Precio", min_value=0.0, value=10.0)
            if st.button("➕ CREAR PRODUCTO"):
                if nom.strip() and not existe_producto(df_inv, nom.strip()):
                    df_inv = pd.concat([df_inv, pd.DataFrame([{"CATEGORIA": nom.strip(), "STOCK": stk, "PRECIO": prc}])], ignore_index=True)
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
                    df_inv = pd.concat([df_inv, pd.DataFrame([{"CATEGORIA": full_nom, "STOCK": stk, "PRECIO": prc}])], ignore_index=True)
                    guardar_csv(df_inv, FILE_INV)
                    st.session_state["df_inv"] = df_inv
                    st.success("Subproducto creado.")
                    st.rerun()

        st.markdown("---")
        st.dataframe(df_inv, use_container_width=True)

# ------------------------------------------------------------
# TAB 4: HISTORIAL
# ------------------------------------------------------------
with tab_historial:
    st.markdown("### 📜 Historial de Ventas y Registro")
    if not df_ventas.empty:
        st.dataframe(df_ventas, use_container_width=True, hide_index=True)
    else:
        st.info("Sin registros de ventas.")
