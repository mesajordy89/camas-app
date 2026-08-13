import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Control de Inventario y Ventas - CAMAS")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
    st.write("### Datos cargados correctamente:")
    st.dataframe(df)
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
