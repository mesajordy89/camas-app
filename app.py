import streamlit as st
import pandas as pd
import datetime
import urllib.parse
import requests
import base64
import io
import os

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Local Mesitas - Sistema POS", page_icon="🛏️", layout="wide")

# Credenciales y Configuración de GitHub
REPO_GITHUB = "mesajordy89/camas-app"
CLAVE_ACCESO = st.secrets.get("CLAVE_ACCESO", "1234")
CLAVE_ADMIN = st.secrets.get("CLAVE_ADMIN", "1234")

# Estilos CSS
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .header-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: white; padding: 2.5rem; border-radius: 16px;
        text-align: center; margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
    }
    .metric-card {
        background: white; padding: 1.2rem; border-radius: 12px;
        border: 1px solid #e2e8f0; text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .metric-title { color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #0f172a; font-size: 1.6rem; font-weight: 700; margin-top: 0.3rem; }
    div[data-testid="stForm"] { background: white; border-radius: 12px; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. PERSISTENCIA CON GITHUB Y RESPALDO LOCAL
# -----------------------------------------------------------------------------
def cargar_csv_github(ruta_archivo):
    """Carga datos de GitHub. Si la red falla, lee el respaldo local."""
    df_resultado = pd.DataFrame()
    token = st.secrets.get("GITHUB_TOKEN", None)
    
    if token:
        url = f"https://raw.githubusercontent.com/{REPO_GITHUB}/main/{ruta_archivo}"
        headers = {"Authorization": f"token {token}"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                df_resultado = pd.read_csv(io.StringIO(res.text), encoding="utf-8-sig")
                # Guardar copia de respaldo en disco local
                df_resultado.to_csv(ruta_archivo, index=False, encoding="utf-8-sig")
                return df_resultado
        except Exception:
            pass

    # Respaldo local si falla la red o GitHub no responde
    if os.path.exists(ruta_archivo):
        try:
            return pd.read_csv(ruta_archivo, encoding="utf-8-sig")
        except Exception:
            pass

    return pd.DataFrame()

def guardar_csv_github(df, ruta_archivo, mensaje_commit):
    """Guarda en disco local y sincroniza con el repositorio GitHub."""
    # 1. Guardar primero en el entorno local como seguro
    df.to_csv(ruta_archivo, index=False, encoding="utf-8-sig")

    token = st.secrets.get("GITHUB_TOKEN", None)
    if not token:
        st.warning("⚠️ No se encontró GITHUB_TOKEN en Secrets. Se guardó únicamente en local.")
        return False

    url_api = f"https://api.github.com/repos/{REPO_GITHUB}/contents/{ruta_archivo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    csv_content = df.to_csv(index=False, encoding="utf-8-sig")
    content_b64 = base64.b64encode(csv_content.encode('utf-8-sig')).decode('utf-8')
    
    sha = None
    try:
        res_get = requests.get(url_api, headers=headers, timeout=5)
        if res_get.status_code == 200:
            sha = res_get.json().get("sha")
    except Exception:
        pass

    data = {
        "message": mensaje_commit,
        "content": content_b64
    }
    if sha:
        data["sha"] = sha

    try:
        res_put = requests.put(url_api, json=data, headers=headers, timeout=5)
        return res_put.status_code in [200, 201]
    except Exception as e:
        st.error(f"Error de conexión con GitHub: {e}")
        return False

# -----------------------------------------------------------------------------
# 3. CONTROL DE SESIÓN Y CARGA DE DATOS
# -----------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        st.markdown("<h2 style='text-align: center; color: #0f172a;'>🔐 Acceso al Sistema POS</h2>", unsafe_allow_html=True)
        clave_ingresada = st.text_input("Ingrese la Clave de Acceso", type="password")
        if st.button("Ingresar", use_container_width=True):
            if clave_ingresada == CLAVE_ACCESO:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Clave incorrecta")
    st.stop()

# Cargar inventarios y ventas
df_inv = cargar_csv_github("inventario.csv")
if df_inv.empty:
    df_inv = pd.DataFrame(columns=["CATEGORIA", "STOCK", "PRECIO", "STOCK_MINIMO"])

df_ventas = cargar_csv_github("ventas.csv")
if df_ventas.empty:
    df_ventas = pd.DataFrame(columns=[
        "ID_VENTA", "FECHA", "CLIENTE", "CEDULA", "CELULAR", "DIRECCION",
        "PRODUCTO", "CANTIDAD", "TOTAL", "ABONO", "SALDO",
        "ESTADO_PAGO", "ESTADO_ENTREGA", "OBSERVACION"
    ])

# -----------------------------------------------------------------------------
# 4. FUNCIONES AUXILIARES
# -----------------------------------------------------------------------------
def generar_link_whatsapp(numero, venta):
    """Genera enlace formateado para enviar comprobantes por WhatsApp."""
    numero_limpio = ''.join(filter(str.isdigit, str(numero)))
    
    # Formateo defensivo de importes numéricos
    total_val = float(venta.get('TOTAL', 0))
    abono_val = float(venta.get('ABONO', 0))
    saldo_val = float(venta.get('SALDO', 0))
    
    msg = (
        f"📋 *COMPROBANTE DE COMPRA - LOCAL MESITAS*\n\n"
        f"🆔 *Venta:* {venta.get('ID_VENTA', '')}\n"
        f"👤 *Cliente:* {venta.get('CLIENTE', '')}\n"
        f"🛋️ *Producto:* {venta.get('PRODUCTO', '')}\n"
        f"📦 *Cantidad:* {venta.get('CANTIDAD', '')}\n"
        f"💵 *Total:* ${total_val:.2f}\n"
        f"💳 *Abono:* ${abono_val:.2f}\n"
        f"📌 *Saldo pendiente:* ${saldo_val:.2f}\n"
        f"🚚 *Estado Entrega:* {venta.get('ESTADO_ENTREGA', '')}\n\n"
        f"¡Gracias por su compra!"
    )
    return f"https://wa.me/{numero_limpio}?text={urllib.parse.quote(msg)}"

# -----------------------------------------------------------------------------
# 5. ENCABEZADO Y MÉTRICAS CLAVE
# -----------------------------------------------------------------------------
top_c1, top_c2 = st.columns([5, 1])
with top_c1:
    st.markdown("""
    <div class="header-box">
        <h1 style='margin:0; font-size: 2.2rem;'>🛋️ LOCAL MESITAS</h1>
        <p style='margin-top:0.5rem; opacity:0.9;'>Sistema POS • Control de Inventarios y Ventas</p>
    </div>
    """, unsafe_allow_html=True)
with top_c2:
    if st.button("🔒 SALIR", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

m1, m2, m3, m4 = st.columns(4)
rec_total = df_ventas["ABONO"].sum() if not df_ventas.empty and "ABONO" in df_ventas.columns else 0.0
stk_total = df_inv["STOCK"].sum() if not df_inv.empty and "STOCK" in df_inv.columns else 0
n_ventas = len(df_ventas)
apartados = len(df_ventas[df_ventas["ESTADO_PAGO"] == "APARTADO"]) if not df_ventas.empty and "ESTADO_PAGO" in df_ventas.columns else 0

m1.markdown(f'<div class="metric-card"><div class="metric-title">💰 Recaudado</div><div class="metric-value">${rec_total:,.2f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><div class="metric-title">📦 Stock Total</div><div class="metric-value">{stk_total} uds</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><div class="metric-title">🧾 Ventas Totales</div><div class="metric-value">{n_ventas}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card"><div class="metric-title">⏳ Apartados Pendientes</div><div class="metric-value">{apartados}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. PESTAÑAS PRINCIPALES DE NAVEGACIÓN
# -----------------------------------------------------------------------------
tab_vender, tab_apartados, tab_inventario, tab_historial = st.tabs([
    "⚡ VENDER", "📦 APARTADOS", "🛠️ INVENTARIO", "📜 HISTORIAL Y GESTIÓN"
])

# -----------------------------------------------------------------------------
# PESTAÑA 1: VENDER
# -----------------------------------------------------------------------------
with tab_vender:
    st.subheader("🛒 Registrar Nueva Venta")
    
    if df_inv.empty:
        st.warning("⚠️ No hay productos registrados en el inventario.")
    else:
        with st.form("form_venta", clear_on_submit=True):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                cliente = st.text_input("Nombre del Cliente*")
                cedula = st.text_input("Cédula / RUC")
                celular = st.text_input("Celular (WhatsApp)*")
                direccion = st.text_area("Dirección de Entrega")

            with col_v2:
                prod_selec = st.selectbox("Producto*", df_inv["CATEGORIA"].tolist())
                # Obtener stock actual
                stock_actual = int(df_inv[df_inv["CATEGORIA"] == prod_selec]["STOCK"].values[0])
                precio_unitario = float(df_inv[df_inv["CATEGORIA"] == prod_selec]["PRECIO"].values[0])
                
                st.info(f"Stock disponible: {stock_actual} | Precio sugerido: ${precio_unitario:.2f}")
                
                cant = st.number_input("Cantidad*", min_value=1, max_value=max(1, stock_actual), value=1)
                total_calc = float(cant * precio_unitario)
                
                total_venta = st.number_input("Valor Total de Venta ($)*", min_value=0.0, value=total_calc)
                abono_inicial = st.number_input("Abono Inicial ($)*", min_value=0.0, max_value=total_venta, value=total_venta)
                
                estado_entrega = st.selectbox("Estado de Entrega", ["ENTREGADO", "PENDIENTE DE ENTREGA", "EN TRANSITO"])
                obs = st.text_input("Observaciones / Detalles adicionales")

            btn_registrar = st.form_submit_button("🚀 REGISTRAR VENTA", use_container_width=True)

        if btn_registrar:
            if not cliente or not celular:
                st.error("❌ Los campos Nombre de Cliente y Celular son obligatorios.")
            elif cant > stock_actual:
                st.error("❌ La cantidad solicitada supera el stock disponible.")
            else:
                saldo_pend = total_venta - abono_inicial
                estado_pago = "PAGADO" if saldo_pend <= 0 else "APARTADO"
                id_nueva_venta = f"V-{len(df_ventas) + 1:04d}"
                fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

                nueva_fila_v = {
                    "ID_VENTA": id_nueva_venta,
                    "FECHA": fecha_hoy,
                    "CLIENTE": cliente,
                    "CEDULA": cedula,
                    "CELULAR": celular,
                    "DIRECCION": direccion,
                    "PRODUCTO": prod_selec,
                    "CANTIDAD": cant,
                    "TOTAL": total_venta,
                    "ABONO": abono_inicial,
                    "SALDO": saldo_pend,
                    "ESTADO_PAGO": estado_pago,
                    "ESTADO_ENTREGA": estado_entrega,
                    "OBSERVACION": obs
                }

                # Descontar Inventario
                df_inv.loc[df_inv["CATEGORIA"] == prod_selec, "STOCK"] -= cant
                
                # Actualizar Ventas
                df_ventas = pd.concat([df_ventas, pd.DataFrame([nueva_fila_v])], ignore_index=True)

                # Persistir Cambios
                g1 = guardar_csv_github(df_inv, "inventario.csv", f"Venta {id_nueva_venta} - Descuento stock")
                g2 = guardar_csv_github(df_ventas, "ventas.csv", f"Registro venta {id_nueva_venta}")

                if g1 and g2:
                    st.success(f"✅ Venta {id_nueva_venta} registrada exitosamente.")
                    link_wa = generar_link_whatsapp(celular, nueva_fila_v)
                    st.markdown(f'<a href="{link_wa}" target="_blank"><button style="width:100%; padding:10px; background-color:#25D366; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">📲 Enviar Comprobante por WhatsApp</button></a>', unsafe_allow_html=True)
                else:
                    st.error("❌ Falló la sincronización con el servidor remoto.")

# -----------------------------------------------------------------------------
# PESTAÑA 2: APARTADOS PENDIENTES
# -----------------------------------------------------------------------------
with tab_apartados:
    st.subheader("📦 Ventas en Apartado / Saldos Pendientes")
    
    df_ap = df_ventas[df_ventas["ESTADO_PAGO"] == "APARTADO"] if not df_ventas.empty else pd.DataFrame()
    
    if df_ap.empty:
        st.info("🎉 No hay ventas registradas con saldo pendiente.")
    else:
        for idx, row in df_ap.iterrows():
            with st.expander(f"📌 Venta: {row['ID_VENTA']} - Cliente: {row['CLIENTE']} (Saldo: ${float(row['SALDO']):.2f})"):
                c_a1, c_a2 = st.columns(2)
                with c_a1:
                    st.write(f"**Producto:** {row['PRODUCTO']} x{row['CANTIDAD']}")
                    st.write(f"**Total Venta:** ${float(row['TOTAL']):.2f}")
                    st.write(f"**Abonado:** ${float(row['ABONO']):.2f}")
                    st.write(f"**Saldo Pendiente:** ${float(row['SALDO']):.2f}")
                with c_a2:
                    st.write(f"**Celular:** {row['CELULAR']}")
                    st.write(f"**Dirección:** {row['DIRECCION']}")
                    st.write(f"**Estado Entrega:** {row['ESTADO_ENTREGA']}")

                st.markdown("---")
                st.markdown("##### 💵 Registrar Nuevo Abono")
                
                with st.form(f"form_abono_{row['ID_VENTA']}"):
                    monto_abono = st.number_input("Monto a abonar ($)", min_value=0.01, max_value=float(row['SALDO']), value=float(row['SALDO']))
                    nuevo_estado_ent = st.selectbox("Actualizar Estado de Entrega", ["ENTREGADO", "PENDIENTE DE ENTREGA", "EN TRANSITO"], index=["ENTREGADO", "PENDIENTE DE ENTREGA", "EN TRANSITO"].index(row['ESTADO_ENTREGA']))
                    btn_abono = st.form_submit_button("✅ GUARDAR ABONO")

                if btn_abono:
                    idx_original = df_ventas[df_ventas["ID_VENTA"] == row["ID_VENTA"]].index[0]
                    nuevo_abono = float(df_ventas.loc[idx_original, "ABONO"]) + monto_abono
                    nuevo_saldo = float(df_ventas.loc[idx_original, "TOTAL"]) - nuevo_abono
                    
                    df_ventas.loc[idx_original, "ABONO"] = nuevo_abono
                    df_ventas.loc[idx_original, "SALDO"] = nuevo_saldo
                    df_ventas.loc[idx_original, "ESTADO_ENTREGA"] = nuevo_estado_ent
                    
                    if nuevo_saldo <= 0:
                        df_ventas.loc[idx_original, "ESTADO_PAGO"] = "PAGADO"

                    if guardar_csv_github(df_ventas, "ventas.csv", f"Abono registrado Venta {row['ID_VENTA']}"):
                        st.success("✅ Abono registrado correctamente.")
                        st.rerun()

# -----------------------------------------------------------------------------
# PESTAÑA 3: INVENTARIO
# -----------------------------------------------------------------------------
with tab_inventario:
    st.subheader("🛠️ Gestión y Reabastecimiento de Inventario")
    
    pwd_inv = st.text_input("🔑 Clave Administrador para Modificaciones", type="password", key="pwd_inv")
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown("##### ➕ Agregar Producto Nuevo")
        with st.form("form_nuevo_prod", clear_on_submit=True):
            n_prod = st.text_input("Nombre / Descripción del Producto")
            n_stk = st.number_input("Cantidad Inicial de Stock", min_value=0, value=1)
            n_prc = st.number_input("Precio Unitario ($)", min_value=0.0, value=10.0)
            n_min = st.number_input("Stock Mínimo Alerta", min_value=0, value=2)
            btn_n_prod = st.form_submit_button("➕ AGREGAR AL INVENTARIO")

        if btn_n_prod:
            if pwd_inv != CLAVE_ADMIN:
                st.error("❌ Clave de administrador incorrecta.")
            elif not n_prod:
                st.error("❌ Debe ingresar el nombre del producto.")
            else:
                nueva_item = {"CATEGORIA": n_prod.upper(), "STOCK": n_stk, "PRECIO": n_prc, "STOCK_MINIMO": n_min}
                df_inv = pd.concat([df_inv, pd.DataFrame([nueva_item])], ignore_index=True)
                if guardar_csv_github(df_inv, "inventario.csv", f"Nuevo producto: {n_prod}"):
                    st.success("✅ Producto agregado con éxito.")
                    st.rerun()

    with col_i2:
        st.markdown("##### 🔄 Actualizar Stock / Precio")
        if not df_inv.empty:
            with st.form("form_act_prod"):
                prod_act = st.selectbox("Seleccionar Producto", df_inv["CATEGORIA"].tolist())
                item_sel = df_inv[df_inv["CATEGORIA"] == prod_act].iloc[0]
                
                u_stk = st.number_input("Nuevo Stock", min_value=0, value=int(item_sel["STOCK"]))
                u_prc = st.number_input("Nuevo Precio ($)", min_value=0.0, value=float(item_sel["PRECIO"]))
                btn_u_prod = st.form_submit_button("🔄 ACTUALIZAR REGISTRO")

            if btn_u_prod:
                if pwd_inv != CLAVE_ADMIN:
                    st.error("❌ Clave de administrador incorrecta.")
                else:
                    df_inv.loc[df_inv["CATEGORIA"] == prod_act, "STOCK"] = u_stk
                    df_inv.loc[df_inv["CATEGORIA"] == prod_act, "PRECIO"] = u_prc
                    if guardar_csv_github(df_inv, "inventario.csv", f"Actualizado stock/precio: {prod_act}"):
                        st.success("✅ Inventario actualizado correctamente.")
                        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Tabla Completa de Inventario")
    st.dataframe(df_inv, use_container_width=True)

# -----------------------------------------------------------------------------
# PESTAÑA 4: HISTORIAL Y GESTIÓN
# -----------------------------------------------------------------------------
with tab_historial:
    st.subheader("📜 Registro Completo de Ventas y Eliminaciones")
    
    if df_ventas.empty:
        st.info("No hay registro de ventas cargadas.")
    else:
        st.dataframe(df_ventas, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🗑️ Zona de Eliminación (Solo Admin)")
        
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            pwd_del = st.text_input("🔑 Clave Administrador para Borrar", type="password", key="pwd_del")
        with col_h2:
            venta_borrar = st.selectbox("Seleccionar ID de Venta a Eliminar", df_ventas["ID_VENTA"].tolist())

        if st.button("🔴 ELIMINAR VENTA SELECCIONADA", use_container_width=True):
            if pwd_del != CLAVE_ADMIN:
                st.error("❌ Clave de administrador incorrecta.")
            else:
                df_ventas = df_ventas[df_ventas["ID_VENTA"] != venta_borrar]
                if guardar_csv_github(df_ventas, "ventas.csv", f"Eliminada venta {venta_borrar}"):
                    st.success(f"✅ Venta {venta_borrar} eliminada del registro.")
                    st.rerun()
