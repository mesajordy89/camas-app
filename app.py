import streamlit as st
from datetime import datetime
import urllib.parse

# Configuración de la página
st.set_page_config(page_title="Local Mesitas - Sistema POS", layout="wide")

# 1. Inicializar el inventario en la sesión si no existe
if "inventario" not in st.session_state:
    st.session_state.inventario = {
        "Camas": {"stock": 10, "precio": 150.00},
        "Colchones": {"stock": 93, "precio": 180.00},
        "Armarios": {"stock": 0, "precio": 250.00},
        "Pajaritas": {"stock": 0, "precio": 15.00}
    }

# Menú principal de navegación
menu = st.sidebar.radio("Navegación", ["Venta Directa", "Inventario", "Apartados y Abonos", "Historial y Caja"])

# --- SECCIÓN: INVENTARIO ---
if menu == "Inventario":
    st.header("📦 Gestión de Inventario")
    
    st.subheader("Productos Actuales")
    for producto, datos in st.session_state.inventario.items():
        st.write(f"**{producto}** — Stock: **{datos['stock']} ud** — Precio: **${datos['precio']:.2f}**")

    st.markdown("---")
    st.subheader("Agregar Nuevo Producto o Categoría")
    
    with st.form("nuevo_producto_form"):
        nuevo_nombre = st.text_input("Nombre del Producto / Categoría")
        stock_inicial = st.number_input("Stock Inicial", min_value=0, value=10)
        precio_inicial = st.number_input("Precio Unitario ($)", min_value=0.0, value=50.00)
        
        submitted = st.form_submit_button("Guardar en el Inventario")
        if submitted and nuevo_nombre:
            if nuevo_nombre in st.session_state.inventario:
                st.warning("¡Este producto ya existe en el inventario!")
            else:
                st.session_state.inventario[nuevo_nombre] = {
                    "stock": stock_inicial,
                    "precio": precio_inicial
                }
                st.success(f"¡'{nuevo_nombre}' agregado con éxito!")
                st.rerun()

# --- SECCIÓN: VENTA DIRECTA ---
elif menu == "Venta Directa":
    st.header("⚡ Venta Rápida (Pago Total e Inmediato)")
    
    # Mostrar tarjetas rápidas de inventario superior
    cols = st.columns(len(st.session_state.inventario))
    for i, (prod, info) in enumerate(st.session_state.inventario.items()):
        with cols[i]:
            st.metric(label=prod, value=f"{info['stock']} ud", delta=f"${info['precio']:.2f}")

    st.markdown("---")
    
    # Selector basado en el inventario dinámico
    producto_seleccionado = st.selectbox("Selecciona el Producto", list(st.session_state.inventario.keys()))
    info_prod = st.session_state.inventario[producto_seleccionado]
    
    st.write(f"Precio unitario: **${info_prod['precio']:.2f}** | Stock disponible: **{info_prod['stock']} ud**")
    
    col1, col2 = st.columns(2)
    with col1:
        cantidad = st.number_input("Cantidad", min_value=1, max_value=max(1, info_prod['stock']), value=1)
        metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
    with col2:
        descuento = st.number_input("Descuento ($)", min_value=0.0, value=0.0)
        nombre_cliente = st.text_input("Nombre del Cliente", value="Cliente General")

    cedula = st.text_input("Cédula / RUC", value="S/N")
    telefono = st.text_input("Teléfono del cliente (Opcional)")
    direccion = st.text_area("Dirección de entrega (Opcional)")

    total_pagar = (info_prod['precio'] * cantidad) - descuento
    st.info(f"Total a Pagar: **${max(0.0, total_pagar):.2f}**")

    if st.button("Registrar Venta"):
        if info_prod['stock'] < cantidad:
            st.error("No hay suficiente stock disponible para esta venta.")
        else:
            # Descontar stock
            st.session_state.inventario[producto_seleccionado]['stock'] -= cantidad
            st.success(f"¡Venta registrada con éxito!")
            
            # Generar enlace de WhatsApp opcional
            mensaje = f"*NUEVA VENTA REGISTRADA*\n\n*Cliente*: {nombre_cliente}\n*Producto*: {cantidad}x {producto_seleccionado}\n*Total*: ${total_pagar:.2f}\n*Pago*: {metodo_pago}"
            whatsapp_url = f"https://api.whatsapp.com/send?phone=593990847819&text={urllib.parse.quote(mensaje)}"
            st.markdown(f"[Enviar comprobante por WhatsApp]({whatsapp_url})")

# --- SECCIÓN: APARTADOS Y ABONOS ---
elif menu == "Apartados y Abonos":
    st.header("📌 Gestión de Apartados")
    st.write("Módulo activo para registrar apartados con abonos iniciales.")

# --- SECCIÓN: HISTORIAL Y CAJA ---
elif menu == "Historial y Caja":
    st.header("📊 Historial de Transacciones y Caja")
    st.write("Resumen de caja y transacciones del día.")
