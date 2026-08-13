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

# Estilos visuales amigables
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
        height: 45px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-box">
        <h1 style="color:white; margin:0;">🏪 Local Mesitas - Control de Inventario y Ventas</h1>
        <p style="margin:5px 0 0 0;">Sistema ágil, rápido y simplificado</p>
    </div>
""", unsafe_allow_html=True)

# --- ALERTA INTELIGENTE DE STOCK BAJO ---
stock_critico = df_inv[df_inv["STOCK"] <= 2]
if not stock_critico.empty:
    productos_bajos = ", ".join([f"**{row['CATEGORIA']}** ({row['STOCK']} ud.)" for _, row in stock_critico.iterrows()])
    st.warning(f"🚨 **ATENCIÓN - STOCK BAJO:** {productos_bajos}. ¡Reabastece pronto!")

tab_ops, tab_inventario, tab_historial = st.tabs(["⚡ Vender y Operaciones", "🛠️ Inventario y Catálogo", "📜 Historial y Cierre de Caja"])

with tab_ops:
    # --- VISTA GENERAL DE INVENTARIO ---
    st.markdown("### 📊 Estado Rápido del Stock")
    
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
        st.markdown("### 🛒 Registrar Venta Rápida")
        
        if df_inv.empty:
            st.info("No hay productos registrados en el inventario.")
        else:
            categoria_sel = st.selectbox("1️⃣ Selecciona el Producto", df_inv["CATEGORIA"].tolist(), key="select_vender_cat")
            
            row_sel = df_inv[df_inv["CATEGORIA"] == categoria_sel].iloc[0]
            stock_disponible = int(row_sel["STOCK"])
            precio_unitario = float(row_sel["PRECIO"])
            
            with st.form(key="form_venta_unificado"):
                cant_vender = st.number_input("2️⃣ Cantidad Vendida", min_value=1, value=1, step=1)
                metodo_pago = st.selectbox("3️⃣ Método de Pago", ["Efectivo", "Transferencia", "Tarjeta", "Crédito / Cuotas"])
                
                st.markdown("---")
                st.markdown("**4️⃣ Datos del Cliente (Opcional pero recomendado):**")
                cliente_nom = st.text_input("Nombre y Apellido", value="Cliente General")
                cliente_ced = st.text_input("Cédula / DNI", value="S/N")
                cliente_tel = st.text_input("Teléfono", value="")
                cliente_cor = st.text_input("Correo", value="")
                
                total_calculado = float(cant_vender) * float(precio_unitario)
                
                st.markdown(f"""
                    <div style="background-color: #eef2f5; padding: 10px; border-radius: 8px; text-align: center; margin: 10px 0;">
                        <p style="margin:0; font-size: 13px; color: #555;">Precio unitario: ${precio_unitario:,.2f}</p>
                        <h3 style="margin:0; color: #1e3c72;">TOTAL A COBRAR: <b>${total_calculado:,.2f}</b></h3>
                    </div>
                """, unsafe_allow_html=True)
                
                btn_vender = st.form_submit_button("🛍️ CONFIRMAR Y REGISTRAR VENTA")
                
                if btn_vender:
                    if cant_vender > stock_disponible:
                        st.error(f"❌ Inventario insuficiente. Solo quedan {stock_disponible} unidades.")
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
                        
                        st.success(f"¡Venta registrada con éxito!")
                        
                        st.session_state["ultimo_recibo"] = f"""*LOCAL MESITAS - COMPROBANTE DE VENTA*
--------------------------------
📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
👤 Cliente: {cliente_nom}
📦 Producto: {categoria_sel}
🔢 Cantidad: {cant_vender} ud.
💳 Método de pago: {metodo_pago}
💰 TOTAL PAGADO: ${total_calculado:,.2f}
--------------------------------
¡Gracias por su compra!"""
                        st.rerun()

    # --- RECIBO RÁPIDO PARA COMPARTIR ---
    with col_ticket:
        st.markdown("### 🧾 Comprobante para WhatsApp")
        if "ultimo_recibo" in st.session_state:
            st.text_area("Copia este mensaje listo para enviar:", value=st.session_state["ultimo_recibo"], height=230)
        else:
            st.info("💡 Aquí aparecerá el comprobante automático de la última venta lista para que la copies y envíes por WhatsApp.")

with tab_inventario:
    st.markdown("### 🛠️ Administración de Inventario y Productos")
    clave = st.text_input("🔑 Clave Administrador", type="password", key="admin_key_input")
    
    if clave == CLAVE_ADMIN:
        st.success("🔓 Modo Administrador Activado")
        c_ing, c_crear = st.columns(2)
        
        with c_ing:
            st.markdown("#### 📦 Modificar Stock / Precio")
            if not df_inv.empty:
                cat_admin = st.selectbox("Seleccionar Producto", df_inv["CATEGORIA"].tolist(), key="select_admin_cat")
                row_admin = df_inv[df_inv["CATEGORIA"] == cat_admin].iloc[0]
                stk_actual = int(row_admin["STOCK"])
                prc_actual = float(row_admin["PRECIO"])
                
                with st.form(key="form_admin_unificado"):
                    st.markdown(f"Stock actual de **{cat_admin}**: `{stk_actual}` unidades")
                    ajuste_stock = st.number_input("Ajustar unidades (+ sumar, - restar)", value=0, step=1)
                    nuevo_precio = st.number_input("Precio Unitario ($)", min_value=0.0, value=prc_actual, step=5.0)
                    
                    if st.form_submit_button("💾 ACTUALIZAR DATOS"):
                        idx = df_inv[df_inv["CATEGORIA"] == cat_admin].index
                        if not idx.empty:
                            nuevo_stock_total = stk_actual + ajuste_stock
                            if nuevo_stock_total < 0:
                                nuevo_stock_total = 0
                            df_inv.loc[idx, "STOCK"] = nuevo_stock_total
                            df_inv.loc[idx, "PRECIO"] = nuevo_precio
                            df_inv.to_csv(FILE_INV, index=False)
                        st.success(f"¡Actualizado correctamente!")
                        st.rerun()
            else:
                st.info("No hay productos.")

        with c_crear:
            st.markdown("#### ✨ Crear Nuevo Producto")
            with st.form(key="form_nuevo_prod"):
                nuevo_prod_nombre = st.text_input("Nombre del producto (ej. Almohadas)")
                nuevo_prod_stock = st.number_input("Stock Inicial", min_value=0, value=10, step=1)
                nuevo_prod_precio = st.number_input("Precio Unitario ($)", min_value=0.0, value=25.0, step=5.0)
                
                if st.form_submit_button("➕ AÑADIR AL CATÁLOGO"):
                    if nuevo_prod_nombre.strip() == "":
                        st.warning("Escribe un nombre válido.")
                    elif nuevo_prod_nombre.capitalize() in df_inv["CATEGORIA"].values:
                        st.error("Este producto ya existe.")
                    else:
                        fila_nueva = pd.DataFrame([{
                            "CATEGORIA": nuevo_prod_nombre.strip().capitalize(),
                            "STOCK": nuevo_prod_stock,
                            "PRECIO": nuevo_prod_precio
                        }])
                        df_inv = pd.concat([df_inv, fila_nueva], ignore_index=True)
                        df_inv.to_csv(FILE_INV, index=False)
                        st.success(f"¡Creado con éxito!")
                        st.rerun()
    elif clave != "":
        st.error("Clave incorrecta")
    else:
        st.info("Ingresa la clave `1234` para desbloquear.")

with tab_historial:
    st.markdown("### 📜 Historial y Cierre de Caja por Método de Pago")
    
    if os.path.exists(FILE_VENTAS):
        df_v_hist = pd.read_csv(FILE_VENTAS)
        if df_v_hist.empty:
            st.info("Aún no hay ventas registradas.")
        else:
            # --- MEJORA 3: RESUMEN DE CAJA POR MÉTODO DE PAGO ---
            st.markdown("#### 💵 Cierre de Caja Actual (Ingresos por Método de Pago)")
            
            tot_efectivo = df_v_hist[df_v_hist["METODO_PAGO"] == "Efectivo"]["TOTAL"].sum() if "METODO_PAGO" in df_v_hist.columns else 0
            tot_trans = df_v_hist[df_v_hist["METODO_PAGO"] == "Transferencia"]["TOTAL"].sum() if "METODO_PAGO" in df_v_hist.columns else 0
            tot_tarjeta = df_v_hist[df_v_hist["METODO_PAGO"] == "Tarjeta"]["TOTAL"].sum() if "METODO_PAGO" in df_v_hist.columns else 0
            tot_credito = df_v_hist[df_v_hist["METODO_PAGO"] == "Crédito / Cuotas"]["TOTAL"].sum() if "METODO_PAGO" in df_v_hist.columns else 0
            tot_general = df_v_hist["TOTAL"].sum() if "TOTAL" in df_v_hist.columns else 0

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("💵 Efectivo", f"${tot_efectivo:,.2f}")
            m2.metric("🏦 Transf.", f"${tot_trans:,.2f}")
            m3.metric("💳 Tarjeta", f"${tot_tarjeta:,.2f}")
            m4.metric("📄 Crédito", f"${tot_credito:,.2f}")
            m5.metric("💰 TOTAL", f"${tot_general:,.2f}")
            
            st.markdown("---")
            busqueda = st.text_input("🔍 Buscar por Cliente o Cédula:")
            if busqueda:
                df_filtrado = df_v_hist[
                    df_v_hist["CLIENTE"].astype(str).str.contains(busqueda, case=False, na=False) |
                    df_v_hist["CEDULA"].astype(str).str.contains(busqueda, case=False, na=False)
                ]
            else:
                df_filtrado = df_v_hist
                
            st.dataframe(df_filtrado, use_container_width=True)
            
            # --- ANULAR VENTA ---
            st.markdown("---")
            st.markdown("#### 🗑️ Anular Venta Errónea")
            clave_borrar = st.text_input("🔑 Clave Administrador para Anular Venta", type="password", key="key_del_venta")
            
            if clave_borrar == CLAVE_ADMIN:
                if not df_v_hist.empty:
                    opciones_ventas = [f"Fila {i} | Fecha: {row['FECHA']} | Cliente: {row['CLIENTE']} | Total: ${row['TOTAL']}" for i, row in df_v_hist.iterrows()]
                    venta_a_borrar_str = st.selectbox("Selecciona la venta a eliminar", opciones_ventas)
                    
                    if st.button("❌ ELIMINAR VENTA Y DEVOLVER STOCK"):
                        idx_str = venta_a_borrar_str.split(" | ")[0].replace("Fila ", "")
                        idx_venta = int(idx_str)
                        
                        cat_venta = df_v_hist.loc[idx_venta, "CATEGORIA"]
                        cant_venta = int(df_v_hist.loc[idx_venta, "CANTIDAD"])
                        
                        if cat_venta in df_inv["CATEGORIA"].values:
                            df_inv.loc[df_inv["CATEGORIA"] == cat_venta, "STOCK"] += cant_venta
                            df_inv.to_csv(FILE_INV, index=False)
                        
                        df_v_nuevo = df_v_hist.drop(idx_venta).reset_index(drop=True)
                        df_v_nuevo.to_csv(FILE_VENTAS, index=False)
                        
                        st.success("¡Venta eliminada y stock devuelto!")
                        st.rerun()
            elif clave_borrar != "":
                st.error("Clave incorrecta")
                
            st.markdown("---")
            csv_data = df_v_hist.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte Completo (CSV)",
                data=csv_data,
                file_name=f"ventas_mesitas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
