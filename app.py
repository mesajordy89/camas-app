import os
import smtplib
import textwrap
import urllib.parse
from datetime import datetime
from email.message import EmailMessage
import mimetypes

import pandas as pd
import streamlit as st

# ==============================================================================
# LOCAL MESITAS - SISTEMA POS
# ==============================================================================

st.set_page_config(
    page_title="Local Mesitas - Sistema POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Constantes de credenciales
CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1999"  # <--- Contraseña de administrador configurada a 1999

NUMERO_1 = "573100000000"
NUMERO_2 = "573200000000"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"
CARPETA_FOTOS = "fotos_productos"

if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)

# ==============================================================================
# FUNCIONES DE BASE DE DATOS Y PERSISTENCIA (CSV)
# ==============================================================================

def cargar_inventario():
    if os.path.exists(FILE_INV):
        df = pd.read_csv(FILE_INV)
        df["Precio"] = pd.to_numeric(df["Precio"], errors="coerce").fillna(0)
        df["Stock"] = pd.to_numeric(df["Stock"], errors="coerce").fillna(0).astype(int)
        if "Tipo" not in df.columns:
            df["Tipo"] = "Producto"
        if "Foto" not in df.columns:
            df["Foto"] = ""
        return df
    else:
        return pd.DataFrame({
            "ID": [101, 102, 201, 202],
            "Nombre": ["Cama Sencilla Madera", "Cama Doble Acolchada", "Colchón Sencillo Resortes", "Colchón Doble Ortopédico"],
            "Tipo": ["Cama", "Cama", "Colchon", "Colchon"],
            "Precio": [450000.0, 750000.0, 300000.0, 500000.0],
            "Stock": [5, 3, 8, 4],
            "Foto": ["", "", "", ""]
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

def enviar_correo_factura(destinatario, asunto, cuerpo):
    try:
        msg = EmailMessage()
        msg.set_content(cuerpo)
        msg['Subject'] = asunto
        msg['From'] = "tu_correo@gmail.com"
        msg['To'] = destinatario
        
        # Configurar servidor SMTP (Ejemplo Gmail - requiere contraseña de aplicación)
        # with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        #     smtp.login("tu_correo@gmail.com", "tu_password_app")
        #     smtp.send_message(msg)
        return True
    except Exception as e:
        return False

# ==============================================================================
# CONTROL DE SESIÓN Y LOGIN
# ==============================================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso al Sistema - Local Mesitas")
    clave = st.text_input("Ingrese la clave de acceso:", type="password")
    if st.button("Ingresar"):
        if clave == CLAVE_ACCESO or clave == CLAVE_ADMIN:
            st.session_state.autenticado = True
            st.session_state.es_admin = (clave == CLAVE_ADMIN)
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# ==============================================================================
# INTERFAZ PRINCIPAL
# ==============================================================================

df_inv = cargar_inventario()
df_ventas = cargar_ventas()

st.title("🛏️ Local Mesitas - Sistema POS")

tabs = st.tabs(["🛒 Nueva Venta / Combo", "📦 Inventario", "📋 Apartados y Ventas", "⚙️ Administración"])

# ------------------------------------------------------------------------------
# TAB 1: NUEVA VENTA / COMBO
# ------------------------------------------------------------------------------
with tabs[0]:
    st.header("Registrar Transacción")
    col1, col2 = st.columns(2)
    
    with col1:
        cliente = st.text_input("Nombre del Cliente")
        telefono = st.text_input("Teléfono / WhatsApp")
        metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Nequi/Daviplata", "Transferencia", "Tarjeta"])
        
    with col2:
        tipo_transaccion = st.radio("Tipo de Operación", ["Venta Directa", "Combo (Cama + Colchón)", "Apartado"])
    
    st.divider()
    
    if tipo_transaccion == "Combo (Cama + Colchón)":
        st.subheader("Selección de Combo")
        camas_disponibles = df_inv[(df_inv["Tipo"] == "Cama") & (df_inv["Stock"] > 0)]
        colchones_disponibles = df_inv[(df_inv["Tipo"] == "Colchon") & (df_inv["Stock"] > 0)]
        
        cama_sel = st.selectbox("Seleccione Cama", camas_disponibles["Nombre"].tolist() if not camas_disponibles.empty else [])
        colchon_sel = st.selectbox("Seleccione Colchón", colchones_disponibles["Nombre"].tolist() if not colchones_disponibles.empty else [])
        
        precio_cama = camas_disponibles[camas_disponibles["Nombre"] == cama_sel]["Precio"].values[0] if cama_sel else 0
        precio_colchon = colchones_disponibles[colchones_disponibles["Nombre"] == colchon_sel]["Precio"].values[0] if colchon_sel else 0
        
        descuento = st.number_input("Descuento Combo ($)", min_value=0.0, value=0.0)
        total_calculado = (precio_cama + precio_colchon) - descuento
        st.write(f"**Total Combo:** ${total_calculado:,.2f}")
        
    else:
        st.subheader("Selección de Producto")
        prods_disponibles = df_inv[df_inv["Stock"] > 0]
        prod_sel = st.selectbox("Producto", prods_disponibles["Nombre"].tolist() if not prods_disponibles.empty else [])
        cant = st.number_input("Cantidad", min_value=1, value=1)
        
        precio_unit = prods_disponibles[prods_disponibles["Nombre"] == prod_sel]["Precio"].values[0] if prod_sel else 0
        total_calculado = precio_unit * cant
        st.write(f"**Total:** ${total_calculado:,.2f}")

    abono = 0.0
    if tipo_transaccion == "Apartado":
        abono = st.number_input("Abono Inicial ($)", min_value=0.0, max_value=float(total_calculado), value=0.0)
        saldo = total_calculado - abono
        st.write(f"**Saldo Pendiente:** ${saldo:,.2f}")
    else:
        abono = total_calculado
        saldo = 0.0

    if st.button("Procesar Transacción"):
        if not cliente:
            st.warning("Ingrese el nombre del cliente.")
        else:
            # Registrar venta
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
            
            # Descontar Stock
            if tipo_transaccion == "Combo (Cama + Colchón)":
                df_inv.loc[df_inv["Nombre"] == cama_sel, "Stock"] -= 1
                df_inv.loc[df_inv["Nombre"] == colchon_sel, "Stock"] -= 1
            else:
                df_inv.loc[df_inv["Nombre"] == prod_sel, "Stock"] -= cant
                
            guardar_inventario(df_inv)
            df_ventas = pd.concat([df_ventas, pd.DataFrame([nueva_venta])], ignore_index=True)
            guardar_ventas(df_ventas)
            
            st.success("Transacción registrada con éxito.")
            
            # Generar Link WhatsApp
            msj_wa = f"Hola {cliente}, confirmamos tu registro en Local Mesitas:\nOperación: {tipo_transaccion}\nTotal: ${total_calculado:,.2f}\nAbono: ${abono:,.2f}\nSaldo: ${saldo:,.2f}"
            url_wa = f"https://wa.me/{telefono}?text={urllib.parse.quote(msj_wa)}"
            st.markdown(f"[📲 Enviar Comprobante por WhatsApp]({url_wa})")

# ------------------------------------------------------------------------------
# TAB 2: INVENTARIO
# ------------------------------------------------------------------------------
with tabs[1]:
    st.header("Estado del Inventario")
    
    # Alertas de Stock Bajo
    stock_bajo = df_inv[df_inv["Stock"] <= 2]
    if not stock_bajo.empty:
        st.warning("⚠️ **Atención:** Hay productos con stock bajo o agotado:")
        st.dataframe(stock_bajo[["ID", "Nombre", "Stock"]])
        
    st.dataframe(df_inv, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: APARTADOS Y VENTAS
# ------------------------------------------------------------------------------
with tabs[2]:
    st.header("Histórico de Ventas y Apartados")
    st.dataframe(df_ventas, use_container_width=True)
    
    st.subheader("Registrar Abono a Apartado")
    pendientes = df_ventas[df_ventas["Estado"] == "Pendiente"]
    if not pendientes.empty:
        venta_id = st.selectbox("Seleccionar Venta Pendiente", pendientes["ID_Venta"].tolist())
        v_row = pendientes[pendientes["ID_Venta"] == venta_id].iloc[0]
        
        st.write(f"Cliente: {v_row['Cliente']} | Saldo Actual: ${v_row['Saldo']:,.2f}")
        nuevo_abono = st.number_input("Monto del Abono ($)", min_value=0.0, max_value=float(v_row['Saldo']), value=0.0)
        
        if st.button("Aplicar Abono"):
            idx = df_ventas[df_ventas["ID_Venta"] == venta_id].index[0]
            df_ventas.at[idx, "Abono"] += nuevo_abono
            df_ventas.at[idx, "Saldo"] -= nuevo_abono
            if df_ventas.at[idx, "Saldo"] == 0:
                df_ventas.at[idx, "Estado"] = "Completado"
            guardar_ventas(df_ventas)
            st.success("Abono registrado correctamente.")
            st.rerun()

# ------------------------------------------------------------------------------
# TAB 4: ADMINISTRACIÓN
# ------------------------------------------------------------------------------
with tabs[3]:
    st.header("Panel de Administración")
    admin_clave = st.text_input("Ingrese la clave de administrador:", type="password")
    
    if admin_clave == CLAVE_ADMIN:
        st.success("Acceso de Administrador Concedido")
        
        st.subheader("Añadir / Modificar Producto")
        with st.form("form_producto"):
            id_p = st.number_input("ID Producto", min_value=1, value=100)
            nombre_p = st.text_input("Nombre")
            tipo_p = st.selectbox("Tipo", ["Cama", "Colchon", "Producto"])
            precio_p = st.number_input("Precio ($)", min_value=0.0, value=0.0)
            stock_p = st.number_input("Stock Inicial", min_value=0, value=1)
            
            submit = st.form_submit_button("Guardar Producto")
            if submit:
                if id_p in df_inv["ID"].values:
                    df_inv.loc[df_inv["ID"] == id_p, ["Nombre", "Tipo", "Precio", "Stock"]] = [nombre_p, tipo_p, precio_p, stock_p]
                else:
                    nuevo_p = pd.DataFrame([{"ID": id_p, "Nombre": nombre_p, "Tipo": tipo_p, "Precio": precio_p, "Stock": stock_p, "Foto": ""}])
                    df_inv = pd.concat([df_inv, nuevo_p], ignore_index=True)
                guardar_inventario(df_inv)
                st.success("Producto actualizado / guardado.")
                st.rerun()
    elif admin_clave:
        st.error("Clave de administración incorrecta.")
