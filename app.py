import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# Configuración de página
st.set_page_config(page_title="Local Mesitas - POS", layout="wide", initial_sidebar_state="collapsed")

ADMIN_PASSWORD = "admin"

FILE_INV = "inventario_mesitas.csv"
FILE_VENTAS = "ventas_mesitas.csv"
FILE_APARTADOS = "apartados_mesitas.csv"

# Teléfonos de los dos dueños (+593 Ecuador)
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


# --- INICIALIZACIÓN DE DATOS ---
COLS_INV = ["CATEGORIA", "STOCK", "STOCK_MINIMO", "PRECIO", "COSTO", "MEDIDA", "CAMA_BASE", "COLCHON_BASE", "ES_TITULO", "PADRE"]
COLS_VENTAS = ["FECHA", "CATEGORIA", "CANTIDAD", "PRECIO_UNITARIO", "TOTAL", "ABONADO", "SALDO_PENDIENTE", "METODO_PAGO", "CLIENTE", "CEDULA", "TELEFONO", "CORREO", "DIRECCION", "ESTADO", "FOTO"]
COLS_APARTADOS = ["ID", "FECHA", "CLIENTE", "TELEFONO", "CATEGORIA", "TOTAL", "ABONADO", "SALDO", "ESTADO", "FECHA_ENTREGA"]

if "df_inv" not in st.session_state: st.session_state["df_inv"] = cargar_csv(FILE_INV, COLS_INV)
if "df_ventas" not in st.session_state: st.session_state["df_ventas"] = cargar_csv(FILE_VENTAS, COLS_VENTAS)
if "df_apartados" not in st.session_state: st.session_state["df_apartados"] = cargar_csv(FILE_APARTADOS, COLS_APARTADOS)
if "carrito" not in st.session_state: st.session_state["carrito"] = []
if "recibos_duenos" not in st.session_state: st.session_state["recibos_duenos"] = None
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
    descuento = st.number_input("🏷️ Descuento General ($)", min_value=0.0, max_value=float(subtotal), value=0.0)
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

        if st.form_submit_button("💰 REGISTRAR VENTA Y EMITIR A DUEÑOS", use_container_width=True, type="primary"):
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
            
            st.session_state["recibos_duenos"] = {
                nombre: generar_link_whatsapp(num, nueva_v_dict)
                for nombre, num in NUMEROS_DUENOS.items()
            }
            st.rerun()


if st.session_state["abrir_dialogo"]:
    abrir_modal_carrito()


# --- BANNER DE NOTIFICACIÓN A DUEÑOS ---
if st.session_state.get("recibos_duenos"):
    st.success("✅ Venta registrada con éxito.")
    st.markdown("### 📲 Enviar notificación por WhatsApp a los dueños:")
    
    links = st.session_state["recibos_duenos"]
    col_w1, col_w2, col_w3 = st.columns([2, 2, 1])
    
    with col_w1:
        st.link_button("📲 Notificar a Dueño 1", links["Dueño 1"], type="primary", use_container_width=True)
    with col_w2:
        st.link_button("📲 Notificar a Dueño 2", links["Dueño 2"], type="primary", use_container_width=True)
    with col_w3:
        if st.button("❌ Cerrar", use_container_width=True):
            st.session_state["recibos_duenos"] = None
            st.rerun()
    st.divider()


# --- NAVEGACIÓN PRINCIPAL ---
tab_venta, tab_apartados, tab_inv, tab_historial = st.tabs([
    "🛒 CATÁLOGO Y VENTA", "📑 APARTADOS", "📦 INVENTARIO", "📊 HISTORIAL"
])

# --- 1. CATÁLOGO Y VENTA ---
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

    # Filtros de categorías
    cats_padre = ["TODOS"] + sorted(list(df_inv[df_inv["ES_TITULO"].astype(str).str.upper().isin(["SI", "SÍ", "TRUE", "1"])]["CATEGORIA"].unique()))
    filtro_sel = st.selectbox("🔍 Filtrar por categoría:", cats_padre)

    subproductos = df_inv[df_inv["CATEGORIA"].apply(lambda x: producto_es_vendible(df_inv, x))]
    if filtro_sel != "TODOS":
        subproductos = subproductos[subproductos["CATEGORIA"].str.startswith(filtro_sel)]

    if subproductos.empty:
        st.info("No hay productos disponibles en esta categoría.")
    else:
        cols_per_row = 3
        cols = st.columns(cols_per_row)

        for idx, (_, row) in enumerate(subproductos.iterrows()):
            stk = int(row['STOCK'])
            icono = "🛏️" if "CAMA" in str(row['CATEGORIA']).upper() else "💤"

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

# --- 2. APARTADOS ---
with tab_apartados:
    st.title("📑 Gestión de Apartados / Reservas")
    
    with st.expander("➕ Registrar Nuevo Apartado", expanded=False):
        with st.form("form_nuevo_apartado"):
            prods_vend = df_inv[df_inv["CATEGORIA"].apply(lambda x: producto_es_vendible(df_inv, x))]["CATEGORIA"].tolist()
            p_ap = st.selectbox("Producto", prods_vend) if prods_vend else st.text_input("Producto")
            c_nom_ap = st.text_input("Nombre Cliente")
            c_tel_ap = st.text_input("Teléfono Cliente")
            tot_ap = st.number_input("Monto Total ($)", min_value=0.0, value=100.0)
            abo_ap = st.number_input("Abono Inicial ($)", min_value=0.0, value=20.0)
            f_ent = st.date_input("Fecha Estimada Entrega")
            
            if st.form_submit_button("Guardar Apartado"):
                nuevo_ap = {
                    "ID": f"AP-{len(st.session_state['df_apartados'])+1:03d}",
                    "FECHA": datetime.now().strftime("%Y-%m-%d"),
                    "CLIENTE": c_nom_ap,
                    "TELEFONO": c_tel_ap,
                    "CATEGORIA": p_ap,
                    "TOTAL": tot_ap,
                    "ABONADO": abo_ap,
                    "SALDO": max(0.0, tot_ap - abo_ap),
                    "ESTADO": "Pendiente",
                    "FECHA_ENTREGA": str(f_ent)
                }
                st.session_state["df_apartados"] = pd.concat([st.session_state["df_apartados"], pd.DataFrame([nuevo_ap])], ignore_index=True)
                guardar_csv(st.session_state["df_apartados"], FILE_APARTADOS)
                st.success("Apartado registrado con éxito.")
                st.rerun()

    st.dataframe(st.session_state["df_apartados"], use_container_width=True)

# --- 3. INVENTARIO & ADMINISTRACIÓN ---
with tab_inv:
    st.title("📦 Control de Inventario y Edición")
    
    pwd = st.text_input("🔒 Contraseña Admin para editar:", type="password")
    if pwd == ADMIN_PASSWORD:
        st.success("Modo Edición Activado")
        
        # Editor interactivo
        edited_df = st.data_editor(st.session_state["df_inv"], num_rows="dynamic", use_container_width=True)
        if st.button("💾 Guardar Cambios en Inventario"):
            st.session_state["df_inv"] = edited_df
            guardar_csv(edited_df, FILE_INV)
            st.success("¡Inventario actualizado correctamente!")
            st.rerun()
    else:
        if pwd != "":
            st.error("Contraseña incorrecta")
        st.dataframe(st.session_state["df_inv"], use_container_width=True)

# --- 4. HISTORIAL DE VENTAS ---
with tab_historial:
    st.title("📊 Historial de Ventas y Reportes")
    
    df_v = st.session_state["df_ventas"]
    if not df_v.empty:
        c1, c2 = st.columns(2)
        tot_ventas = pd.to_numeric(df_v["TOTAL"], errors="coerce").sum()
        c1.metric("💰 Ventas Totales", f"${tot_ventas:,.2f}")
        c2.metric("📦 Cantidad de Transacciones", len(df_v))
        
    st.dataframe(df_v, use_container_width=True)
