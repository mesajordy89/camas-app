from datetime import datetime
from email.message import EmailMessage
import mimetypes
import os
import smtplib
import textwrap
import urllib.parse

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
# ESTILOS CSS PERSONALIZADOS PARA CELULAR Y BOTONES LLAMATIVOS
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Estilos generales */
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Botones principales para pantallas táctiles */
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

    /* Campos de entrada optimizados para táctil */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        font-size: 1rem !important;
        padding: 10px !important;
        border-radius: 10px !important;
    }

    /* Pestañas más grandes para celular */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        padding: 12px 16px !important;
    }

    /* Tarjetas de productos/resumen */
    .product-card {
        background-color: #f8fafc;
        border-left: 5px solid #2563eb;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# CONFIGURACIÓN Y CONSTANTES
# ------------------------------------------------------------------------------
CLAVE_ADMIN = "1998"  # Clave de administrador actualizada
FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"

# Funciones de carga y guardado de datos
def cargar_inventario():
    if os.path.exists(FILE_INV):
        try:
            return pd.read_csv(FILE_INV)
        except Exception:
            pass
    return pd.DataFrame(
        columns=["id", "nombre", "categoria", "precio", "stock"]
    )

def guardar_inventario(df):
    df.to_csv(FILE_INV, index=False)

def cargar_ventas():
    if os.path.exists(FILE_VENTAS):
        try:
            return pd.read_csv(FILE_VENTAS)
        except Exception:
            pass
    return pd.DataFrame(
        columns=["fecha", "producto", "cantidad", "total", "metodo_pago"]
    )

def guardar_ventas(df):
    df.to_csv(FILE_VENTAS, index=False)

# Carga de datos iniciales
df_inv = cargar_inventario()
df_ventas = cargar_ventas()

# ------------------------------------------------------------------------------
# NAVEGACIÓN Y MENÚ PRINCIPAL
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
    
    if df_inv.empty:
        st.warning("No hay productos registrados en el inventario.")
    else:
        producto_sel = st.selectbox(
            "Seleccionar Producto:", df_inv["nombre"].tolist()
        )
        
        prod_data = df_inv[df_inv["nombre"] == producto_sel].iloc[0]
        
        st.info(f"**Precio:** ${prod_data['precio']:.2f} | **Stock disponible:** {prod_data['stock']}")
        
        cantidad = st.number_input("Cantidad:", min_value=1, max_value=int(prod_data['stock']) if prod_data['stock'] > 0 else 1, value=1)
        metodo_pago = st.selectbox("Método de Pago:", ["Efectivo", "Transferencia", "Tarjeta"])
        
        total = cantidad * prod_data["precio"]
        st.markdown(f"### **Total a Pagar:** :green[${total:.2f}]")
        
        if st.button("🚀 REALIZAR VENTA"):
            if prod_data["stock"] < cantidad:
                st.error("¡Stock insuficiente!")
            else:
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

# ------------------------------------------------------------------------------
# 2. INVENTARIO / PRODUCTOS
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
# 4. MÓDULO DE ADMINISTRACIÓN
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
            if nuevo_nombre and nuevo_id:
                nuevo_prod = pd.DataFrame([{
                    "id": nuevo_id,
                    "nombre": nuevo_nombre,
                    "categoria": nueva_cat,
                    "precio": nuevo_precio,
                    "stock": nuevo_stock
                }])
                df_inv = pd.concat([df_inv, nuevo_prod], ignore_index=True)
                guardar_inventario(df_inv)
                st.success(f"Producto '{nuevo_nombre}' agregado correctamente.")
            else:
                st.error("Por favor completa al menos el ID y Nombre del producto.")
    elif clave_input != "":
        st.error("Clave incorrecta. Intente nuevamente.")
