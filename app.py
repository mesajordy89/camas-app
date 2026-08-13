import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="CAMAS - Inventario Rápido", page_icon="🛏️", layout="wide")

# Clave para autorizar llegada de mercancía (puedes cambiar "1234")
CLAVE_ADMIN = "1234"

st.title("🛏️ Control de Unidades - CAMAS")

conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

CATEGORIAS = ["Camas", "Colchones", "Armarios", "Pajaritas"]

# Asegurar que existan los registros base
if df.empty or "CATEGORIA" not in df.columns:
    df = pd.DataFrame([{"CATEGORIA": cat, "STOCK": 0} for cat in CATEGORIAS])

st.markdown("---")

# Función simplificada por categoría
def mostrar_categoria_simple(nombre_cat, icono):
    st.subheader(f"{icono} {nombre_cat}")
    
    # Obtener stock actual de la categoría
    fila = df[df["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()]
    stock_actual = fila["STOCK"].values[0] if not fila.empty else 0
    
    # Mostrar cantidad grande en tarjeta
    st.metric(f"Unidades Disponibles de {nombre_cat}", f"{stock_actual} unidades")
    
    col_in, col_out = st.columns(2)
    
    # --- ENTRADA (MERCANCÍA QUE LLEGA) ---
    with col_in:
        st.markdown("##### 📥 Llegó Mercancía (Solo Admin)")
        clave = st.text_input(f"Clave Admin ({nombre_cat})", type="password", key=f"pass_{nombre_cat}")
        
        if clave == CLAVE_ADMIN:
            with st.form(key=f"form_sumar_{nombre_cat}"):
                cant_sumar = st.number_input("¿Cuántas llegaron?", min_value=1, step=1)
                if st.form_submit_button("➕ Sumar Unidades"):
                    df.loc[df["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper(), "STOCK"] += cant_sumar
                    conn.update(data=df)
                    st.success(f"¡Se sumaron {cant_sumar} unidades a {nombre_cat}!")
                    st.rerun()
        elif clave != "":
            st.error("Clave incorrecta")
            
    # --- SALIDA (VENTA REALIZADA) ---
    with col_out:
        st.markdown("##### 🛒 Se Vendió (Empleados)")
        with st.form(key=f"form_restar_{nombre_cat}"):
            cant_restar = st.number_input("¿Cuántas se vendieron?", min_value=1, step=1)
            if st.form_submit_button("➖ Restar Venta"):
                if cant_restar > stock_actual:
                    st.error(f"No hay suficientes unidades. Disponibles: {stock_actual}")
                else:
                    df.loc[df["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper(), "STOCK"] -= cant_restar
                    conn.update(data=df)
                    st.success(f"¡Se restaron {cant_restar} unidades de {nombre_cat}!")
                    st.rerun()

# Pestañas principales
tab_camas, tab_colchones, tab_armarios, tab_pajaritas = st.tabs([
    "🛏️ Camas", "💤 Colchones", "🚪 Armarios", "🎀 Pajaritas"
])

with tab_camas:
    mostrar_categoria_simple("Camas", "🛏️")

with tab_colchones:
    mostrar_categoria_simple("Colchones", "💤")

with tab_armarios:
    mostrar_categoria_simple("Armarios", "🚪")

with tab_pajaritas:
    mostrar_categoria_simple("Pajaritas", "🎀")
