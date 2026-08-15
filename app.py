from datetime import datetime
import os
import pandas as pd
import streamlit as st

# ==============================================================================
# LOCAL MESITAS - SISTEMA POS (VERSIÓN OPTIMIZADA PARA MÓVIL)
# ==============================================================================

st.set_page_config(
    page_title="Local Mesitas - Sistema POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------------------------
# ESTILOS CSS PERSONALIZADOS
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    div.stButton > button {
        width: 100% !important;
        height: 3.2rem !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0px 4px 10px rgba(37, 99, 235, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
        margin-bottom: 8px !important;
    }
    div.stButton > button:hover, div.stButton > button:active {
        transform: scale(0.98);
        background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.2) !important;
    }
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        font-size: 1rem !important;
        padding: 10px !important;
        border-radius: 10px !important;
    }
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        padding: 12px 16px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# CONFIGURACIÓN Y CONSTANTES
# ------------------------------------------------------------------------------
CLAVE_ADMIN = "1998"
FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"

COLUMNAS_INV = ["id", "nombre", "categoria", "precio", "stock"]
COLUMNAS_VENTAS = ["fecha", "producto", "cantidad", "total", "metodo_pago"]

# Funciones de carga y guardado
def cargar_inventario():
    if os.path.exists(FILE_INV):
        try:
            df = pd.read_csv(FILE_INV)
            if not df.empty and all(col in df.columns for col in COLUMNAS_INV):
                return df
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNAS_INV)

def guardar_inventario(df):
    df.to_csv(FILE_INV, index=False)

def cargar_ventas():
    if os.path.exists(FILE_VENTAS):
        try:
            df = pd.read_csv(FILE_VENTAS)
            if not df.empty and all(col in df.columns for col in COLUMNAS_VENTAS):
                return df
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNAS_VENTAS)

def guardar_ventas(df):
    df.to_csv(FILE_VENTAS, index=False)

# Carga inicial
df_inv = cargar_inventario()
df_ventas = cargar_ventas()

# ------------------------------------------------------------------------------
# NAVEGACIÓN PRINCIPAL
# ------------------------------------------------------------------------------
st.title("🛏️ Local Mesitas - POS Mobile")

tab_pos, tab_inv, tab_ventas, tab_admin = st.tabs(
    ["🛒 Punto de Venta", "📦 Productos", "📊 Ventas", "🔒 Admin"]
)

# ------------------------------------------------------------------------------
# 1. PUNTO DE VENTA (POS)
# ------------------------------------------------------------------------------
with tab_pos:
    st.subheader("Registrar Venta")
    
    if df_inv.empty or df_inv["nombre"].dropna().empty:
        st.warning("No hay productos registrados en el inventario. Agrega productos desde la pestaña Admin.")
    else:
        lista_productos = df_inv["nombre"].tolist()
        producto_sel = st.selectbox("Seleccionar Producto:", lista_productos)
        
        prod_data = df_inv[df_inv["nombre"] == producto_sel].iloc[0]
        stock_disp = int(prod_data["stock"])
        precio_unit = float(prod_data["precio"])
        
        st.info(f"**Precio:** ${precio_unit:.2f} | **Stock disponible:** {stock_disp}")
        
        if stock_disp <= 0:
            st.error("❌ Producto agotado. No se pueden realizar ventas de este ítem.")
        else:
            cantidad = st.number_input(
                "Cantidad:", 
                min_value=1, 
                max_value=stock_disp, 
                value=1, 
                step=1
            )
            metodo_pago = st.selectbox("Método de Pago:", ["Efectivo", "Transferencia", "Tarjeta"])
            
            total = cantidad * precio_unit
            st.markdown(f"### **Total a Pagar:** :green[${total:.2f}]")
            
            if st.button("🚀 REALIZAR VENTA"):
                # Actualizar stock
                df_inv.loc[df_inv["nombre"] == producto_sel, "stock"] -= cantidad
                guardar_inventario(df_inv)
                
                # Registrar venta
                nueva_venta = pd.DataFrame([{
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "producto": producto_sel,
                    "cantidad": cantidad,
                    "total": total,
                    "metodo_pago": metodo_pago
                }])
                df_ventas = pd.concat([df_ventas, nueva_venta], ignore_index=True)
                guardar_ventas(df_ventas)
                
                st.success("¡Venta registrada con éxito!")
                st.rerun()

# ------------------------------------------------------------------------------
# 2. INVENTARIO
# ------------------------------------------------------------------------------
with tab_inv:
    st.subheader("Inventario de Productos")
    st.dataframe(df_inv, use_container_width=True)

# ------------------------------------------------------------------------------
# 3. HISTORIAL DE VENTAS
# ------------------------------------------------------------------------------
with tab_ventas:
    st.subheader("Historial de Ventas")
    st.dataframe(df_ventas, use_container_width=True)

# ------------------------------------------------------------------------------
# 4. ADMINISTRACIÓN
# ------------------------------------------------------------------------------
with tab_admin:
    st.subheader("Panel de Administración")
    clave_input = st.text_input("Ingrese la clave de Administrador:", type="password")
    
    if clave_input == CLAVE_ADMIN:
        st.success("Acceso concedido como Administrador.")
        st.markdown("---")
        st.markdown("### Agregar Nuevo Producto")
        
        nuevo_id = st.text_input("ID / Código del Producto:")
        nuevo_nombre = st.text_input("Nombre del Producto:")
        nueva_cat = st.text_input("Categoría:")
        nuevo_precio = st.number_input("Precio ($):", min_value=0.0, format="%.2f")
        nuevo_stock = st.number_input("Stock Inicial:", min_value=0, step=1)
        
        if st.button("➕ AGREGAR PRODUCTO"):
            if nuevo_nombre.strip() and nuevo_id.strip():
                nuevo_prod = pd.DataFrame([{
                    "id": nuevo_id.strip(),
                    "nombre": nuevo_nombre.strip(),
                    "categoria": nueva_cat.strip(),
                    "precio": nuevo_precio,
                    "stock": int(nuevo_stock)
                }])
                df_inv = pd.concat([df_inv, nuevo_prod], ignore_index=True)
                guardar_inventario(df_inv)
                st.success(f"Producto '{nuevo_nombre}' agregado correctamente.")
                st.rerun()
            else:
                st.error("Por favor completa al menos el ID y Nombre del producto.")
    elif clave_input != "":
        st.error("Clave incorrecta. Intente nuevamente.")
