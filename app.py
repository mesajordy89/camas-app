import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuración de página
st.set_page_config(page_title="Local Mesitas - Control de Inventario", page_icon="🛏️", layout="wide")

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
        <h1 style="color:white; margin:0;">🏪 Local Mesitas - Control de Inventario y Ventas</h1>
        <p style="margin:5px 0 0 0;">Sistema integral con alertas inteligentes y gestión dinámica</p>
    </div>
""", unsafe_allow_html=True)

# --- ALERTA INTELIGENTE DE STOCK BAJO ---
stock_critico = df_inv[df_inv["STOCK"] <= 2]
if not stock_critico.empty:
    productos_bajos = ", ".join([f"**{row['CATEGORIA']}** ({row['STOCK']} ud.)" for _, row in stock_critico.iterrows()])
    st.warning(f"🚨 **ALERTA DE STOCK CRÍTICO:** Los siguientes productos tienen poca o nula existencia: {productos_bajos}. ¡Reabastece pronto!")

tab_ops, tab_inventario, tab_historial = st.tabs(["⚡ Operaciones y Ventas", "🛠️ Administrar Inventario y Productos", "📜 Historial y Reportes"])

with tab_ops:
    # --- VISTA GENERAL DE INVENTARIO ---
    st.markdown("### 📊 Estado Actual del Inventario")
    
    iconos = {"Camas": "🛏️", "Colchones": "💤", "Armarios": "🚪", "Pajaritas": "🎀"}
    cols = st.columns(len(df_inv) if len(df_inv) > 0 else 1)
    
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

    st.markdown("---")
    
    col_vender, col_ticket = st.columns(2)
    
    # --- REGISTRAR VENTA ---
    with col_vender:
        st.markdown("### 🛒 Registrar Venta")
        
        if df_inv.empty:
            st.info("No hay productos registrados en el inventario.")
        else:
            categoria_sel = st.selectbox("Seleccionar Producto", df_inv["CATEGORIA"].tolist(), key="select_vender_cat")
            
            row_sel = df_inv[df_inv["CATEGORIA"] == categoria_sel].iloc[0]
            stock_disponible = int(row_sel["STOCK"])
            precio_unitario = float(row_sel["PRECIO"])
            
            with st.form(key="form_venta_unificado"):
                cant_vender = st.number_input("Cantidad Vendida", min_value=1, value=1, step=1)
                metodo_pago = st.selectbox("💳 Método de Pago", ["Efectivo", "Transferencia", "Tarjeta", "Crédito / Cuotas"])
                
                st.markdown("**Datos del Cliente:**")
                cliente_nom = st.text_input("Nombre y Apellido")
                cliente_ced = st.text_input("Cédula / DNI")
                cliente_tel = st.text_input("Teléfono")
                cliente_cor = st.text_input("Correo")
                
                # Cálculo directo de la multiplicación
                total_calculado = float(cant_vender) * float(precio_unitario)
                
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
                        df_inv.loc[df_inv["CATEGORIA"] == categoria_sel, "STOCK"] -= cant_vender
                        df_inv.to_csv(FILE_INV, index=False)
                        
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
                        
                        # Guardar correctamente en la sesión con el total ya calculado
                        st.session_state["ultimo_recibo"] = {
                            "cliente": cliente_nom, "producto": categoria_sel, 
                            "cantidad": cant_vender, "total": total_calculado, "pago": metodo_pago
                        }
                        st.rerun()

    # --- RECIBO RÁPIDO PARA COMPARTIR ---
    with col_ticket:
        st.markdown("### 🧾 Comprobante / Recibo Reciente")
        if "ultimo_recibo" in st.session_state:
            rec = st.session_state["ultimo_recibo"]
            ticket_texto = f"""*LOCAL MESITAS - COMPROBANTE DE VENTA*
--------------------------------
📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
👤 Cliente: {rec['cliente']}
📦 Producto: {rec['producto']}
🔢 Cantidad: {rec['cantidad']} ud.
💳 Método de pago: {rec['pago']}
💰 *TOTAL PAGADO: ${float(rec['total']):,.2f}*
--------------------------------
¡Gracias por su compra!"""
            st.text_area("Copia este mensaje para WhatsApp:", value=ticket_texto, height=180)
        else:
            st.info("💡 Realiza una venta para generar el comprobante instantáneo y enviarlo por WhatsApp al cliente.")

with tab_inventario:
    st.markdown("### 🛠️ Gestión Avanzada de Inventario y Creación de Productos")
    clave = st.text_input("🔑 Clave Administrador", type="password", key="admin_key_input")
    
    if clave == CLAVE_ADMIN:
        st.success("🔓 Modo Administrador Activado")
        c_ing, c_crear = st.columns(2)
        
        with c_ing:
            st.markdown("#### 📦 Modificar Stock / Precio Existente")
            if not df_inv.empty:
                cat_admin = st.selectbox("Producto a Modificar", df_inv["CATEGORIA"].tolist(), key="select_admin_cat")
                row_admin = df_inv[df_inv["CATEGORIA"] == cat_admin].iloc[0]
                stk_actual = int(row_admin["STOCK"])
                prc_actual = float(row_admin["PRECIO"])
                
                with st.form(key="form_admin_unificado"):
                    st.markdown(f"Stock actual de **{cat_admin}**: `{stk_actual}` unidades")
                    ajuste_stock = st.number_input("Ajustar unidades (+ para sumar, - para restar)", value=0, step=1)
                    nuevo_precio = st.number_input("Precio Unitario ($)", min_value=0.0, value=prc_actual, step=5.0)
                    
                    if st.form_submit_button("💾 ACTUALIZAR STOCK Y PRECIO"):
                        idx = df_inv[df_inv["CATEGORIA"] == cat_admin].index
                        if not idx.empty:
                            nuevo_stock_total = stk_actual + ajuste_stock
                            if nuevo_stock_total < 0:
                                nuevo_stock_total = 0
                            df_inv.loc[idx, "STOCK"] = nuevo_stock_total
                            df_inv.loc[idx, "PRECIO"] = nuevo_precio
                            df_inv.to_csv(FILE_INV, index=False)
                        st.success(f"¡Inventario de {cat_admin} actualizado!")
                        st.rerun()
            else:
                st.info("No hay productos.")

        with c_crear:
            st.markdown("#### ✨ Crear Nuevo Producto o Categoría")
            with st.form(key="form_nuevo_prod"):
                nuevo_prod_nombre = st.text_input("Nombre del nuevo artículo (ej. Almohadas)")
                nuevo_prod_stock = st.number_input("Stock Inicial", min_value=0, value=10, step=1)
                nuevo_prod_precio = st.number_input("Precio Unitario ($)", min_value=0.0, value=25.0, step=5.0)
                
                if st.form_submit_button("➕ AÑADIR AL CATÁLOGO"):
                    if nuevo_prod_nombre.strip() == "":
                        st.warning("Escribe un nombre válido.")
                    elif nuevo_prod_nombre.capitalize() in df_inv["CATEGORIA"].values:
                        st.error("Este producto ya existe en el inventario.")
                    else:
                        fila_nueva = pd.DataFrame([{
                            "CATEGORIA": nuevo_prod_nombre.strip().capitalize(),
                            "STOCK": nuevo_prod_stock,
                            "PRECIO": nuevo_prod_precio
                        }])
                        df_inv = pd.concat([df_inv, fila_nueva], ignore_index=True)
                        df_inv.to_csv(FILE_INV, index=False)
                        st.success(f"¡Producto '{nuevo_prod_nombre}' agregado exitosamente!")
                        st.rerun()
    elif clave != "":
        st.error("Clave incorrecta")
    else:
        st.info("Ingresa la clave `1234` para desbloquear la administración.")

with tab_historial:
    st.markdown("### 📜 Historial y Reportes Financieros")
    if os.path.exists(FILE_VENTAS):
        df_v_hist = pd.read_csv(FILE_VENTAS)
        if df_v_hist.empty:
            st.info("Aún no hay ventas registradas.")
        else:
            total_recaudado = df_v_hist["TOTAL"].sum() if "TOTAL" in df_v_hist.columns else 0
            
            k1, k2 = st.columns(2)
            k1.metric("💰 Recaudación Total", f"${total_recaudado:,.2f}")
            k2.metric("🛍️ Total Transacciones", f"{len(df_v_hist)} ventas")
            
            st.markdown("---")
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
                file_name=f"ventas_mesitas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
