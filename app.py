from datetime import datetime
import os
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (MOBILE-FIRST)
# ==============================================================================
st.set_page_config(
    page_title="Local Mesitas - POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inyección de CSS para diseño móvil y colores llamativos
st.markdown("""
<style>
    /* Estilos generales */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Botones principales de gran tamaño */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
        background-color: #2E7D32 !important;
        color: white !important;
        border: none;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover {
        background-color: #1B5E20 !important;
    }

    /* Tarjetas de productos y ventas */
    .card-mobile {
        background-color: #FFFFFF;
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 12px;
        border-left: 6px solid #2E7D32;
    }
    
    .card-warning {
        border-left-color: #D32F2F !important;
        background-color: #FFEBEE;
    }

    .badge-ok {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
    }

    .badge-alert {
        background-color: #FFEBEE;
        color: #C62828;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
    }

    /* Pestañas grandes para celular */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Constantes de credenciales
CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1999"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"

# ==============================================================================
# FUNCIONES DE PERSISTENCIA (CSV)
# ==============================================================================

def cargar_inventario():
    if os.path.exists(FILE_INV):
        df = pd.read_csv(FILE_INV)
        df["Precio"] = pd.to_numeric(df["Precio"], errors="coerce").fillna(0)
        df["Stock"] = pd.to_numeric(df["Stock"], errors="coerce").fillna(0).astype(int)
        if "Tipo" not in df.columns:
            df["Tipo"] = "Producto"
        return df
    else:
        return pd.DataFrame({
            "ID": [101, 102, 201, 202],
            "Nombre": ["Cama Sencilla Madera", "Cama Doble Acolchada", "Colchón Sencillo Resortes", "Colchón Doble Ortopédico"],
            "Tipo": ["Cama", "Cama", "Colchon", "Colchon"],
            "Precio": [450000.0, 750000.0, 300000.0, 500000.0],
            "Stock": [5, 3, 8, 1]
        })

def guardar_inventario(df):
    df.to_csv(FILE_INV, index=False)

def cargar_ventas():
    if os.path.exists(FILE_VENTAS):
        df = pd.read_csv(FILE_VENTAS)
        df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
        df["Abono"] = pd.to_numeric(df["Abono"], errors="coerce").fillna(0)
        df["Saldo"] = pd.to_numeric(df["Saldo"], errors="coerce").fillna(0)
        return df
    else:
        return pd.DataFrame(columns=[
            "ID_Venta", "Fecha", "Cliente", "Telefono", "Tipo_Venta",
            "Detalle", "Total", "Abono", "Saldo", "Estado", "Metodo_Pago"
        ])

def guardar_ventas(df):
    df.to_csv(FILE_VENTAS, index=False)

# ==============================================================================
# CONTROL DE SESIÓN
# ==============================================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center;'>🔐 Local Mesitas POS</h2>", unsafe_allow_html=True)
    clave = st.text_input("Ingresa tu PIN de acceso:", type="password")
    if st.button("🔓 INGRESAR AL SISTEMA", use_container_width=True):
        if clave in [CLAVE_ACCESO, CLAVE_ADMIN]:
            st.session_state.autenticado = True
            st.session_state.es_admin = (clave == CLAVE_ADMIN)
            st.rerun()
        else:
            st.error("PIN incorrecto. Intenta de nuevo.")
    st.stop()

# ==============================================================================
# INTERFAZ PRINCIPAL
# ==============================================================================

df_inv = cargar_inventario()
df_ventas = cargar_ventas()

st.markdown("<h3 style='text-align: center; color: #1B5E20;'>🛏️ LOCAL MESITAS - POS</h3>", unsafe_allow_html=True)

tabs = st.tabs(["🛒 VENDER", "📦 INVENTARIO", "📋 APARTADOS", "⚙️ ADMIN"])

# ------------------------------------------------------------------------------
# TAB 1: REGISTRO RÁPIDO DE VENTA
# ------------------------------------------------------------------------------
with tabs[0]:
    st.subheader("📱 Nueva Transacción")
    
    tipo_transaccion = st.radio("Tipo de Operación:", ["Venta Directa", "Combo (Cama + Colchón)", "Apartado"], horizontal=True)
    
    st.markdown("---")
    
    cliente = st.text_input("👤 Nombre del Cliente")
    telefono = st.text_input("📞 WhatsApp / Teléfono")
    metodo_pago = st.selectbox("💳 Método de Pago", ["Efectivo", "Nequi/Daviplata", "Transferencia", "Tarjeta"])

    cama_sel, colchon_sel, prod_sel = "", "", ""
    cant = 1
    total_calculado = 0.0

    if tipo_transaccion == "Combo (Cama + Colchón)":
        st.markdown("### 🛏️ + 🛌 Configurar Combo")
        camas_disponibles = df_inv[(df_inv["Tipo"] == "Cama") & (df_inv["Stock"] > 0)]
        colchones_disponibles = df_inv[(df_inv["Tipo"] == "Colchon") & (df_inv["Stock"] > 0)]
        
        cama_sel = st.selectbox("Selecciona Cama", camas_disponibles["Nombre"].tolist() if not camas_disponibles.empty else ["Sin Stock"])
        colchon_sel = st.selectbox("Selecciona Colchón", colchones_disponibles["Nombre"].tolist() if not colchones_disponibles.empty else ["Sin Stock"])
        
        p_cama = camas_disponibles[camas_disponibles["Nombre"] == cama_sel]["Precio"].values[0] if cama_sel in camas_disponibles["Nombre"].values else 0
        p_colchon = colchones_disponibles[colchones_disponibles["Nombre"] == colchon_sel]["Precio"].values[0] if colchon_sel in colchones_disponibles["Nombre"].values else 0
        
        descuento = st.number_input("Descuento Combo ($)", min_value=0.0, step=5000.0)
        total_calculado = max(0.0, (p_cama + p_colchon) - descuento)

    else:
        st.markdown("### 📦 Seleccionar Producto")
        prods_disponibles = df_inv[df_inv["Stock"] > 0]
        prod_sel = st.selectbox("Producto", prods_disponibles["Nombre"].tolist() if not prods_disponibles.empty else ["Sin Stock"])
        cant = st.number_input("Cantidad", min_value=1, value=1)
        
        p_unit = prods_disponibles[prods_disponibles["Nombre"] == prod_sel]["Precio"].values[0] if prod_sel in prods_disponibles["Nombre"].values else 0
        total_calculado = p_unit * cant

    abono = total_calculado
    saldo = 0.0

    if tipo_transaccion == "Apartado":
        abono = st.number_input("Abono Inicial ($)", min_value=0.0, max_value=float(total_calculado), step=10000.0)
        saldo = total_calculado - abono

    st.markdown(f"""
    <div class="card-mobile">
        <h4 style="margin:0; color:#1B5E20;">Total a Cobrar: ${total_calculado:,.0f}</h4>
        <p style="margin:0; color:#555;">Abono: ${abono:,.0f} | Saldo: <b>${saldo:,.0f}</b></p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("✅ FINALIZAR Y REGISTRAR", use_container_width=True):
        if not cliente:
            st.error("Por favor ingresa el nombre del cliente.")
        else:
            nueva_venta = {
                "ID_Venta": len(df_ventas) + 1,
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Cliente": cliente,
                "Telefono": telefono,
                "Tipo_Venta": tipo_transaccion,
                "Detalle": f"{cama_sel} + {colchon_sel}" if tipo_transaccion == "Combo (Cama + Colchón)" else f"{prod_sel} (x{cant})",
                "Total": total_calculado,
                "Abono": abono,
                "Saldo": saldo,
                "Estado": "Completado" if saldo == 0 else "Pendiente",
                "Metodo_Pago": metodo_pago
            }
            
            # Descontar inventario
            if tipo_transaccion == "Combo (Cama + Colchón)":
                df_inv.loc[df_inv["Nombre"] == cama_sel, "Stock"] -= 1
                df_inv.loc[df_inv["Nombre"] == colchon_sel, "Stock"] -= 1
            else:
                df_inv.loc[df_inv["Nombre"] == prod_sel, "Stock"] -= cant
                
            guardar_inventario(df_inv)
            df_ventas = pd.concat([df_ventas, pd.DataFrame([nueva_venta])], ignore_index=True)
            guardar_ventas(df_ventas)
            
            st.balloons()
            st.success("¡Venta registrada con éxito!")
            
            msj_wa = f"Hola {cliente}, confirmamos tu compra en Local Mesitas:\n📌 Detalle: {nueva_venta['Detalle']}\n💵 Total: ${total_calculado:,.0f}\n✅ Abono: ${abono:,.0f}\n📌 Saldo: ${saldo:,.0f}"
            url_wa = f"https://wa.me/{telefono}?text={urllib.parse.quote(msj_wa)}"
            st.markdown(f'<a href="{url_wa}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#25D366 !important; color:white; border-radius:12px; height:3em; font-weight:bold; border:none;">📲 ENVIAR COMPROBANTE WHATSAPP</button></a>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2: INVENTARIO VISUAL
# ------------------------------------------------------------------------------
with tabs[1]:
    st.subheader("📦 Estado del Inventario")
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Productos", len(df_inv))
    col_m2.metric("Bajos en Stock", len(df_inv[df_inv["Stock"] <= 2]))

    st.markdown("---")
    
    for _, row in df_inv.iterrows():
        alerta = row["Stock"] <= 2
        clase_card = "card-warning" if alerta else "card-mobile"
        badge = f'<span class="badge-alert">AGOTÁNDOSE ({row["Stock"]})</span>' if alerta else f'<span class="badge-ok">Stock: {row["Stock"]}</span>'
        
        st.markdown(f"""
        <div class="{clase_card}">
            <div style="display:flex; justify-shadow:space-between; align-items:center;">
                <h4 style="margin:0; font-size:16px;">{row['Nombre']}</h4>
                {badge}
            </div>
            <p style="margin:5px 0 0 0; color:#666;">Categoría: {row['Tipo']} | <b>${row['Precio']:,.0f}</b></p>
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 3: CONTROL DE APARTADOS
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("📋 Registro de Apartados")
    
    pendientes = df_ventas[df_ventas["Estado"] == "Pendiente"]
    
    if pendientes.empty:
        st.info("No hay apartados pendientes por cobrar.")
    else:
        for _, row in pendientes.iterrows():
            st.markdown(f"""
            <div class="card-mobile">
                <h4 style="margin:0; color:#D32F2F;">Cliente: {row['Cliente']}</h4>
                <p style="margin:4px 0;">Detalle: {row['Detalle']}</p>
                <p style="margin:4px 0;">Total: ${row['Total']:,.0f} | Abono: ${row['Abono']:,.0f}</p>
                <h4 style="margin:4px 0; color:#2E7D32;">Pendiente: ${row['Saldo']:,.0f}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"💵 Abonar a Venta #{row['ID_Venta']}"):
                monto_abono = st.number_input(f"Monto a abonar (#{row['ID_Venta']})", min_value=0.0, max_value=float(row["Saldo"]), step=5000.0, key=f"ab_{row['ID_Venta']}")
                if st.button(f"REGISTRAR ABONO #{row['ID_Venta']}", use_container_width=True):
                    idx = df_ventas[df_ventas["ID_Venta"] == row["ID_Venta"]].index[0]
                    df_ventas.at[idx, "Abono"] += monto_abono
                    df_ventas.at[idx, "Saldo"] -= monto_abono
                    if df_ventas.at[idx, "Saldo"] == 0:
                        df_ventas.at[idx, "Estado"] = "Completado"
                    guardar_ventas(df_ventas)
                    st.success("Abono procesado correctamente.")
                    st.rerun()

# ------------------------------------------------------------------------------
# TAB 4: ADMINISTRACIÓN
# ------------------------------------------------------------------------------
with tabs[3]:
    st.subheader("⚙️ Configuración")
    pin_admin = st.text_input("Ingrese PIN Administrador", type="password")
    
    if pin_admin == CLAVE_ADMIN:
        st.success("Acceso Administrador Activo")
        
        with st.form("form_nuevo_prod"):
            st.markdown("### ➕ Añadir / Editar Producto")
            id_p = st.number_input("ID Producto", min_value=1, value=100)
            nombre_p = st.text_input("Nombre del Producto")
            tipo_p = st.selectbox("Categoría", ["Cama", "Colchon", "Producto"])
            precio_p = st.number_input("Precio ($)", min_value=0.0, step=10000.0)
            stock_p = st.number_input("Stock Inicial", min_value=0, value=1)
            
            if st.form_submit_button("GUARDAR EN INVENTARIO"):
                if id_p in df_inv["ID"].values:
                    df_inv.loc[df_inv["ID"] == id_p, ["Nombre", "Tipo", "Precio", "Stock"]] = [nombre_p, tipo_p, precio_p, stock_p]
                else:
                    nuevo_p = pd.DataFrame([{"ID": id_p, "Nombre": nombre_p, "Tipo": tipo_p, "Precio": precio_p, "Stock": stock_p}])
                    df_inv = pd.concat([df_inv, nuevo_p], ignore_index=True)
                guardar_inventario(df_inv)
                st.success("Producto guardado correctamente.")
                st.rerun()
    elif pin_admin:
        st.error("PIN incorrecto.")
