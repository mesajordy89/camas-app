import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuración de página
st.set_page_config(page_title="Local Mesitas - Sistema POS y Apartados", page_icon="🛏️", layout="wide")

CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1234"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"

# --- SISTEMA DE BLOQUEO CON CONTRASEÑA ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("""
        <style>
        .stApp { background-color: #0f2027; color: white; }
        .login-box {
            max-width: 400px;
            margin: 100px auto;
            padding: 30px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            backdrop-filter: blur(4px);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="login-box">
            <h2>🔐 Acceso Restringido</h2>
            <p style="color: #bbb;">Local Mesitas - Control Interno</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        passw = st.text_input("Ingresa la clave de acceso", type="password", key="input_pass_app")
        if st.button("🚀 INGRESAR AL SISTEMA"):
            if passw == CLAVE_ACCESO:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Clave incorrecta")
    st.stop()

# --- CARGAR O CREAR INVENTARIO ---
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

# --- CARGAR O CREAR VENTAS ---
if os.path.exists(FILE_VENTAS):
    df_ventas = pd.read_csv(FILE_VENTAS)
    if "ABONADO" not in df_ventas.columns:
        df_ventas["ABONADO"] = df_ventas["TOTAL"]
        df_ventas["SALDO_PENDIENTE"] = 0.0
        df_ventas["ESTADO"] = "Pagado y Entregado"
        df_ventas.to_csv(FILE_VENTAS, index=False)
else:
    df_ventas = pd.DataFrame(columns=[
        "FECHA", "CATEGORIA", "CANTIDAD", "PRECIO_UNITARIO", "TOTAL", 
        "ABONADO", "SALDO_PENDIENTE", "METODO_PAGO", "CLIENTE", "CEDULA", "TELEFONO", "CORREO", "ESTADO"
    ])
    df_ventas.to_csv(FILE_VENTAS, index=False)

# --- ESTILOS VISUALES PREMIUM ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    .header-box {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 25px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #1f4068 0%, #162447 100%);
        color: white;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
        height: 48px;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

col_title, col_logout = st.columns([6, 1])
with col_logout:
    if st.button("🔒 Salir"):
        st.session_state["autenticado"] = False
        st.rerun()

st.markdown("""
    <div class="header-box">
        <h1 style="color:white; margin:0; font-weight: 700;">🏪 Local Mesitas</h1>
        <p style="margin:8px 0 0 0; font-size: 16px; opacity: 0.85;">Sistema Rápido POS, Ventas y Apartados</p>
    </div>
""", unsafe_allow_html=True)

# Alerta de stock bajo
stock_critico = df_inv[df_inv["STOCK"] <= 2]
if not stock_critico.empty:
    productos_bajos = ", ".join([f"**{row['CATEGORIA']}** ({row['STOCK']} ud.)" for _, row in stock_critico.iterrows()])
    st.warning(f"🚨 **ATENCIÓN - STOCK BAJO:** {productos_bajos}. ¡Reabastece pronto!")

tab_ops, tab_apartados, tab_inventario, tab_historial = st.tabs([
    "⚡ Venta Directa", 
    "📦 Apartados y Abonos", 
    "🛠️ Inventario", 
    "📜 Historial y Caja"
])

# ================= TAB 1: VENTA DIRECTA =================
with tab_ops:
    st.markdown("### ⚡ Venta Rápida (Pago Total e Inmediato)")
    
    if df_inv.empty:
        st.info("No hay productos en el inventario.")
    else:
        # Mostramos inventario rápido arriba
        cols = st.columns(len(df_inv))
        iconos = {"Camas": "🛏️", "Colchones": "💤", "Armarios": "🚪", "Pajaritas": "🎀"}
        for idx, row in df_inv.iterrows():
            cat = row["CATEGORIA"]
            cols[idx].metric(label=f"{iconos.get(cat, '📦')} {cat}", value=f"{int(row['STOCK'])} ud", delta=f"${row['PRECIO']:,.2f}")

        st.markdown("---")
        categoria_sel = st.selectbox("Selecciona el Producto", df_inv["CATEGORIA"].tolist(), key="v_cat")
        row_sel = df_inv[df_inv["CATEGORIA"] == categoria_sel].iloc[0]
        stock_disp = int(row_sel["STOCK"])
        precio_unit = float(row_sel["PRECIO"])
        
        with st.form("form_venta_rapida"):
            c1, c2 = st.columns(2)
            cant = c1.number_input("Cantidad", min_value=1, value=1, step=1)
            pago = c2.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
            
            cliente = st.text_input("Nombre del Cliente", value="Cliente General")
            celda = st.text_input("Cédula / Teléfono", value="S/N")
            
            total = cant * precio_unit
            st.markdown(f"### Total a Cobrar: ${total:,.2f}")
            
            if st.form_submit_button("💰 COBRAR Y ENTREGAR INMEDIATAMENTE"):
                if cant > stock_disp:
                    st.error(f"❌ Stock insuficiente. Solo hay {stock_disp} unidades.")
                else:
                    df_inv.loc[df_inv["CATEGORIA"] == categoria_sel, "STOCK"] -= cant
                    df_inv.to_csv(FILE_INV, index=False)
                    
                    nueva = pd.DataFrame([{
                        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "CATEGORIA": categoria_sel, "CANTIDAD": cant, "PRECIO_UNITARIO": precio_unit,
                        "TOTAL": total, "ABONADO": total, "SALDO_PENDIENTE": 0.0,
                        "METODO_PAGO": pago, "CLIENTE": cliente, "CEDULA": celda,
                        "TELEFONO": "", "CORREO": "", "ESTADO": "Pagado y Entregado"
                    }])
                    pd.concat([pd.read_csv(FILE_VENTAS), nueva], ignore_index=True).to_csv(FILE_VENTAS, index=False)
                    st.success("¡Venta procesada y stock descontado con éxito!")
                    st.rerun()

# ================= TAB 2: APARTADOS Y ABONOS (SUPER FÁCIL) =================
with tab_apartados:
    st.markdown("### 📦 Gestión de Apartados y Clientes")
    
    # Botón desplegable o sección limpia para crear apartado nuevo directamente aquí
    with st.expander("➕ CREAR NUEVO APARTADO (Hacer clic para abrir)", expanded=True):
        if not df_inv.empty:
            with st.form("form_nuevo_ap"):
                ap_cat = st.selectbox("Producto a Apartar", df_inv["CATEGORIA"].tolist())
                p_info = df_inv[df_inv["CATEGORIA"] == ap_cat].iloc[0]
                
                c_a1, c_a2 = st.columns(2)
                ap_cant = c_a1.number_input("Cantidad", min_value=1, value=1)
                ap_abono = c_a2.number_input("Dinero que deja abonando hoy ($)", min_value=0.0, value=10.0, step=5.0)
                
                ap_cliente = st.text_input("Nombre y Apellido del Cliente")
                ap_cel = st.text_input("Teléfono o Cédula")
                
                precio_p = float(p_info["PRECIO"])
                tot_p = ap_cant * precio_p
                saldo_p = tot_p - ap_abono
                
                st.info(f"Valor Total: ${tot_p:,.2f} | Abonando hoy: ${ap_abono:,.2f} | **Falta pagar: ${saldo_p:,.2f}**")
                
                if st.form_submit_button("💾 GUARDAR APARTADO EN BODEGA"):
                    if ap_cliente.strip() == "":
                        st.warning("Por favor ingresa el nombre del cliente.")
                    else:
                        nuevo_ap = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "CATEGORIA": ap_cat, "CANTIDAD": ap_cant, "PRECIO_UNITARIO": precio_p,
                            "TOTAL": tot_p, "ABONADO": ap_abono, "SALDO_PENDIENTE": max(0.0, saldo_p),
                            "METODO_PAGO": "Efectivo", "CLIENTE": ap_cliente, "CEDULA": ap_cel,
                            "TELEFONO": "", "CORREO": "", 
                            "ESTADO": "Pagado y Entregado" if saldo_p <= 0 else "Apartado (Pendiente)"
                        }])
                        
                        # Si por coincidencia pagó todo de una vez
                        if saldo_p <= 0:
                            df_inv.loc[df_inv["CATEGORIA"] == ap_cat, "STOCK"] -= ap_cant
                            df_inv.to_csv(FILE_INV, index=False)
                            st.success("¡El cliente pagó el total de inmediato, producto entregado!")
                        else:
                            st.success(f"¡Apartado guardado para {ap_cliente}! Quedó guardado en bodega.")
                            
                        pd.concat([pd.read_csv(FILE_VENTAS), nuevo_ap], ignore_index=True).to_csv(FILE_VENTAS, index=False)
                        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Listado de Apartados Activos y Abonos")
    
    df_v = pd.read_csv(FILE_VENTAS) if os.path.exists(FILE_VENTAS) else pd.DataFrame()
    if not df_v.empty and "ESTADO" in df_v.columns:
        pendientes = df_v[df_v["ESTADO"].str.contains("Apartado", case=False, na=False)]
        
        # Mensaje de éxito si alguien terminó de pagar
        if "msg_exito" in st.session_state:
            st.markdown(st.session_state["msg_exito"], unsafe_allow_html=True)
            if st.button("✖️ Cerrar aviso"):
                del st.session_state["msg_exito"]
                st.rerun()

        if pendientes.empty:
            st.success("✨ ¡No hay apartados pendientes en este momento!")
        else:
            # Mostramos una tabla bonita y limpia para identificar rápido
            st.dataframe(pendientes[["CLIENTE", "CATEGORIA", "CANTIDAD", "TOTAL", "ABONADO", "SALDO_PENDIENTE"]], use_container_width=True)
            
            st.markdown("#### 💸 Registrar Abono a un Cliente")
            ops = [f"Fila {i} | Cliente: {r['CLIENTE']} | Producto: {r['CATEGORIA']} | Debe: ${r['SALDO_PENDIENTE']}" for i, r in pendientes.iterrows()]
            elegido = st.selectbox("Selecciona al cliente que vino a abonar", ops)
            
            with st.form("form_dar_abono"):
                i_idx = int(elegido.split(" | ")[0].replace("Fila ", ""))
                c_nom = df_v.loc[i_idx, "CLIENTE"]
                c_prod = df_v.loc[i_idx, "CATEGORIA"]
                c_debe = float(df_v.loc[i_idx, "SALDO_PENDIENTE"])
                
                cant_abonar = st.number_input(f"¿Cuánto dinero trae {c_nom} hoy? ($)", min_value=0.0, max_value=c_debe, value=c_debe, step=5.0)
                
                if st.form_submit_button("📥 REGISTRAR ABONO"):
                    nuevo_abonado = float(df_v.loc[i_idx, "ABONADO"]) + cant_abonar
                    nuevo_saldo = float(df_v.loc[i_idx, "SALDO_PENDIENTE"]) - cant_abonar
                    
                    df_v.loc[i_idx, "ABONADO"] = nuevo_abonado
                    df_v.loc[i_idx, "SALDO_PENDIENTE"] = max(0.0, nuevo_saldo)
                    
                    if nuevo_saldo <= 0:
                        df_v.loc[i_idx, "ESTADO"] = "Pagado y Entregado"
                        cant_entregar = int(df_v.loc[i_idx, "CANTIDAD"])
                        
                        if c_prod in df_inv["CATEGORIA"].values:
                            df_inv.loc[df_inv["CATEGORIA"] == c_prod, "STOCK"] -= cant_entregar
                            df_inv.to_csv(FILE_INV, index=False)
                            
                        st.session_state["msg_exito"] = f"""
                            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 25px; border-radius: 14px; text-align: center; color: white; margin: 15px 0;">
                                <h1 style="margin:0; font-size: 26px;">🎉 ¡FELICIDADES!</h1>
                                <h3 style="margin:10px 0;">EL CLIENTE <b>{c_nom.upper()}</b> ACABÓ SU PAGO.</h3>
                                <p style="font-size: 18px; margin:0;">📦 <b>ENTREGUE EL PRODUCTO:</b> {cant_entregar}x {c_prod}</p>
                            </div>
                        """
                    else:
                        st.success(f"¡Abono registrado con éxito! Saldo restante: ${nuevo_saldo:,.2f}")
                        
                    df_v.to_csv(FILE_VENTAS, index=False)
                    st.rerun()

# ================= TAB 3: INVENTARIO =================
with tab_inventario:
    st.markdown("### 🛠️ Inventario (Protegido)")
    pass_inv = st.text_input("Clave de Administrador", type="password", key="p_inv")
    if pass_inv == CLAVE_ADMIN:
        st.success("Acceso concedido")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Modificar Stock")
            if not df_inv.empty:
                prod_m = st.selectbox("Producto", df_inv["CATEGORIA"].tolist())
                act_s = st.number_input("Sumar / Restar stock (+ o -)", value=0, step=1)
                nue_p = st.number_input("Nuevo Precio ($)", value=float(df_inv[df_inv["CATEGORIA"] == prod_m]["PRECIO"].values[0]))
                if st.button("Actualizar Stock"):
                    idx = df_inv[df_inv["CATEGORIA"] == prod_m].index[0]
                    df_inv.loc[idx, "STOCK"] = max(0, int(df_inv.loc[idx, "STOCK"]) + act_s)
                    df_inv.loc[idx, "PRECIO"] = nue_p
                    df_inv.to_csv(FILE_INV, index=False)
                    st.success("¡Actualizado!")
                    st.rerun()
        with c2:
            st.markdown("#### Añadir Producto Nuevo")
            n_nom = st.text_input("Nombre del producto")
            n_stk = st.number_input("Stock inicial", min_value=0, value=5)
            n_prc = st.number_input("Precio ($)", min_value=0.0, value=50.0)
            if st.button("Crear Producto"):
                if n_nom.strip() != "":
                    nuevo_reg = pd.DataFrame([{"CATEGORIA": n_nom.capitalize(), "STOCK": n_stk, "PRECIO": n_prc}])
                    pd.concat([df_inv, nuevo_reg], ignore_index=True).to_csv(FILE_INV, index=False)
                    st.success("¡Creado!")
                    st.rerun()
    elif pass_inv != "":
        st.error("Clave incorrecta")

# ================= TAB 4: HISTORIAL Y CAJA =================
with tab_historial:
    st.markdown("### 📜 Cierre de Caja y Registros")
    if os.path.exists(FILE_VENTAS):
        df_h = pd.read_csv(FILE_VENTAS)
        if not df_h.empty:
            total_caja = df_h["ABONADO"].sum() if "ABONADO" in df_h.columns else df_h["TOTAL"].sum()
            st.metric("💵 Total Dinero Recibido (Ventas + Abonos)", f"${total_caja:,.2f}")
            st.dataframe(df_h, use_container_width=True)
            
            if st.button("📥 Descargar Reporte CSV"):
                st.download_button("Descargar", df_h.to_csv(index=False).encode('utf-8'), "reporte.csv", "text/csv")
