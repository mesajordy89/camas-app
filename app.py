import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de la página
st.set_page_config(page_title="CAMAS - Control de Inventario y Ventas", page_icon="🛏️", layout="wide")

# Clave secreta para que SOLO TÚ puedas ingresar mercancía
CLAVE_ADMIN = "1234"

st.title("🛏️ Control de Unidades y Ventas - CAMAS")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Cargar Inventario
try:
    df_inv = conn.read(worksheet="Inventario", ttl=0)
except Exception:
    try:
        df_inv = conn.read(ttl=0)
    except Exception:
        df_inv = pd.DataFrame([
            {"CATEGORIA": "Camas", "STOCK": 0},
            {"CATEGORIA": "Colchones", "STOCK": 0},
            {"CATEGORIA": "Armarios", "STOCK": 0},
            {"CATEGORIA": "Pajaritas", "STOCK": 0}
        ])

# Cargar Ventas
try:
    df_ventas = conn.read(worksheet="Ventas", ttl=0)
except Exception:
    df_ventas = pd.DataFrame(columns=["FECHA", "CATEGORIA", "CANTIDAD", "CLIENTE", "CEDULA", "TELEFONO", "CORREO"])

# Validar columnas del inventario
if "CATEGORIA" not in df_inv.columns or "STOCK" not in df_inv.columns:
    df_inv = pd.DataFrame([
        {"CATEGORIA": "Camas", "STOCK": 0},
        {"CATEGORIA": "Colchones", "STOCK": 0},
        {"CATEGORIA": "Armarios", "STOCK": 0},
        {"CATEGORIA": "Pajaritas", "STOCK": 0}
    ])

def mostrar_categoria(nombre_cat, icono):
    st.subheader(f"{icono} {nombre_cat}")
    
    # Obtener stock actual
    fila = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()]
    stock_actual = int(fila["STOCK"].values[0]) if not fila.empty else 0
    
    st.metric(f"Unidades Disponibles de {nombre_cat}", f"{stock_actual} unidades")
    
    col_in, col_out = st.columns(2)
    
    # --- SOLO TÚ (CON CLAVE) PUEDES INGRESAR MERCANCÍA ---
    with col_in:
        st.markdown("##### 📥 Llegó Mercancía (Acceso Administrador)")
        clave = st.text_input(f"Clave Admin ({nombre_cat})", type="password", key=f"pass_{nombre_cat}")
        
        if clave == CLAVE_ADMIN:
            with st.form(key=f"form_sumar_{nombre_cat}"):
                cant_sumar = st.number_input("¿Cuántas llegaron?", min_value=1, step=1)
                if st.form_submit_button("➕ Sumar al Inventario"):
                    df_inv.loc[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper(), "STOCK"] += cant_sumar
                    
                    # Guardar cambios usando conn.write() para evitar UnsupportedOperationError
                    try:
                        conn.write(worksheet="Inventario", data=df_inv)
                    except Exception:
                        conn.write(data=df_inv)
                        
                    st.success(f"¡Se sumaron {cant_sumar} unidades a {nombre_cat}!")
                    st.rerun()
        elif clave != "":
            st.error("Clave incorrecta")

    # --- TUS EMPLEADAS REGISTRAN LA VENTA Y CLIENTE ---
    with col_out:
        st.markdown("##### 🛒 Registrar Venta")
        with st.form(key=f"form_venta_{nombre_cat}"):
            cant_vender = st.number_input("Cantidad Vendida", min_value=1, step=1)
            
            st.markdown("---")
            st.markdown("**Datos del Cliente:**")
            cliente_nom = st.text_input("Nombre y Apellido")
            cliente_ced = st.text_input("Cédula / DNI")
            cliente_tel = st.text_input("Número de Teléfono")
            cliente_cor = st.text_input("Correo Electrónico")
            
            btn_vender = st.form_submit_button("🛍️ Confirmar Venta")
            
            if btn_vender:
                if cant_vender > stock_actual:
                    st.error(f"No hay suficiente inventario. Solo quedan {stock_actual} unidades.")
                elif cliente_nom.strip() == "":
                    st.warning("Debes ingresar el nombre del cliente.")
                else:
                    # 1. Descontar del inventario
                    df_inv.loc[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper(), "STOCK"] -= cant_vender
                    try:
                        conn.write(worksheet="Inventario", data=df_inv)
                    except Exception:
                        conn.write(data=df_inv)
                    
                    # 2. Registrar la venta en la pestaña Ventas
                    nueva_venta = pd.DataFrame([{
                        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "CATEGORIA": nombre_cat,
                        "CANTIDAD": cant_vender,
                        "CLIENTE": cliente_nom,
                        "CEDULA": cliente_ced,
                        "TELEFONO": cliente_tel,
                        "CORREO": cliente_cor
                    }])
                    
                    df_v_actualizado = pd.concat([df_ventas, nueva_venta], ignore_index=True)
                    try:
                        conn.write(worksheet="Ventas", data=df_v_actualizado)
                    except Exception:
                        conn.write(data=df_v_actualizado)
                    
                    st.success(f"¡Venta realizada! Se descontaron {cant_vender} unidades y se guardó la venta de {cliente_nom}.")
                    st.rerun()

# Pestañas principales
tab_camas, tab_colchones, tab_armarios, tab_pajaritas, tab_historial = st.tabs([
    "🛏️ Camas", "💤 Colchones", "🚪 Armarios", "🎀 Pajaritas", "📜 Historial de Ventas"
])

with tab_camas:
    mostrar_categoria("Camas", "🛏️")

with tab_colchones:
    mostrar_categoria("Colchones", "💤")

with tab_armarios:
    mostrar_categoria("Armarios", "🚪")

with tab_pajaritas:
    mostrar_categoria("Pajaritas", "🎀")

with tab_historial:
    st.subheader("📜 Historial de Ventas Realizadas")
    if df_ventas.empty:
        st.info("Aún no hay ventas registradas.")
    else:
        st.dataframe(df_ventas, use_container_width=True)
