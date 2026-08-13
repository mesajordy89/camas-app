import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="CAMAS - Control de Inventario y Ventas", page_icon="🛏️", layout="wide")

CLAVE_ADMIN = "1234"

# Archivos locales de almacenamiento
FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"

# Cargar o crear Inventario
if os.path.exists(FILE_INV):
    df_inv = pd.read_csv(FILE_INV)
else:
    df_inv = pd.DataFrame([
        {"CATEGORIA": "Camas", "STOCK": 0},
        {"CATEGORIA": "Colchones", "STOCK": 0},
        {"CATEGORIA": "Armarios", "STOCK": 0},
        {"CATEGORIA": "Pajaritas", "STOCK": 0}
    ])
    df_inv.to_csv(FILE_INV, index=False)

# Cargar o crear Ventas
if os.path.exists(FILE_VENTAS):
    df_ventas = pd.read_csv(FILE_VENTAS)
else:
    df_ventas = pd.DataFrame(columns=["FECHA", "CATEGORIA", "CANTIDAD", "CLIENTE", "CEDULA", "TELEFONO", "CORREO"])
    df_ventas.to_csv(FILE_VENTAS, index=False)

st.title("🛏️ Control de Unidades y Ventas - CAMAS")

def mostrar_categoria(nombre_cat, icono):
    st.subheader(f"{icono} {nombre_cat}")
    
    fila = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()]
    stock_actual = int(fila["STOCK"].values[0]) if not fila.empty else 0
    
    st.metric(f"Unidades Disponibles de {nombre_cat}", f"{stock_actual} unidades")
    
    col_in, col_out = st.columns(2)
    
    # --- ENTRADA SOLO CON CLAVE ---
    with col_in:
        st.markdown("##### 📥 Llegó Mercancía (Acceso Admin)")
        clave = st.text_input(f"Clave Admin ({nombre_cat})", type="password", key=f"pass_{nombre_cat}")
        
        if clave == CLAVE_ADMIN:
            with st.form(key=f"form_sumar_{nombre_cat}"):
                cant_sumar = st.number_input("¿Cuántas llegaron?", min_value=1, step=1)
                if st.form_submit_button("➕ Sumar al Inventario"):
                    idx = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()].index
                    if not idx.empty:
                        df_inv.loc[idx, "STOCK"] += cant_sumar
                        df_inv.to_csv(FILE_INV, index=False)
                    st.success(f"¡Se sumaron {cant_sumar} unidades a {nombre_cat}!")
                    st.rerun()
        elif clave != "":
            st.error("Clave incorrecta")

    # --- VENTAS Y CLIENTES ---
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
                    # Descontar stock
                    idx = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()].index
                    if not idx.empty:
                        df_inv.loc[idx, "STOCK"] -= cant_vender
                        df_inv.to_csv(FILE_INV, index=False)
                    
                    # Guardar Venta
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
                    df_v_actualizado.to_csv(FILE_VENTAS, index=False)
                    
                    st.success(f"¡Venta realizada! Se descontaron {cant_vender} unidades y se guardaron los datos de {cliente_nom}.")
                    st.rerun()

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
    if os.path.exists(FILE_VENTAS):
        df_v_hist = pd.read_csv(FILE_VENTAS)
        if df_v_hist.empty:
            st.info("Aún no hay ventas registradas.")
        else:
            st.dataframe(df_v_hist, use_container_width=True)
    else:
        st.info("Aún no hay ventas registradas.")
