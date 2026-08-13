import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuración de página
st.set_page_config(page_title="CAMAS - Control de Inventario y Ventas", page_icon="🛏️", layout="wide")

CLAVE_ADMIN = "1234"

# Archivos locales de almacenamiento
FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"

# Cargar o crear Inventario (Categoría, Stock, Precio)
if os.path.exists(FILE_INV):
    df_inv = pd.read_csv(FILE_INV)
    if "PRECIO" not in df_inv.columns:
        df_inv["PRECIO"] = 0.0
else:
    df_inv = pd.DataFrame([
        {"CATEGORIA": "Camas", "STOCK": 0, "PRECIO": 0.0},
        {"CATEGORIA": "Colchones", "STOCK": 0, "PRECIO": 0.0},
        {"CATEGORIA": "Armarios", "STOCK": 0, "PRECIO": 0.0},
        {"CATEGORIA": "Pajaritas", "STOCK": 0, "PRECIO": 0.0}
    ])
    df_inv.to_csv(FILE_INV, index=False)

# Cargar o crear Ventas
if os.path.exists(FILE_VENTAS):
    df_ventas = pd.read_csv(FILE_VENTAS)
else:
    df_ventas = pd.DataFrame(columns=[
        "FECHA", "CATEGORIA", "CANTIDAD", "PRECIO_UNITARIO", "TOTAL", 
        "METODO_PAGO", "CLIENTE", "CEDULA", "TELEFONO", "CORREO"
    ])
    df_ventas.to_csv(FILE_VENTAS, index=False)

st.title("🛏️ Sistema de Control de Inventario y Ventas - CAMAS")

def mostrar_categoria(nombre_cat, icono):
    st.subheader(f"{icono} Gestión de {nombre_cat}")
    
    fila = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()]
    stock_actual = int(fila["STOCK"].values[0]) if not fila.empty else 0
    precio_actual = float(fila["PRECIO"].values[0]) if not fila.empty else 0.0
    
    # Métricas e indicadores
    col_m1, col_m2 = st.columns(2)
    col_m1.metric(f"Unidades Disponibles de {nombre_cat}", f"{stock_actual} unidades")
    col_m2.metric(f"Precio Unitario", f"${precio_actual:,.2f}")
    
    # Alerta de Stock Bajo
    if stock_actual <= 2:
        st.warning(f"⚠️ ¡Atención! Stock bajo en {nombre_cat}. Solo quedan {stock_actual} unidades.")
    
    st.markdown("---")
    col_in, col_out = st.columns(2)
    
    # --- 📥 ENTRADA Y PRECIOS (SOLO ADMIN CON CLAVE) ---
    with col_in:
        st.markdown("##### 📥 Recibir Mercancía y Configurar Precio (Admin)")
        clave = st.text_input(f"Clave Admin ({nombre_cat})", type="password", key=f"pass_{nombre_cat}")
        
        if clave == CLAVE_ADMIN:
            with st.form(key=f"form_sumar_{nombre_cat}"):
                cant_sumar = st.number_input("¿Cuántas llegaron?", min_value=0, step=1)
                nuevo_precio = st.number_input("Precio Unitario ($)", min_value=0.0, value=precio_actual, step=5.0)
                
                if st.form_submit_button("➕ Actualizar Inventario"):
                    idx = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()].index
                    if not idx.empty:
                        df_inv.loc[idx, "STOCK"] += cant_sumar
                        df_inv.loc[idx, "PRECIO"] = nuevo_precio
                        df_inv.to_csv(FILE_INV, index=False)
                    st.success(f"¡Inventario de {nombre_cat} actualizado!")
                    st.rerun()
        elif clave != "":
            st.error("Clave incorrecta")

    # --- 🛒 REGISTRAR VENTA (EMPLEADAS) ---
    with col_out:
        st.markdown("##### 🛒 Registrar Venta")
        with st.form(key=f"form_venta_{nombre_cat}"):
            cant_vender = st.number_input("Cantidad Vendida", min_value=1, step=1)
            metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta", "Crédito / Cuotas"])
            
            st.markdown("---")
            st.markdown("**Datos del Cliente:**")
            cliente_nom = st.text_input("Nombre y Apellido")
            cliente_ced = st.text_input("Cédula / DNI")
            cliente_tel = st.text_input("Número de Teléfono")
            cliente_cor = st.text_input("Correo Electrónico")
            
            total_calculado = cant_vender * precio_actual
            st.markdown(f"### **Total a cobrar: ${total_calculado:,.2f}**")
            
            btn_vender = st.form_submit_button("🛍️ Confirmar Venta")
            
            if btn_vender:
                if cant_vender > stock_actual:
                    st.error(f"No hay suficiente inventario. Solo quedan {stock_actual} unidades.")
                elif cliente_nom.strip() == "":
                    st.warning("Debes ingresar el nombre del cliente.")
                else:
                    # Descontar del inventario
                    idx = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()].index
                    if not idx.empty:
                        df_inv.loc[idx, "STOCK"] -= cant_vender
                        df_inv.to_csv(FILE_INV, index=False)
                    
                    # Registrar venta con detalle financiero
                    nueva_venta = pd.DataFrame([{
                        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "CATEGORIA": nombre_cat,
                        "CANTIDAD": cant_vender,
                        "PRECIO_UNITARIO": precio_actual,
                        "TOTAL": total_calculado,
                        "METODO_PAGO": metodo_pago,
                        "CLIENTE": cliente_nom,
                        "CEDULA": cliente_ced,
                        "TELEFONO": cliente_tel,
                        "CORREO": cliente_cor
                    }])
                    
                    df_v_actualizado = pd.concat([df_ventas, nueva_venta], ignore_index=True)
                    df_v_actualizado.to_csv(FILE_VENTAS, index=False)
                    
                    st.success(f"¡Venta confirmada! Se cobraron ${total_calculado:,.2f} a {cliente_nom}.")
                    st.rerun()

# Pestañas Principales
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
    st.subheader("📜 Historial de Ventas y Finanzas")
    
    if os.path.exists(FILE_VENTAS):
        df_v_hist = pd.read_csv(FILE_VENTAS)
        
        if df_v_hist.empty:
            st.info("Aún no hay ventas registradas.")
        else:
            # Resumen Financiero Superior
            total_recaudado = df_v_hist["TOTAL"].sum() if "TOTAL" in df_v_hist.columns else 0
            st.metric("Total Recaudado en Ventas", f"${total_recaudado:,.2f}")
            
            # Buscador
            busqueda = st.text_input("🔍 Buscar por Nombre o Cédula del Cliente:")
            if busqueda:
                df_filtrado = df_v_hist[
                    df_v_hist["CLIENTE"].astype(str).str.contains(busqueda, case=False, na=False) |
                    df_v_hist["CEDULA"].astype(str).str.contains(busqueda, case=False, na=False)
                ]
            else:
                df_filtrado = df_v_hist
                
            st.dataframe(df_filtrado, use_container_width=True)
            
            # Botón de Descargar a Excel/CSV
            csv_data = df_v_hist.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte Completo de Ventas (Excel/CSV)",
                data=csv_data,
                file_name=f"reporte_ventas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
    else:
        st.info("Aún no hay ventas registradas.")
