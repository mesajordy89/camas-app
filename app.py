import streamlit as st

# ==========================================
# 1. INICIALIZAR LA LISTA EN SESSION_STATE
# ==========================================
if "lista_productos" not in st.session_state:
  st.session_state.lista_productos = [
      "Cama 1.5 plazas",
      "Cama 2 plazas",
      "Cama Queen",
      "Cama King",
      "Colchones",
  ]

# --- AQUÍ VA TODO EL CÓDIGO QUE YA TENÍAS PREVIAMENTE (Títulos, estilos, etc.) ---

st.subheader("Gestión y Selección de Productos")

# ==========================================
# 2. APARTADO PARA AGREGAR PRODUCTOS TÚ MISMO
# ==========================================
nuevo_producto = st.text_input("Agregar nuevo producto a la lista:")
if st.button("Añadir a la lista"):
  if (
      nuevo_producto
      and nuevo_producto not in st.session_state.lista_productos
  ):
    st.session_state.lista_productos.append(nuevo_producto)
    st.success(f"¡'{nuevo_producto}' agregado con éxito!")
    st.rerun()  # Actualiza la pantalla para que aparezca de inmediato
  elif not nuevo_producto:
    st.warning("Escribe el nombre del producto primero.")
  else:
    st.info("Ese producto ya existe en la lista.")

# ==========================================
# 3. TU MENÚ SELECTBOX CONECTADO A LA LISTA DINÁMICA
# ==========================================
producto_seleccionado = st.selectbox(
    "Selecciona el Producto", options=st.session_state.lista_productos
)

st.write(f"Producto activo para la venta: **{producto_seleccionado}**")

# --- AQUÍ CONTINÚA EL RESTO DE TU CÓDIGO (Formulario de cliente, total, WhatsApp, etc.) ---
