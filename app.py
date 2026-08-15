import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# Configuración de la aplicación
st.set_page_config(page_title="Local Mesitas - POS", layout="wide", initial_sidebar_state="collapsed")

ADMIN_PASSWORD = "admin"

FILE_INV = "inventario_mesitas.csv"
FILE_VENTAS = "ventas_mesitas.csv"
FILE_APARTADOS = "apartados_mesitas.csv"

# Teléfonos de los dos dueños (código de país Ecuador 593)
NUMEROS_DUENOS = {
    "Dueño 1": "593990847819",
    "Dueño 2": "593983576800"
}

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    .catalog-card {
        background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0;
        padding: 16px; margin-bottom: 20px;
    }
    .card-img-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px; height: 120px; display: flex;
        align-items: center; justify-content: center; font-size: 3rem;
    }
</style>
""", unsafe_allow_html=True)


# --- FUNCIONES BASE ---
def cargar_csv(filepath, columnas_defecto):
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            for col in columnas_defecto:
                if col not in df.columns:
                    df[col] = "NO" if col == "ES_TITULO" else ""
            return df
        except Exception:
            return pd.DataFrame(columns=columnas_defecto)
    else:
        df = pd.DataFrame(columns=columnas_defecto)
        df.to_csv(filepath, index=False)
        return df

def guardar_csv(df, filepath):
    df.to_csv(filepath, index=False)

def generar_link_whatsapp(numero, venta_dict):
    mensaje = f"""*NUEVA VENTA REGISTRADA - LOCAL MESITAS* 🧾
----------------------------------------
*Cliente:* {venta_dict['CLIENTE']}
*Cédula/RUC:* {venta_dict['CEDULA']}
*Teléfono:* {venta_dict['TELEFONO']}
*Dirección:* {venta_dict['DIRECCION']}
----------------------------------------
*Detalle:* {venta_dict['CATEGORIA']}
*Cant. Total:* {venta_dict['CANTIDAD']}
*Método Pago:* {venta_dict['METODO_PAGO']}
*Total Cobrado:* ${venta_dict['TOTAL']:.2f}
----------------------------------------
¡Venta registrada con éxito! 🚀"""
    return f"https://wa.me/{numero}?text={urllib.parse.quote(mensaje)}"

def producto_es_vendible(df_inv, categoria):
    fila = df_inv[df_inv["CATEGORIA"] == categoria]
    if fila.empty: return False
    row = fila.iloc[0]
    es_titulo = str(row.get("ES_TITULO", "NO")).strip().upper() in ["SI", "SÍ", "TRUE", "1"]
    cama_base = str(row.get("CAMA_BASE", "NO")).strip().upper() == "SI"
    colchon_base = str(row.get("COLCHON_BASE", "NO")).strip().upper() == "SI"
    return not (es_titulo or cama_base or colchon_base)


# --- INICIALIZACIÓN ---
COLS_INV = ["CATEGORIA", "STOCK", "STOCK_MINIMO", "PRECIO", "COSTO", "MEDIDA", "CAMA_BASE", "COLCHON_BASE", "ES_TITULO", "PADRE"]
COLS_VENTAS = ["FECHA", "CATEGORIA", "CANTIDAD", "PRECIO_UNITARIO", "TOTAL", "ABONADO", "SALDO_PENDIENTE", "METODO_PAGO", "CLIENTE", "CEDULA", "TELEFONO", "CORREO", "DIRECCION", "ESTADO", "FOTO"]
COLS_APARTADOS = ["ID", "FECHA", "CLIENTE", "TELEFONO", "CATEGORIA", "TOTAL", "ABONADO", "SALDO", "ESTADO", "FECHA_ENTREGA"]

if "df_inv" not in st.session_state: st.session_state["df_inv"] = cargar_csv(FILE_INV, COLS_INV)
if "df_ventas" not in st.session_state: st.session_state["df_ventas"] = cargar_csv(FILE_VENTAS, COLS_VENTAS)
if "df_apartados" not in st.session_state: st.session_state["df_apartados"] = cargar_csv(FILE_APARTADOS, COLS_APARTADOS)
if "carrito" not in st.session_state: st.session_state["carrito"] = []
if "links_auto_open" not in st.session_state: st.session_state["links_auto_open"] = None
if "abrir_dialogo" not in st.session_state: st.session_state["abrir_dialogo"] = False
if "filtro_categoria" not in st.session_state: st.session_state["filtro_categoria"] = "TODOS"
if "admin_autenticado" not in st.session_state: st.session_state["admin_autenticado"] = False

df_inv = st.session_state["df_inv"]


# --- MODAL CHECKOUT PARA EL VENDEDOR ---
@st.dialog("🛒 Checkout - Registrar Venta")
def abrir_modal_carrito():
    if not st.session_state["carrito"]:
        st.info("El carrito de compras está vacío.")
        if st.button("⬅️ Volver al catálogo", use_container_width=True):
            st.session_state["abrir_dialogo"] = False
            st.rerun()
        return

    subtotal = 0.0
    st.write("### Productos a Cobrar")
    
    for i, item in enumerate(list(st.session_state["carrito"])):
        tot_item = item["cantidad"] * item["precio"]
        subtotal += tot_item
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        c1.write(f"**{item['producto']}**")
        c2.write(f"x{item['cantidad']}")
        c3.write(f"${tot_item:,.2f}")
        if c4.button("🗑️", key=f"del_mod_{i}"):
            st.session_state["carrito"].pop(i)
            st.rerun()

    st.divider()
    descuento = st.number_input("🏷️ Descuento ($)", min_value=0.0, max_value=float(subtotal), value=0.0)
    total_final = max(0.0, subtotal - descuento)
    
    st.markdown(f"### **Total Final: ${total_final:,.2f}**")
    st.divider()

    sin_datos = st.checkbox("⚡ Consumidor Final (Sin datos)", value=False)

    with st.form("form_modal_checkout"):
        m_pago = st.selectbox("💳 Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
        
        if sin_datos:
            c_nom, c_ced, c_tel, c_dir = "CONSUMIDOR FINAL", "9999999999999", "S/N", "S/N"
        else:
            c_nom = st.text_input("👤 Nombre Cliente")
            c_ced = st.text_input("🆔 Cédula/RUC")
            c_tel = st.text_input("📞 Teléfono Cliente")
            c_dir = st.text_input("📍 Dirección Entrega")

        if st.form_submit_button("💰 REGISTRAR VENTA Y NOTIFICAR A DUEÑOS", use_container_width=True, type="primary"):
            df_inv_local = st.session_state["df_inv"]
            for item in st.session_state["carrito"]:
                df_inv_local.loc[df_inv_local["CATEGORIA"] == item["producto"], "STOCK"] -= item["cantidad"]
            
            guardar_csv(df_inv_local, FILE_INV)
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
                "CLIENTE": c_nom if c_nom else "CONSUMIDOR FINAL",
                "CEDULA": c_ced if c_ced else "9999999999999",
                "TELEFONO": c_tel if c_tel else "S/N",
                "CORREO": "",
                "DIRECCION": c_dir if c_dir else "S/N",
                "ESTADO": "Pagado y Entregado",
                "FOTO": "Sin foto"
            }

            df_v_act = pd.concat([st.session_state["df_ventas"], pd.DataFrame([nueva_v_dict])], ignore_index=True)
            guardar_csv(df_v_act, FILE_VENTAS)
            st.session_state["df_ventas"] = df_v_act
            st.session_state["carrito"] = []
            st.session_state["abrir_dialogo"] = False
            
            # Generar enlaces automáticos para ambos dueños
            st.session_state["links_auto_open"] = [
                generar_link_whatsapp(num, nueva_v_dict) for num in NUMEROS_DUENOS.values()
            ]
            st.rerun()


if st.session_state["abrir_dialogo"]:
    abrir_modal_carrito()


# --- EJECUCIÓN AUTOMÁTICA HACIA AMBOS DUEÑOS ---
if st.session_state.get("links_auto_open"):
    links = st.session_state["links_auto_open"]
    st.success("✅ Venta registrada. Enviando notificación por WhatsApp a ambos dueños...")
    
    # Inyección JS para abrir automáticamente ambas pestañas
    js_code = f"""
        <script>
            window.open('{links[0]}', '_blank');
            window.open('{links[1]}', '_blank');
        </script>
    """
    components.html(js_code, height=0, width=0)
    
    # Respaldo de botones directos
    c1, c2, c3 = st.columns([2, 2, 1])
    c1.link_button("📲 Notificar a Dueño 1", links[0], use_container_width=True, type="primary")
    c2.link_button("📲 Notificar a Dueño 2", links[1], use_container_width=True, type="primary")
    if c3.button("❌ Cerrar", use_container_width=True):
        st.session_state["links_auto_open"] = None
        st.rerun()
    st.divider()


# --- INTERFAZ CATÁLOGO DE VENTA ---
tab_venta, tab_apartados, tab_inv, tab_historial = st.tabs([
    "🛒 CATÁLOGO Y VENTA", "📑 APARTADOS", "📦 INVENTARIO", "📊 HISTORIAL"
])

with tab_venta:
    col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 1, 1])
    col_hdr1.title("✨ Punto de Venta")
    
    cant_items = sum([it['cantidad'] for it in st.session_state["carrito"]])
    
    if col_hdr2.button(f"🛒 Ver Carrito ({cant_items})", type="primary", use_container_width=True):
        st.session_state["abrir_dialogo"] = True
        st.rerun()

    if col_hdr3.button("🗑️ Vaciar Carrito", use_container_width=True, disabled=(cant_items == 0)):
        st.session_state["carrito"] = []
        st.session_state["abrir_dialogo"] = False
        st.rerun()

    subproductos = df_inv[df_inv["CATEGORIA"].apply(lambda x: producto_es_vendible(df_inv, x))]

    cols_per_row = 3
    cols = st.columns(cols_per_row)

    for idx, (_, row) in enumerate(subproductos.iterrows()):
        stk = int(row['STOCK'])
        icono = "🛏️" if "CAMA" in row['CATEGORIA'].upper() else "💤"

        with cols[idx % cols_per_row]:
            st.markdown(f"""
            <div class="catalog-card">
                <div class="card-img-header">
                    <span>{icono}</span>
                </div>
                <h4>{row['CATEGORIA']}</h4>
                <h3>${row['PRECIO']:,.2f}</h3>
            </div>
            """, unsafe_allow_html=True)

            if stk > 0:
                if st.button(f"🛒 Agregar ({stk} dispon.)", key=f"add_{idx}", use_container_width=True):
                    st.session_state["carrito"].append({"producto": row['CATEGORIA'], "cantidad": 1, "precio": float(row['PRECIO'])})
                    st.session_state["abrir_dialogo"] = True
                    st.rerun()
            else:
                st.button("🚫 Sin Stock", key=f"dis_{idx}", disabled=True, use_container_width=True)
