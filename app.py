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
CARPETA_FOTOS = "fotos_ventas"

# Crear carpeta para guardar las fotos si no existe
if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)

# --- SISTEMA DE BLOQUEO CON CONTRASEÑA ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #1e1e2f 0%, #27293d 100%); color: white; }
        .login-box {
            max-width: 450px;
            margin: 100px auto;
            padding: 40px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="login-box">
            <h1 style="color: #ffaa00; margin-bottom: 10px;">🔐 Local Mesitas</h1>
            <p style="color: #bbb; font-size: 16px;">Ingrese su contraseña para acceder al sistema</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        passw = st.text_input("Contraseña", type="password", key="input_pass_app")
        if st.button("🚀 INGRESAR AL SISTEMA", use_container_width=True):
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
    if "DIRECCION" not in df_ventas.columns:
        df_ventas["DIRECCION"] = "S/N"
        df_ventas.to_csv(FILE_VENTAS, index=False)
    if "FOTO" not in df_ventas.columns:
        df_ventas["FOTO"] = "Sin foto"
        df_ventas.to_csv(FILE_VENTAS, index=False)
else:
    df_ventas = pd.DataFrame(columns=[
        "FECHA", "CATEGORIA", "CANTIDAD", "PRECIO_UNITARIO", "TOTAL", 
        "ABONADO", "SALDO_PENDIENTE", "METODO_PAGO", "CLIENTE", "CEDULA", 
        "TELEFONO", "CORREO", "DIRECCION", "ESTADO", "FOTO"
    ])
    df_ventas.to_csv(FILE_VENTAS, index=False)

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stApp { background-color: #f7f9fc; font-family: 'Segoe UI', Roboto, sans-serif; }
    
    .header-box {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px rgba(255, 65, 108, 0.3);
    }
    
    .card-resibo {
        background: white;
        padding: 25px;
        border-radius: 16px;
        border-left: 6px solid #ff416c;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border-radius: 12px;
        font-weight: 700;
        font-size: 16px;
        height: 55px;
        border: none;
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4);
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(17, 153, 142, 0.6);
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
        <h1 style="color:white; margin:0; font-size: 32px; font-weight: 800;">🏪 LOCAL MESITAS</h1>
        <p style="margin:10px 0 0 0; font-size: 18px; opacity: 0.9;">Sistema de Caja, Ventas, Apartados y Registro Fotográfico</p>
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
            
            cc1, cc2 = st.columns(2)
            celda = cc1.text_input("Cédula / RUC", value="S/N")
            telefono = cc2.text_input("Teléfono", value="")
            
            correo = st.text_input("Correo electrónico", value="")
            direccion = st.text_input("Dirección de Entrega", value="")
            
            foto_subida = st.file_uploader("📸 Subir Foto de la Cama o Producto (Opcional)", type=["jpg", "png", "jpeg"])
            
            total = cant * precio_unit
            st.markdown(f"### Total a Cobrar: ${total:,.2f}")
            
            if st.form_submit_button("💰 COBRAR Y GENERAR RECIBO DE VENTA"):
                if cant > stock_disp:
                    st.error(f"❌ Stock insuficiente. Solo hay {stock_disp} unidades.")
                else:
                    ruta_foto_guardada = "Sin foto"
                    if foto_subida is not None:
                        nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto_subida.name}"
                        ruta_foto_guardada = os.path.join(CARPETA_FOTOS, nombre_archivo)
                        with open(ruta_foto_guardada, "wb") as f:
                            f.write(foto_subida.getbuffer())

                    df_inv.loc[df_inv["CATEGORIA"] == categoria_sel, "STOCK"] -= cant
                    df_inv.to_csv(FILE_INV, index=False)
                    
                    df_actual_v = pd.read_csv(FILE_VENTAS)
                    if "FOTO" not in df_actual_v.columns:
                        df_actual_v["FOTO"] = "Sin foto"
                        
                    nueva = pd.DataFrame([{
                        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "CATEGORIA": categoria_sel, "CANTIDAD": cant, "PRECIO_UNITARIO": precio_unit,
                        "TOTAL": total, "ABONADO": total, "SALDO_PENDIENTE": 0.0,
                        "METODO_PAGO": pago, "CLIENTE": cliente, "CEDULA": celda,
                        "TELEFONO": telefono, "CORREO": correo, "DIRECCION": direccion, 
                        "ESTADO": "Pagado y Entregado", "FOTO": ruta_foto_guardada
                    }])
                    pd.concat([df_actual_v, nueva], ignore_index=True).to_csv(FILE_VENTAS, index=False)
                    st.success("¡Venta procesada con éxito y foto guardada!")
                    st.rerun()

# ================= TAB 2: APARTADOS Y ABONOS =================
with tab_apartados:
    st.markdown("### 📦 Gestión de Apartados y Clientes")
    
    with st.expander("➕ CREAR NUEVO APARTADO (Hacer clic para abrir formulario)", expanded=True):
        if not df_inv.empty:
            with st.form("form_nuevo_ap"):
                ap_cat = st.selectbox("Producto a Apartar", df_inv["CATEGORIA"].tolist())
                p_info = df_inv[df_inv["CATEGORIA"] == ap_cat].iloc[0]
                
                c_a1, c_a2 = st.columns(2)
                ap_cant = c_a1.number_input("Cantidad", min_value=1, value=1)
                ap_abono = c_a2.number_input("Dinero que deja abonando hoy ($)", min_value=0.0, value=10.0, step=5.0)
                
                ap_cliente = st.text_input("Nombre y Apellido del Cliente")
                
                c_inf1, c_inf2 = st.columns(2)
                ap_ced = c_inf1.text_input("Cédula / DNI")
                ap_tel = c_inf2.text_input("Teléfono de contacto")
                
                ap_corr = st.text_input("Correo electrónico")
                ap_dir = st.text_input("Dirección exacta")
                
                ap_foto = st.file_uploader("📸 Subir Foto de la Cama o Producto Apartado (Opcional)", type=["jpg", "png", "jpeg"], key="foto_ap")
                
                precio_p = float(p_info["PRECIO"])
                tot_p = ap_cant * precio_p
                saldo_p = tot_p - ap_abono
                
                st.info(f"💵 Valor Total: ${tot_p:,.2f} | 📥 Abono Hoy: ${ap_abono:,.2f} | 🔴 **Falta por pagar: ${saldo_p:,.2f}**")
                
                if st.form_submit_button("💾 GUARDAR APARTADO Y GENERAR RECIBO"):
                    if ap_cliente.strip() == "":
                        st.warning("Por favor ingresa el nombre del cliente.")
                    else:
                        ruta_foto_ap = "Sin foto"
                        if ap_foto is not None:
                            nombre_archivo = f"ap_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ap_foto.name}"
                            ruta_foto_ap = os.path.join(CARPETA_FOTOS, nombre_archivo)
                            with open(ruta_foto_ap, "wb") as f:
                                f.write(ap_foto.getbuffer())

                        df_actual_v = pd.read_csv(FILE_VENTAS)
                        if "FOTO" not in df_actual_v.columns:
                            df_actual_v["FOTO"] = "Sin foto"
                            
                        nuevo_ap = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "CATEGORIA": ap_cat, "CANTIDAD": ap_cant, "PRECIO_UNITARIO": precio_p,
                            "TOTAL": tot_p, "ABONADO": ap_abono, "SALDO_PENDIENTE": max(0.0, saldo_p),
                            "METODO_PAGO": "Efectivo", "CLIENTE": ap_cliente, "CEDULA": ap_ced,
                            "TELEFONO": ap_tel, "CORREO": ap_corr, "DIRECCION": ap_dir, 
                            "ESTADO": "Pagado y Entregado" if saldo_p <= 0 else "Apartado (Pendiente)",
                            "FOTO": ruta_foto_ap
                        }])
                        
                        if saldo_p <= 0:
                            df_inv.loc[df_inv["CATEGORIA"] == ap_cat, "STOCK"] -= ap_cant
                            df_inv.to_csv(FILE_INV, index=False)
                            st.success("¡El cliente pagó el total de inmediato!")
                        else:
                            st.success(f"¡Apartado guardado correctamente para {ap_cliente}!")
                            
                        pd.concat([df_actual_v, nuevo_ap], ignore_index=True).to_csv(FILE_VENTAS, index=False)
                        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Apartados Activos y Consulta de Recibos")
    
    df_v = pd.read_csv(FILE_VENTAS) if os.path.exists(FILE_VENTAS) else pd.DataFrame()
    if not df_v.empty and "ESTADO" in df_v.columns:
        if "DIRECCION" not in df_v.columns:
            df_v["DIRECCION"] = "S/N"
        if "FOTO" not in df_v.columns:
            df_v["FOTO"] = "Sin foto"
            
        pendientes = df_v[df_v["ESTADO"].str.contains("Apartado", case=False, na=False)]
        
        if "msg_exito" in st.session_state:
            st.markdown(st.session_state["msg_exito"], unsafe_allow_html=True)
            if st.button("✖️ Cerrar aviso de pago completo"):
                del st.session_state["msg_exito"]
                st.rerun()

        if pendientes.empty:
            st.success("✨ ¡No hay apartados pendientes en este momento!")
        else:
            lista_recibos = [f"Fila {i} ➔ Cliente: {r['CLIENTE']} | Producto: {r['CATEGORIA']} | Debe: ${r['SALDO_PENDIENTE']:,.2f}" for i, r in pendientes.iterrows()]
            recibo_sel = st.selectbox("🔍 Selecciona un apartado para ver su Recibo Detallado y abonar:", lista_recibos)
            
            if recibo_sel:
                idx_sel = int(recibo_sel.split(" ➔ ")[0].replace("Fila ", ""))
                r_data = df_v.loc[idx_sel]
                
                col_recibo_txt, col_recibo_img = st.columns([1.5, 1])
                
                with col_recibo_txt:
                    st.markdown(f"""
                        <div class="card-resibo">
                            <h2 style="color: #ff416c; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px;">🧾 RECIBO DE APARTADO</h2>
                            <p style="font-size: 15px; margin: 4px 0;"><b>📅 Fecha:</b> {r_data['FECHA']}</p>
                            <p style="font-size: 15px; margin: 4px 0;"><b>👤 Cliente:</b> {r_data['CLIENTE']}</p>
                            <p style="font-size: 15px; margin: 4px 0;"><b>📞 Teléfono:</b> {r_data['TELEFONO']} | <b>🆔 Cédula:</b> {r_data['CEDULA']}</p>
                            <p style="font-size: 15px; margin: 4px 0;"><b>📍 Dirección:</b> {r_data['DIRECCION']}</p>
                            <hr style="border: 0; border-top: 1px dashed #ccc; margin: 10px 0;">
                            <p style="font-size: 15px; margin: 4px 0;"><b>📦 Producto:</b> {r_data['CANTIDAD']}x {r_data['CATEGORIA']}</p>
                            <p style="font-size: 16px; margin: 4px 0;"><b>💰 Valor Total:</b> ${r_data['TOTAL']:,.2f}</p>
                            <p style="font-size: 16px; margin: 4px 0; color: #11998e;"><b>✅ Abonado:</b> ${r_data['ABONADO']:,.2f}</p>
                            <p style="font-size: 18px; margin: 8px 0; color: #ff4b2b;"><b>🔴 SALDO: ${r_data['SALDO_PENDIENTE']:,.2f}</b></p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_recibo_img:
                    st.markdown("#### 🖼️ Foto del Producto")
                    foto_path = str(r_data.get("FOTO", "Sin foto"))
                    if foto_path != "Sin foto" and os.path.exists(foto_path):
                        st.image(foto_path, caption=f"{r_data['CATEG']} - {r_data['CLIENTE']}", use_column_width=True)
                    else:
                        st.info("Sin foto adjunta en este registro.")

                with st.form(f"form_abono_{idx_sel}"):
                    st.markdown("#### 💸 Registrar nuevo abono a este recibo")
                    cant_abonar = st.number_input(f"¿Cuánto dinero trae {r_data['CLIENTE']} hoy? ($)", min_value=0.0, max_value=float(r_data['SALDO_PENDIENTE']), value=float(r_data['SALDO_PENDIENTE']), step=5.0)
                    
                    if st.form_submit_button("📥 REGISTRAR ABONO AL RECIBO"):
                        nuevo_abonado = float(r_data["ABONADO"]) + cant_abonar
                        nuevo_saldo = float(r_data["SALDO_PENDIENTE"]) - cant_abonar
                        
                        df_v.loc[idx_sel, "ABONADO"] = nuevo_abonado
                        df_v.loc[idx_sel, "SALDO_PENDIENTE"] = max(0.0, nuevo_saldo)
                        
                        if nuevo_saldo <= 0:
                            df_v.loc[idx_sel, "ESTADO"] = "Pagado y Entregado"
                            cant_entregar = int(r_data["CANTIDAD"])
                            c_prod = r_data["CATEGORIA"]
                            
                            if c_prod in df_inv["CATEGORIA"].values:
                                df_inv.loc[df_inv["CATEGORIA"] == c_prod, "STOCK"] -= cant_entregar
                                df_inv.to_csv(FILE_INV, index=False)
                                
                            st.session_state["msg_exito"] = f"""
                                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 30px; border-radius: 16px; text-align: center; color: white; margin: 15px 0;">
                                    <h1 style="margin:0; font-size: 28px;">🎉 ¡DEUDA SALDADA!</h1>
                                    <h3 style="margin:10px 0;">EL CLIENTE <b>{r_data['CLIENTE'].upper()}</b> TERMINÓ DE PAGAR.</h3>
                                    <p style="font-size: 20px; margin:0;">📦 <b>ENTREGUE EL PRODUCTO:</b> {cant_entregar}x {c_prod}</p>
                                </div>
                            """
                        else:
                            st.success(f"¡Abono registrado! Nuevo saldo pendiente: ${nuevo_saldo:,.2f}")
                            
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
            
            # Visor rápido de foto en historial seleccionando la fila
            st.markdown("---")
            st.markdown("#### 🔍 Ver Foto de un Registro del Historial")
            lista_hist = [f"Fila {i} | Fecha: {r['FECHA']} | Cliente: {r['CLIENTE']} | Prod: {r['CATEGORIA']}" for i, r in df_h.iterrows()]
            reg_foto_sel = st.selectbox("Selecciona un registro para ver su foto guardada", lista_hist)
            if reg_foto_sel:
                idx_h = int(reg_foto_sel.split(" | ")[0].replace("Fila ", ""))
                path_f = str(df_h.loc[idx_h].get("FOTO", "Sin foto"))
                if path_f != "Sin foto" and os.path.exists(path_f):
                    st.image(path_f, width=300, caption=f"Foto de {df_h.loc[idx_h]['CATEGORIA']}")
                else:
                    st.info("Este registro no tiene foto guardada.")

            st.markdown("---")
            st.markdown("#### 🗑️ Eliminar Registro Erróneo (Protegido)")
            pass_del = st.text_input("Contraseña de Administrador para borrar", type="password", key="pass_del_reg")
            
            if pass_del == CLAVE_ADMIN:
                lista_borrar = [f"Fila {i} | Fecha: {r['FECHA']} | Cliente: {r['CLIENTE']} | Total: ${r['TOTAL']}" for i, r in df_h.iterrows()]
                reg_a_borrar = st.selectbox("Selecciona el registro que deseas eliminar", lista_borrar, key="sel_borrar")
                
                if st.button("❌ BORRAR REGISTRO SELECCIONADO PERMANENTEMENTE"):
                    idx_del = int(reg_a_borrar.split(" | ")[0].replace("Fila ", ""))
                    # Borrar archivo de foto asociado si existe
                    foto_a_borrar = str(df_h.loc[idx_del].get("FOTO", "Sin foto"))
                    if foto_a_borrar != "Sin foto" and os.path.exists(foto_a_borrar):
                        try:
                            os.remove(foto_a_borrar)
                        except:
                            pass
                            
                    df_h = df_h.drop(idx_del).reset_index(drop=True)
                    df_h.to_csv(FILE_VENTAS, index=False)
                    st.success("¡Registro eliminado correctamente!")
                    st.rerun()
            elif pass_del != "":
                st.error("Clave incorrecta para borrar")
            
            st.markdown("---")
            if st.button("📥 Descargar Reporte CSV"):
                st.download_button("Descargar", df_h.to_csv(index=False).encode('utf-8'), "reporte.csv", "text/csv")
