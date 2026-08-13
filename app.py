import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuración de la página
st.set_page_config(
    page_title="CAMAS - Control de Inventario",
    page_icon="🛏️",
    layout="wide"
)

# Estilos CSS
st.markdown("""
    <style>
    .main { padding: 1rem 2rem; }
    .stButton>button { width: 100%; border-radius: 8px; height: 2.8em; font-weight: bold; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #1e88e5; }
    </style>
""", unsafe_allow_html=True)

st.title("🛏️ Sistema de Inventario y Ventas - CAMAS")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# Estructura básica si está vacío
if df.empty or len(df.columns) < 4:
    df = pd.DataFrame(columns=["NOMBRE", "CATEGORIA", "PRECIO", "STOCK"])

# Métricas superiores
col1, col2, col3 = st.columns(3)
col1.metric("📦 Productos Registrados", len(df))
col2.metric("📊 Stock Total", f"{df['STOCK'].sum() if 'STOCK' in df.columns and not df.empty else 0} unidades")
col3.metric("Estado", "🟢 Sistema Conectado")

st.markdown("---")

# Función general para renderizar la sección de cada categoría
def mostrar_seccion_categoria(nombre_cat, icono):
    st.subheader(f"{icono} Gestión de {nombre_cat}")
    
    # Filtrar datos por categoría
    df_cat = df[df["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()] if not df.empty else pd.DataFrame()
    
    # 1. Mostrar Tabla de la Categoría
    st.markdown("##### 📦 Inventario Actual")
    if df_cat.empty:
        st.info(f"No hay productos registrados en {nombre_cat}.")
    else:
        st.dataframe(df_cat, use_container_width=True)
        
    st.markdown("---")
    
    # 2. Formularios de Entrada y Salida para esta Categoría
    col_in, col_out = st.columns(2)
    
    # --- REGISTRAR ENTRADA (LLEGADA) ---
    with col_in:
        st.markdown(f"##### 📥 Entrada de {nombre_cat}")
        tipo_e = st.radio(f"Acción para {nombre_cat}", ["Crear nuevo producto", "Aumentar stock existente"], key=f"radio_{nombre_cat}", horizontal=True)
        
        if tipo_e == "Crear nuevo producto":
            with st.form(key=f"form_nuevo_{nombre_cat}"):
                nom = st.text_input("Nombre del Producto")
                prec = st.number_input("Precio ($)", min_value=0.0, step=0.50)
                stk = st.number_input("Cantidad Inicial", min_value=1, step=1)
                if st.form_submit_button(f"➕ Guardar en {nombre_cat}"):
                    if nom.strip() == "":
                        st.warning("Ingresa el nombre del producto.")
                    else:
                        nuevo = pd.DataFrame([{"NOMBRE": nom, "CATEGORIA": nombre_cat, "PRECIO": prec, "STOCK": stk}])
                        df_act = pd.concat([df, nuevo], ignore_index=True)
                        conn.update(data=df_act)
                        st.success(f"¡'{nom}' agregado a {nombre_cat}!")
                        st.rerun()
        else:
            if df_cat.empty:
                st.caption(f"No hay productos en {nombre_cat} para sumar stock.")
            else:
                with st.form(key=f"form_sumar_{nombre_cat}"):
                    prod_sel = st.selectbox("Selecciona Producto", df_cat["NOMBRE"].tolist())
                    cant = st.number_input("Cantidad que llega", min_value=1, step=1)
                    if st.form_submit_button("📥 Registrar Llegada"):
                        df.loc[df["NOMBRE"] == prod_sel, "STOCK"] += cant
                        conn.update(data=df)
                        st.success(f"¡Se sumaron {cant} unidades a '{prod_sel}'!")
                        st.rerun()

    # --- REGISTRAR VENTA (SALIDA) ---
    with col_out:
        st.markdown(f"##### 🛒 Venta de {nombre_cat}")
        if df_cat.empty:
            st.caption(f"No hay productos disponibles para vender en {nombre_cat}.")
        else:
            with st.form(key=f"form_venta_{nombre_cat}"):
                prod_v = st.selectbox("Producto a Vender", df_cat["NOMBRE"].tolist())
                cant_v = st.number_input("Cantidad Vendida", min_value=1, step=1)
                if st.form_submit_button("🛍️ Confirmar Venta"):
                    stk_actual = df.loc[df["NOMBRE"] == prod_v, "STOCK"].values[0]
                    if cant_v > stk_actual:
                        st.error(f"Stock insuficiente. Quedan: {stk_actual}")
                    else:
                        df.loc[df["NOMBRE"] == prod_v, "STOCK"] -= cant_v
                        conn.update(data=df)
                        st.success(f"¡Venta registrada! Se descontaron {cant_v} unidades de '{prod_v}'.")
                        st.rerun()

# ---------------------------------------------------------
# PESTAÑAS PRINCIPALES
# ---------------------------------------------------------
tab_camas, tab_colchones, tab_armarios, tab_pajaritas, tab_todos = st.tabs([
    "🛏️ Camas", "💤 Colchones", "🚪 Armarios", "🎀 Pajaritas", "🌐 Todos los Productos"
])

with tab_camas:
    mostrar_seccion_categoria("Camas", "🛏️")

with tab_colchones:
    mostrar_seccion_categoria("Colchones", "💤")

with tab_armarios:
    mostrar_seccion_categoria("Armarios", "🚪")

with tab_pajaritas:
    mostrar_seccion_categoria("Pajaritas", "🎀")

with tab_todos:
    st.subheader("🌐 Inventario Global")
    if df.empty:
        st.info("No hay productos registrados en el sistema.")
    else:
        st.dataframe(df, use_container_width=True)
