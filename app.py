import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuración de diseño de la página
st.set_page_config(
    page_title="CAMAS - Control de Inventario",
    page_icon="🛏️",
    layout="wide"
)

# Estilos CSS personalizados para mejorar la apariencia
st.markdown("""
    <style>
    .main { padding: 1rem 2rem; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #2e7d32; color: white; font-weight: bold; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #1e88e5; }
    </style>
""", unsafe_allow_html=True)

st.title("🛏️ Sistema de Inventario y Ventas - CAMAS")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# Inicializar columnas si la hoja está vacía
if df.empty or len(df.columns) < 4:
    df = pd.DataFrame(columns=["NOMBRE", "CATEGORIA", "PRECIO", "STOCK"])

# Resumen de Métricas (Tarjetas de información rápida)
col_m1, col_m2, col_m3 = st.columns(3)
total_productos = len(df)
total_stock = df["STOCK"].sum() if "STOCK" in df.columns and not df.empty else 0
col_m1.metric("📦 Productos Distintos", total_productos)
col_m2.metric("📊 Stock Total Disponible", f"{total_stock} unidades")
col_m3.metric("Status", "🟢 En línea")

st.markdown("---")

# Organización por Pestañas
tab_inv, tab_entrada, tab_venta = st.tabs(["📋 Inventario Actual", "📥 Registrar Entrada (Llegada)", "🛒 Registrar Venta (Salida)"])

# ---------------------------------------------------------
# PESTAÑA 1: INVENTARIO ACTUAL
# ---------------------------------------------------------
with tab_inv:
    st.subheader("📦 Productos Registrados")
    if df.empty:
        st.info("Aún no hay productos ingresados.")
    else:
        st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# PESTAÑA 2: ENTRADA DE MERCANCÍA (Nuevos o Aumento de Stock)
# ---------------------------------------------------------
with tab_entrada:
    st.subheader("📥 Registrar Entrada de Mercancía")
    
    opcion_entrada = st.radio("¿Qué deseas hacer?", ["Agregar producto nuevo", "Aumentar stock de producto existente"], horizontal=True)
    
    if opcion_entrada == "Agregar producto nuevo":
        with st.form(key="form_nuevo_prod"):
            nombre = st.text_input("Nombre del Producto")
            categoria = st.selectbox("Categoría", ["Camas", "Colchones", "Almohadas", "Muebles", "Accesorios", "Otros"])
            precio = st.number_input("Precio ($)", min_value=0.0, step=0.50)
            stock = st.number_input("Cantidad Inicial", min_value=1, step=1)
            btn_guardar = st.form_submit_button("➕ Guardar Producto Nuevo")
            
            if btn_guardar:
                if nombre.strip() == "":
                    st.warning("Escribe el nombre del producto.")
                else:
                    nuevo = pd.DataFrame([{"NOMBRE": nombre, "CATEGORIA": categoria, "PRECIO": precio, "STOCK": stock}])
                    df_actualizado = pd.concat([df, nuevo], ignore_index=True)
                    conn.update(data=df_actualizado)
                    st.success(f"¡Producto '{nombre}' agregado exitosamente!")
                    st.rerun()

    else:
        if df.empty:
            st.warning("No hay productos en el inventario para actualizar.")
        else:
            with st.form(key="form_aumentar_stock"):
                prod_selec = st.selectbox("Selecciona el producto", df["NOMBRE"].tolist())
                cant_sumar = st.number_input("Cantidad que llega", min_value=1, step=1)
                btn_aumentar = st.form_submit_button("📥 Sumar al Stock")
                
                if btn_aumentar:
                    df.loc[df["NOMBRE"] == prod_selec, "STOCK"] += cant_sumar
                    conn.update(data=df)
                    st.success(f"¡Se agregaron {cant_sumar} unidades a '{prod_selec}'!")
                    st.rerun()

# ---------------------------------------------------------
# PESTAÑA 3: REGISTRAR VENTA (Descontar del Stock)
# ---------------------------------------------------------
with tab_venta:
    st.subheader("🛒 Registrar Salida por Venta")
    if df.empty:
        st.warning("No hay productos en inventario.")
    else:
        with st.form(key="form_venta"):
            prod_vender = st.selectbox("Producto Vendido", df["NOMBRE"].tolist())
            cant_vender = st.number_input("Cantidad Vendida", min_value=1, step=1)
            btn_vender = st.form_submit_button("🛍️ Confirmar Venta")
            
            if btn_vender:
                stock_actual = df.loc[df["NOMBRE"] == prod_vender, "STOCK"].values[0]
                if cant_vender > stock_actual:
                    st.error(f"No hay suficiente stock. Stock disponible: {stock_actual}")
                else:
                    df.loc[df["NOMBRE"] == prod_vender, "STOCK"] -= cant_vender
                    conn.update(data=df)
                    st.success(f"¡Venta realizada! Se descontaron {cant_vender} unidades de '{prod_vender}'.")
                    st.rerun()
