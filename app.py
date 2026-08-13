import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuración de página
st.set_page_config(page_title="CAMAS - Control de Inventario", page_icon="🛏️", layout="wide")

CLAVE_ADMIN = "1234"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"

# Cargar o crear Inventario
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

# Estilos visuales
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .header-box {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .stButton>button {
        background: #1e3c72;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-box">
        <h1 style="color:white; margin:0;">🛏️ Control de Inventario y Ventas - CAMAS</h1>
        <p style="margin:5px 0 0 0;">Gestión de stock, precios y facturación automática</p>
    </div>
""", unsafe_allow_html=True)

tab_ops, tab_historial = st.tabs(["⚡ Operaciones Rápidas", "📜 Historial de Ventas"])

with tab_ops:
    # --- VISTA GENERAL DE INVENTARIO ---
    st.markdown("### 📊 Estado Actual del Inventario y Precios")
    
    iconos = {"Camas": "🛏️", "Colchones": "💤", "Armarios": "🚪", "Pajaritas": "🎀"}
    cols = st.columns(len(df_inv))
    
    for idx, row in df_inv.iterrows():
        cat = row["CATEGORIA"]
        stk = int(row["STOCK"])
        prc = float(row["PRECIO"])
        ico = iconos.get(cat, "📦")
        
        with cols[idx]:
            st.metric(
                label=f"{ico} {cat}", 
                value=f"{stk} ud.", 
                delta=f"${prc:,.2f}"
            )
            if stk <= 2:
                st.caption("⚠️ *Stock Bajo*")

    st.markdown("---")
    
    col_vender, col_ingresar = st.columns(2)
    
    # --- REGISTRAR VENTA (CÁLCULO AUTOMÁTICO) ---
    with col_vender:
        st.markdown("### 🛒 Registrar Venta")
        
        # Selector de categoría fuera del formulario para calcular en tiempo real
        categoria_sel = st.selectbox("Seleccionar Producto", df_inv["CATEGORIA"].tolist(), key="select_vender_cat")
        
        row_sel = df_inv[df_inv["CATEGORIA"] == categoria_sel].iloc[0]
        stock_disponible = int(row_sel["STOCK"])
        precio_unitario = float(row_sel["PRECIO"])
        
        with st.form(key="form_venta_unificado"):
            cant_vender = st.number_input("Cantidad Vendida", min_value=1, value=1, step=1)
            metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta", "Crédito / Cuotas"])
            
            st.markdown("**Datos del Cliente:**")
            cliente_nom = st.text_input("Nombre y Apellido")
            cliente_ced = st.text_input("Cédula / DNI")
            cliente_tel = st.text_input("Teléfono")
            cliente_cor = st.text_input("Correo")
            
            # Cálculo matemático automático
            total_calculado = cant_vender * precio_unitario
            
            st.markdown(f"""
                <div style="background-color: #eef2f5; padding: 12px; border-radius: 8px; text-align: center; margin: 10px 0;">
                    <p style="margin:0; font-size: 14px; color: #555;">Precio unitario: ${precio_unitario:,.2f}</p>
                    <h3 style="margin:0; color: #1e3c72;">Total a cobrar: <b>${total_calculado:,.2f}</b></h3>
                </div>
            """, unsafe_allow_html=True)
            
            btn_vender = st.form_submit_button("🛍️ CONFIRMAR VENTA")
            
            if btn_vender:
                if cant_vender > stock_disponible:
                    st.error(f"❌ Inventario insuficiente. Solo quedan {stock_disponible} unidades.")
                elif cliente_nom.strip() == "":
                    st.warning("⚠️ Debes ingresar el nombre del cliente.")
                else:
                    # Restar stock
                    df_inv.loc[df_inv["CATEGORIA"] == categoria_sel, "STOCK"] -= cant_vender
                    df_inv.to_csv(FILE_INV, index=False)
                    
                    # Guardar venta
                    nueva_venta = pd.DataFrame([{
                        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "CATEGORIA": categoria_sel,
                        "CANTIDAD": cant_vender,
                        "PRECIO_UNITARIO": precio_unitario,
                        "TOTAL": total_calculado,
                        "METODO_PAGO": metodo_pago,
                        "CLIENTE": cliente_nom,
                        "CEDULA": cliente_ced,
                        "TELEFONO": cliente_tel,
                        "CORREO": cliente_cor
                    }])
                    df_v_act = pd.concat([df_ventas, nueva_venta], ignore_index=True)
                    df_v_act.to_csv(FILE_VENTAS, index=False)
                    
                    st.success(f"¡Venta realizada por ${total_calculado:,.2f}!")
                    st.rerun()

    # --- INGRESAR O CORREGIR MERCANCÍA (ADMIN) ---
    with col_ingresar:
        st.markdown("### 📥 Administrar Inventario y Precios")
        clave = st.text_input("🔑 Clave Administrador", type="password", key="admin_key_input")
        
        if clave == CLAVE_ADMIN:
            cat_admin = st.selectbox("Producto a Modificar", df_inv["CATEGORIA"].tolist(), key="select_admin_cat")
            row_admin = df_inv[df_inv["CATEGORIA"] == cat_admin].iloc[0]
            stk_actual = int(row_admin["STOCK"])
            prc_actual = float(row_admin["PRECIO"])
            
            with st.form(key="form_admin_unificado"):
                st.markdown(f"Stock actual de **{cat_admin}**: `{stk_actual}` unidades")
                
                # Permite sumar (positivo) o restar (negativo) por si hubo un error
                ajuste_stock = st.number_input("Ajustar unidades (+ para sumar, - para corregir/restar)", value=0, step=1)
                nuevo_precio = st.number_input("Precio Unitario ($)", min_value=0.0, value=prc_actual, step=5.0)
                
                if st.form_submit_button("💾 APLICAR CAMBIOS EN INVENTARIO"):
                    idx = df_inv[df_inv["CATEGORIA"] == cat_admin].index
                    if not idx.empty:
                        nuevo_stock_total = stk_actual + ajuste_stock
                        if nuevo_stock_total < 0:
                            nuevo_stock_total = 0
                        df_inv.loc[idx, "STOCK"] = nuevo_stock_total
                        df_inv.loc[idx, "PRECIO"] = nuevo_precio
                        df_inv.to_csv(FILE_INV, index=False)
                    st.success(f"¡Inventario y precio de {cat_admin} actualizados con éxito!")
                    st.rerun()
        elif clave != "":
            st.error("Clave incorrecta")
        else:
            st.info("Ingresa la clave `1234` para ajustar inventarios o cambiar precios.")

with tab_historial:
    st.markdown("### 📜 Historial de Ventas")
    if os.path.exists(FILE_VENTAS):
        df_v_hist = pd.read_csv(FILE_VENTAS)
        if df_v_hist.empty:
            st.info("Aún no hay ventas registradas.")
        else:
            total_recaudado = df_v_hist["TOTAL"].sum() if "TOTAL" in df_v_hist.columns else 0
            st.metric("Total Recaudado", f"${total_recaudado:,.2f}")
            
            busqueda = st.text_input("🔍 Buscar Cliente o Cédula:")
            if busqueda:
                df_filtrado = df_v_hist[
                    df_v_hist["CLIENTE"].astype(str).str.contains(busqueda, case=False, na=False) |
                    df_v_hist["CEDULA"].astype(str).str.contains(busqueda, case=False, na=False)
                ]
            else:
                df_filtrado = df_v_hist
                
            st.dataframe(df_filtrado, use_container_width=True)
            
            csv_data = df_v_hist.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte (Excel / CSV)",
                data=csv_data,
                file_name=f"ventas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
