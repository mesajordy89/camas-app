import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuración de página con layout amplio
st.set_page_config(
    page_title="CAMAS - Control de Inventario", 
    page_icon="🛏️", 
    layout="wide"
)

CLAVE_ADMIN = "1234"

# Archivos de datos
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

# --- ESTILOS CSS PERSONALIZADOS (DISEÑO PREMIUM) ---
st.markdown("""
    <style>
    /* Estilo del fondo y contenedor principal */
    .stApp {
        background-color: #f4f6f9;
    }
    
    /* Encabezado principal */
    .title-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 24px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .title-banner h1 {
        color: #ffffff !important;
        font-weight: 800;
        margin: 0;
    }
    
    /* Tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-left: 6px solid #2a5298;
    }

    /* Estilizado de pestañas */
    button[data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: bold !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 10px 20px !important;
    }
    
    /* Cajas de secciones */
    .card-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin-bottom: 20px;
    }
    
    /* Botones primarios */
    .stButton>button {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        border-radius: 10px;
        height: 3em;
        font-size: 16px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(42,82,152,0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(42,82,152,0.4);
    }
    </style>
""", unsafe_allow_html=True)

# Banner superior
st.markdown("""
    <div class="title-banner">
        <h1>🛏️ Sistema de Gestión e Inventario - CAMAS</h1>
        <p style="margin-top: 5px; opacity: 0.9;">Control en tiempo real de productos, ventas y clientes</p>
    </div>
""", unsafe_allow_html=True)

# Función para renderizar la interfaz de cada categoría
def mostrar_categoria(nombre_cat, icono):
    fila = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()]
    stock_actual = int(fila["STOCK"].values[0]) if not fila.empty else 0
    precio_actual = float(fila["PRECIO"].values[0]) if not fila.empty else 0.0
    
    # Métricas superiores vistosas
    m1, m2, m3 = st.columns(3)
    m1.metric("📦 Categoría", f"{icono} {nombre_cat}")
    m2.metric("📊 Unidades en Stock", f"{stock_actual} ud.")
    m3.metric("🏷️ Precio Unitario", f"${precio_actual:,.2f}")
    
    if stock_actual <= 2:
        st.error(f"⚠️ **ALERTA DE STOCK BAJO:** Quedan solo {stock_actual} unidades disponibles de {nombre_cat}.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_in, col_out = st.columns(2)
    
    # --- PANEL 1: REGISTRAR ENTRADA (ADMIN) ---
    with col_in:
        with st.container():
            st.markdown("### 📥 Recepción de Mercancía")
            st.caption("Acceso exclusivo para administradores")
            
            clave = st.text_input("🔑 Clave de Autorización", type="password", key=f"pass_{nombre_cat}")
            
            if clave == CLAVE_ADMIN:
                st.success("🔓 Sesión de administrador activa")
                with st.form(key=f"form_sumar_{nombre_cat}"):
                    cant_sumar = st.number_input("Cantidad que ingresa", min_value=0, step=1)
                    nuevo_precio = st.number_input("Precio Unitario ($)", min_value=0.0, value=precio_actual, step=5.0)
                    
                    if st.form_submit_button("➕ GUARDAR E INCREMENTAR STOCK"):
                        idx = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()].index
                        if not idx.empty:
                            df_inv.loc[idx, "STOCK"] += cant_sumar
                            df_inv.loc[idx, "PRECIO"] = nuevo_precio
                            df_inv.to_csv(FILE_INV, index=False)
                        st.success("¡Inventario actualizado correctamente!")
                        st.rerun()
            elif clave != "":
                st.error("❌ Clave incorrecta")
            else:
                st.info("💡 Ingrese la clave para modificar inventario o precio.")

    # --- PANEL 2: REGISTRAR VENTA ---
    with col_out:
        with st.container():
            st.markdown("### 🛒 Registrar Nueva Venta")
            st.caption("Módulo para registro rápido de facturación")
            
            with st.form(key=f"form_venta_{nombre_cat}"):
                cant_vender = st.number_input("Cantidad Vendida", min_value=1, step=1)
                metodo_pago = st.selectbox("💳 Método de Pago", ["Efectivo", "Transferencia", "Tarjeta Débito/Crédito", "Crédito / Cuotas"])
                
                st.markdown("---")
                st.markdown("**👤 Información del Cliente**")
                c1, c2 = st.columns(2)
                cliente_nom = c1.text_input("Nombre y Apellido")
                cliente_ced = c2.text_input("Cédula / DNI")
                cliente_tel = c1.text_input("Teléfono de Contacto")
                cliente_cor = c2.text_input("Correo Electrónico")
                
                total_calculado = cant_vender * precio_actual
                
                st.markdown(f"""
                    <div style="background-color: #eef2f5; padding: 15px; border-radius: 10px; text-align: center; margin: 15px 0;">
                        <h3 style="margin:0; color: #1e3c72;">Total a Cobrar: <b>${total_calculado:,.2f}</b></h3>
                    </div>
                """, unsafe_allow_html=True)
                
                btn_vender = st.form_submit_button("🛍️ CONFIRMAR Y REGISTRAR VENTA")
                
                if btn_vender:
                    if cant_vender > stock_actual:
                        st.error(f"❌ Inventario insuficiente. Disponible: {stock_actual} unidades.")
                    elif cliente_nom.strip() == "":
                        st.warning("⚠️ El nombre del cliente es obligatorio.")
                    else:
                        # Actualizar stock
                        idx = df_inv[df_inv["CATEGORIA"].astype(str).str.upper() == nombre_cat.upper()].index
                        if not idx.empty:
                            df_inv.loc[idx, "STOCK"] -= cant_vender
                            df_inv.to_csv(FILE_INV, index=False)
                        
                        # Registrar transacción
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
                        
                        st.success(f"¡Venta confirmada a {cliente_nom} por ${total_calculado:,.2f}!")
                        st.rerun()

# Pestañas de la aplicación
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
    st.markdown("### 📜 Panel de Historial y Reportes Financieros")
    
    if os.path.exists(FILE_VENTAS):
        df_v_hist = pd.read_csv(FILE_VENTAS)
        
        if df_v_hist.empty:
            st.info("Aún no se han registrado ventas en el sistema.")
        else:
            # Resumen acumulado
            total_recaudado = df_v_hist["TOTAL"].sum() if "TOTAL" in df_v_hist.columns else 0
            
            k1, k2 = st.columns(2)
            k1.metric("💰 Recaudación Total", f"${total_recaudado:,.2f}")
            k2.metric("🛍️ Total Transacciones", f"{len(df_v_hist)} ventas")
            
            st.markdown("---")
            busqueda = st.text_input("🔍 Buscar venta por Cliente o Cédula:")
            
            if busqueda:
                df_filtrado = df_v_hist[
                    df_v_hist["CLIENTE"].astype(str).str.contains(busqueda, case=False, na=False) |
                    df_v_hist["CEDULA"].astype(str).str.contains(busqueda, case=False, na=False)
                ]
            else:
                df_filtrado = df_v_hist
                
            st.dataframe(df_filtrado, use_container_width=True)
            
            # Descargar Excel/CSV
            csv_data = df_v_hist.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 EXPORTAR REPORTE A EXCEL (CSV)",
                data=csv_data,
                file_name=f"ventas_camas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
    else:
        st.info("Aún no hay ventas registradas.")
