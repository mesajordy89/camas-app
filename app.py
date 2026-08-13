import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("Control de Inventario y Ventas - CAMAS")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Cargar datos existentes
df = conn.read(ttl=0)

# Formulario para agregar productos
st.subheader("➕ Agregar Nuevo Producto")

with st.form(key="nuevo_producto_form"):
    nombre = st.text_input("Nombre del Producto")
    categoria = st.selectbox("Categoría", ["Camas", "Colchones", "Accesorios", "Muebles", "Otros"])
    precio = st.number_input("Precio ($)", min_value=0.0, step=0.50)
    stock = st.number_input("Stock (Cantidad)", min_value=0, step=1)
    
    submit_button = st.form_submit_button(label="Guardar Producto")

if submit_button:
    if nombre.strip() == "":
        st.warning("Por favor, ingresa el nombre del producto.")
    else:
        # Crear la fila nueva
        nuevo_registro = pd.DataFrame([{
            "NOMBRE": nombre,
            "CATEGORIA": categoria,
            "PRECIO": precio,
            "STOCK": stock
        }])
        
        # Unir los datos nuevos con la lista actual
        df_actualizado = pd.concat([df, nuevo_registro], ignore_index=True)
        
        # Guardar cambios en Google Sheets
        conn.update(data=df_actualizado)
        st.success(f"¡Producto '{nombre}' guardado exitosamente!")
        st.rerun()

# Mostrar la tabla de productos actualizados
st.subheader("📦 Inventario Actual")
st.dataframe(df_actualizado if 'df_actualizado' in locals() else df, use_container_width=True)
