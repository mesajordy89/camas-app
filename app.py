import streamlit as st

# 1. Inicializar la lista en st.session_state si no existe
if "lista_productos" not in st.session_state:
  st.session_state.lista_productos = [
      "Cama 1.5 plazas",
      "Cama 2 plazas",
      "Cama Queen",
      "Cama King",
      "Colchones",
  ]

st.subheader("Gestión y Selección de Productos")

# 2. Campo para que puedas escribir y agregar un nuevo elemento tú mismo
nuevo_producto = st.text_input("Agregar nuevo producto a la lista:")
if st.button("Añadir a la lista"):
  if (
      nuevo_producto
      and nuevo_producto not in st.session_state.lista_productos
  ):
    st.session_state.lista_productos.append(nuevo_producto)
    st.success(f"¡'{nuevo_producto}' agregado con éxito!")
    st.rerun()  # Recarga la app para actualizar el menú desplegable
  elif not nuevo_producto:
    st.warning("Escribe el nombre del producto primero.")
  else:
    st.info("Ese producto ya existe en la lista.")

# 3. Menú desplegable que se alimenta de tu lista dinámica
producto_seleccionado = st.selectbox(
    "Selecciona el Producto", options=st.session_state.lista_productos
)

st.write(f"Producto activo para la venta: **{producto_seleccionado}**")
