import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# Configuración de página
st.set_page_config(page_title="Local Mesitas - POS", layout="wide", initial_sidebar_state="collapsed")

ADMIN_PASSWORD = "admin"

FILE_INV = "inventario_mesitas.csv"
FILE_VENTAS = "ventas_mesitas.csv"
FILE_APARTADOS = "apartados_mesitas.csv"

NUMEROS_WHATSAPP = {
    "Vendedor 1 (0990847819)": "593990847819",
    "Vendedor 2 (0983576800)": "593983576800"
}

# --- ESTILOS CSS PRO PARA EL CATÁLOGO ---
st.markdown("""
<style>
    .stApp { 
        background-color: #f8fafc; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .catalog-card {
        background: #ffffff;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 20px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    
    .catalog-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
        border-color: #cbd5e1;
    }

    .card-img-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
        position: relative;
        margin-bottom: 12px;
    }

    .badge-float {
        position: absolute;
        top: 8px;
        right: 8px;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .badge-ok { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .badge-low { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .badge-out { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }

    .card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.3;
        margin-bottom: 8px;
        min-height: 42px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .card-price-tag {
        font-size: 1.4rem;
        font-weight: 800;
        color: #2563eb;
        margin-bottom: 10px;
    }

    .promo-banner {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        color: #ffffff;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
    }
</style>
""", unsafe_allow_html=True)


# --- FUNCIONES BASE ---
def cargar_csv(filepath, columnas_defecto):
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            for col in columnas_defecto:
                if col not in df.columns:
                    df[col] = "NO" if col == "ES_TITULO" else ""
            return df
        except Exception:
            return pd.DataFrame(columns=columnas_defecto)
    else:
        df = pd.DataFrame(columns=columnas_defecto)
        df.to_csv(filepath, index=False)
        return df

def guardar_csv(df, filepath):
    df.to_csv(filepath, index=False)

def generar_link_whatsapp(numero, venta_dict):
    mensaje = f"""*RECIBO DE VENTA - LOCAL MESITAS* 🧾
----------------------------------------
*Cliente:* {venta_dict['CLIENTE']}
*Cédula/RUC:* {venta_dict['CEDULA']}
*Teléfono:* {venta_dict['TELEFONO']}
*Dirección:* {venta_dict['DIRECCION']}
----------------------------------------
*Detalle:* {venta_dict['CATEGORIA']}
*Cant. Total:* {venta_dict['CANTIDAD']}
*Método Pago:* {venta_dict['METODO_PAGO']}
*Total Pagado:* ${venta_dict['TOTAL']:.2f}
----------------------------------------
¡Gracias por su compra! 🚀"""
    return f"https://wa.me/{numero}?text={urllib.parse.quote(mensaje)}"

def producto_es_vendible(df_inv, categoria):
    fila = df_inv[df_inv["CATEGORIA"] == categoria]
    if fila.empty: return False
    row = fila.iloc[0]
    es_titulo = str(row.get("ES_TITULO", "NO")).strip().upper() in ["SI", "SÍ", "TRUE", "1"]
    cama_base = str(row.get("CAMA_BASE", "NO")).strip().upper() == "SI"
    colchon_base = str(row.get("COLCHON_BASE", "NO")).strip().upper() == "SI"
    return not (es_titulo or cama_base or colchon_base)

def verificar_admin():
    if "admin_autenticado" not in st.session_state:
        st.session_state["admin_autenticado"] = False

    active_tab = st.session_state.get("active_tab", "default")

    if not st.session_state["admin_autenticado"]:
        st.warning("🔒 Esta sección requiere acceso de Administrador.")
        clave = st.text_input("Ingrese la clave de Administrador:", type="password", key=f"pass_input_{active_tab}")
        if st.button("🔓 Iniciar Sesión Admin", key=f"btn_login_{active_tab}"):
            if clave == ADMIN_PASSWORD:
                st.session_state["admin_autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
        return False
    else:
        col_m1, col_m2 = st.columns([6, 1])
        col_m1.info("🔑 Sesión de Administrador activa")
        if col_m2.button("🚪 Cerrar Sesión", key=f"btn_logout_{active_tab}"):
            st.session_state["admin_autenticado"] = False
            st.rerun()
        return True


# --- INICIALIZACIÓN ---
COLS_INV = ["CATEGORIA", "STOCK", "STOCK_MINIMO", "PRECIO", "COSTO", "MEDIDA", "CAMA_BASE", "COLCHON_BASE", "ES_TITULO", "PADRE"]
COLS_VENTAS = ["FECHA", "CATEGORIA", "CANTIDAD", "PRECIO_UNITARIO", "TOTAL", "ABONADO", "SALDO_PENDIENTE", "METODO_PAGO", "CLIENTE", "CEDULA", "TELEFONO", "CORREO", "DIRECCION", "ESTADO", "FOTO"]
COLS_APARTADOS = ["ID", "FECHA", "CLIENTE", "TELEFONO", "CATEGORIA", "TOTAL", "ABONADO", "SALDO", "ESTADO", "FECHA_ENTREGA"]

if "df_inv" not in st.session_state:
    st.session_state["df_inv"] = cargar_csv(FILE_INV, COLS_INV)
if "df_ventas" not in st.session_state:
    st.session_state["df_ventas"] = cargar_csv(FILE_VENTAS, COLS_VENTAS)
if "df_apartados" not in st.session_state:
    st.session_state["df_apartados"] = cargar_csv(FILE_APARTADOS, COLS_APARTADOS)
if "carrito" not in st.session_state:
    st.session_state["carrito"] = []
if "redirect_url" not in st.session_state:
    st.session_state["redirect_url"] = None
if "abrir_dialogo" not in st.session_state:
    st.session_state["abrir_dialogo"] = False
if "filtro_categoria" not in st.session_state:
    st.session_state["filtro_categoria"] = "TODOS"

for col in COLS_INV:
    if col not in st.session_state["df_inv"].columns:
        st.session_state["df_inv"][col] = "NO" if col == "ES_TITULO" else ""

df_inv = st.session_state["df_inv"]

if st.session_state["redirect_url"]:
    url = st.session_state["redirect_url"]
    st.session_state["redirect_url"] = None
    st.markdown(f'<meta http-equiv="refresh" content="0;url={url}">', unsafe_allow_html=True)
    st.success("Redirigiendo a WhatsApp...")


# --- VENTANA MODAL DIRECTA ---
@st.dialog("🛒 Resumen de Compra & Checkout")
def abrir_modal_carrito():
    if not st.session_state["carrito"]:
        st.info("El carrito de compras está vacío actualmente.")
        if st.button("⬅️ Volver al catálogo", use_container_width=True):
            st.session_state["abrir_dialogo"] = False
            st.rerun()
        return

    subtotal = 0.0
    st.write("### Productos en la Orden")
    
    for i, item in enumerate(list(st.session_state["carrito"])):
        tot_item = item["cantidad"] * item["precio"]
        subtotal += tot_item
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        c1.write(f"**{item['producto']}**")
        c2.write(f"x{item['cantidad']}")
        c3.write(f"${tot_item:,.2f}")
        if c4.button("🗑️", key=f"del_mod_{i}"):
            st.session_state["carrito"].pop(i)
            st.rerun()

    st.divider()

    if st.button("➕ Agregar más productos del catálogo", use_container_width=True):
        st.session_state["abrir_dialogo"] = False
        st.rerun()

    st.write("")
    descuento = st.number_input("🏷️ Descuento General ($)", min_value=0.0, max_value=float(subtotal), value=0.0)
    total_final = max(0.0, subtotal - descuento)
    
    st.markdown(f"### **Total Final: ${total_final:,.2f}**")
    st.divider()

    # OPCIÓN DE VENTA SIN DATOS / CONSUMIDOR FINAL
    sin_datos = st.checkbox("⚡ Venta sin datos (Consumidor Final / Sin Factura)", value=False)

    with st.form("form_modal_checkout"):
        m_pago = st.selectbox("💳 Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
        
        st.subheader("Datos del Cliente")
        if sin_datos:
            c_nom = st.text_input("👤 Nombre Cliente", value="CONSUMIDOR FINAL", disabled=True)
            c_ced = st.text_input("🆔 Cédula/RUC", value="9999999999999", disabled=True)
            c_tel = st.text_input("📞 Teléfono", value="S/N", disabled=True)
            c_dir = st.text_input("📍 Dirección Entrega", value="S/N", disabled=True)
        else:
            c_nom = st.text_input("👤 Nombre Cliente", value="")
            c_ced = st.text_input("🆔 Cédula/RUC", value="")
            c_tel = st.text_input("📞 Teléfono", value="")
            c_dir = st.text_input("📍 Dirección Entrega", value="")
            
        destino_recibo = st.selectbox("📲 Enviar Recibo por WhatsApp", list(NUMEROS_WHATSAPP.keys()))

        if st.form_submit_button("💰 FINALIZAR COMPRA Y EMITIR RECIBO", use_container_width=True, type="primary"):
            df_inv_local = st.session_state["df_inv"]
            for item in st.session_state["carrito"]:
                df_inv_local.loc[df_inv_local["CATEGORIA"] == item["producto"], "STOCK"] -= item["cantidad"]
            
            guardar_csv(df_inv_local, FILE_INV)
            st.session_state["df_inv"] = df_inv_local

            resumen_prods = " + ".join([f"{it['producto']} (x{it['cantidad']})" for it in st.session_state["carrito"]])
            cant_total = sum([it['cantidad'] for it in st.session_state["carrito"]])

            nueva_v_dict = {
                "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "CATEGORIA": resumen_prods,
                "CANTIDAD": cant_total,
                "PRECIO_UNITARIO": total_final,
                "TOTAL": total_final,
                "ABONADO": total_final,
                "SALDO_PENDIENTE": 0.0,
                "METODO_PAGO": m_pago,
                "CLIENTE": c_nom if c_nom else "CONSUMIDOR FINAL",
                "CEDULA": c_ced if c_ced else "9999999999999",
                "TELEFONO": c_tel if c_tel else "S/N",
                "CORREO": "",
                "DIRECCION": c_dir if c_dir else "S/N",
                "ESTADO": "Pagado y Entregado",
                "FOTO": "Sin foto"
            }

            df_v_act = pd.concat([st.session_state["df_ventas"], pd.DataFrame([nueva_v_dict])], ignore_index=True)
            guardar_csv(df_v_act, FILE_VENTAS)
            st.session_state["df_ventas"] = df_v_act
            st.session_state["carrito"] = []
            st.session_state["abrir_dialogo"] = False
            
            num_dest = NUMEROS_WHATSAPP[destino_recibo]
            st.session_state["redirect_url"] = generar_link_whatsapp(num_dest, nueva_v_dict)
            st.rerun()


if st.session_state["abrir_dialogo"]:
    abrir_modal_carrito()


# --- INTERFAZ PRINCIPAL ---
tab_venta, tab_apartados, tab_inv, tab_historial = st.tabs([
    "🛒 CATÁLOGO Y VENTA", "📑 APARTADOS", "📦 INVENTARIO", "📊 HISTORIAL"
])


# ============================================================
#            TAB 1: CATÁLOGO Y VENTA
# ============================================================
with tab_venta:
    col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 1, 1])
    col_hdr1.title("✨ Catálogo de Productos")
    
    cant_items = sum([it['cantidad'] for it in st.session_state["carrito"]])
    
    if col_hdr2.button(f"🛒 Ver Carrito ({cant_items})", type="primary", use_container_width=True):
        st.session_state["abrir_dialogo"] = True
        st.rerun()

    if col_hdr3.button("🗑️ Vaciar Carrito", use_container_width=True, disabled=(cant_items == 0)):
        st.session_state["carrito"] = []
        st.session_state["abrir_dialogo"] = False
        st.rerun()

    if df_inv.empty:
        st.info("📦 No hay productos registrados en el inventario.")
    else:
        subproductos = df_inv[df_inv["CATEGORIA"].apply(lambda x: producto_es_vendible(df_inv, x))]

        # PROMOCIÓN COMBO
        camas_disponibles = subproductos[subproductos["CATEGORIA"].str.contains("CAMA", case=False, na=False) & (subproductos["STOCK"] > 0)]["CATEGORIA"].tolist()
        colchones_disponibles = subproductos[subproductos["CATEGORIA"].str.contains("COLCHON|COLCHÓN", case=False, na=False) & (subproductos["STOCK"] > 0)]["CATEGORIA"].tolist()

        if camas_disponibles and colchones_disponibles:
            with st.container():
                st.markdown('<div class="promo-banner"><h3 style="margin:0; font-weight:800;">⚡ Armar Combo Promocional Especial</h3><p style="margin:4px 0 0 0; opacity:0.9; font-size:0.9rem;">Combina cama + colchón a un precio preferencial</p></div>', unsafe_allow_html=True)
                cb1, cb2, cb3, cb4 = st.columns([3, 3, 2, 2])
                sel_c = cb1.selectbox("🛏️ Cama", camas_disponibles, key="cb_cama")
                sel_m = cb2.selectbox("💤 Colchón", colchones_disponibles, key="cb_colchon")
                
                prc_c = float(df_inv[df_inv["CATEGORIA"] == sel_c]["PRECIO"].values[0]) if sel_c else 0.0
                prc_m = float(df_inv[df_inv["CATEGORIA"] == sel_m]["PRECIO"].values[0]) if sel_m else 0.0
                
                p_combo = cb3.number_input("💵 Precio Combo ($)", min_value=0.0, value=(prc_c + prc_m))
                
                if cb4.button("⚡ Añadir Combo", type="primary", use_container_width=True):
                    st.session_state["carrito"].append({"producto": sel_c, "cantidad": 1, "precio": round(p_combo * 0.5, 2)})
                    st.session_state["carrito"].append({"producto": sel_m, "cantidad": 1, "precio": round(p_combo * 0.5, 2)})
                    st.session_state["abrir_dialogo"] = True
                    st.rerun()

        st.divider()

        # BOTONES DE FILTRO RÁPIDO
        f1, f2, f3 = st.columns([1, 1, 3])
        if f1.button("📌 Todos los Productos", use_container_width=True):
            st.session_state["filtro_categoria"] = "TODOS"
        if f2.button("🛏️ Solo Camas", use_container_width=True):
            st.session_state["filtro_categoria"] = "CAMA"
        if f3.button("💤 Solo Colchones", use_container_width=True):
            st.session_state["filtro_categoria"] = "COLCHON"

        # BUSCADOR
        search_query = st.text_input("🔍 Buscar por nombre de producto...", placeholder="Ej: Tapizada, Sueño Total...")
        
        # FILTRADO DE DATOS
        if st.session_state["filtro_categoria"] != "TODOS":
            subproductos = subproductos[subproductos["CATEGORIA"].str.contains(st.session_state["filtro_categoria"], case=False, na=False)]

        if search_query:
            subproductos = subproductos[subproductos["CATEGORIA"].str.contains(search_query, case=False, na=False)]

        st.write("")

        # TARJETAS DE PRODUCTOS
        cols_per_row = 3
        cols = st.columns(cols_per_row)

        for idx, (_, row) in enumerate(subproductos.iterrows()):
            stk = int(row['STOCK'])
            stk_min = int(row['STOCK_MINIMO'])
            
            if stk <= 0:
                badge = '<span class="badge-float badge-out">Agotado</span>'
            elif stk <= stk_min:
                badge = f'<span class="badge-float badge-low">¡Últimas {stk} unid!</span>'
            else:
                badge = f'<span class="badge-float badge-ok">Stock: {stk}</span>'

            icono = "🛏️" if "CAMA" in row['CATEGORIA'].upper() else "💤" if "COLCHON" in row['CATEGORIA'].upper() else "📦"

            with cols[idx % cols_per_row]:
                st.markdown(f"""
                <div class="catalog-card">
                    <div class="card-img-header">
                        {badge}
                        <span>{icono}</span>
                    </div>
                    <div class="card-title">{row['CATEGORIA']}</div>
                    <div class="card-price-tag">${row['PRECIO']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

                if stk > 0:
                    c_cant, c_btn = st.columns([1, 2])
                    cant_pedir = c_cant.number_input("Cant:", min_value=1, max_value=stk, value=1, key=f"cant_in_{idx}")
                    
                    if c_btn.button("🛒 Añadir", key=f"add_{idx}", use_container_width=True, type="secondary"):
                        encontrado = False
                        for item in st.session_state["carrito"]:
                            if item["producto"] == row['CATEGORIA']:
                                if item["cantidad"] + cant_pedir <= stk:
                                    item["cantidad"] += cant_pedir
                                    encontrado = True
                                else:
                                    item["cantidad"] = stk
                                    encontrado = True
                                break
                        if not encontrado:
                            st.session_state["carrito"].append({
                                "producto": row['CATEGORIA'],
                                "cantidad": cant_pedir,
                                "precio": float(row['PRECIO'])
                            })
                        st.session_state["abrir_dialogo"] = True
                        st.rerun()
                else:
                    st.button("🚫 Sin Stock", key=f"dis_{idx}", disabled=True, use_container_width=True)


# ============================================================
#            TAB 2: APARTADOS (PÚBLICO - SIN CLAVE)
# ============================================================
with tab_apartados:
    st.markdown("### 📑 Gestión de Apartados y Reservas")
    
    with st.expander("➕ Registrar Nuevo Apartado", expanded=False):
        with st.form("form_nuevo_apartado"):
            col_ap1, col_ap2 = st.columns(2)
            c_cliente = col_ap1.text_input("👤 Nombre Cliente")
            c_tel = col_ap2.text_input("📞 Teléfono WhatsApp")
            prods_vendibles = df_inv[df_inv["CATEGORIA"].apply(lambda x: producto_es_vendible(df_inv, x))]["CATEGORIA"].tolist()
            c_prod = col_ap1.selectbox("🛏️ Producto a Reservar", prods_vendibles)
            c_tot = col_ap2.number_input("💵 Precio Total ($)", min_value=0.0)
            c_abono = col_ap1.number_input("💰 Abono Inicial ($)", min_value=0.0)
            c_fecha_ent = col_ap2.date_input("📅 Fecha Entrega")

            if st.form_submit_button("📌 Registrar Apartado", use_container_width=True, type="primary"):
                if c_cliente and c_prod and c_tot > 0:
                    nuevo_id = len(st.session_state["df_apartados"]) + 1
                    saldo_pend = max(0.0, c_tot - c_abono)
                    nuevo_apt = {
                        "ID": f"APT-{nuevo_id:03d}",
                        "FECHA": datetime.now().strftime("%Y-%m-%d"),
                        "CLIENTE": c_cliente,
                        "TELEFONO": c_tel,
                        "CATEGORIA": c_prod,
                        "TOTAL": c_tot,
                        "ABONADO": c_abono,
                        "SALDO": saldo_pend,
                        "ESTADO": "Pendiente" if saldo_pend > 0 else "Liquidado",
                        "FECHA_ENTREGA": c_fecha_ent.strftime("%Y-%m-%d")
                    }
                    df_apt_act = pd.concat([st.session_state["df_apartados"], pd.DataFrame([nuevo_apt])], ignore_index=True)
                    guardar_csv(df_apt_act, FILE_APARTADOS)
                    st.session_state["df_apartados"] = df_apt_act
                    st.success("✅ Apartado guardado con éxito")
                    st.rerun()
                else:
                    st.error("❌ Por favor completa el cliente, producto y un precio válido.")

    st.write("")
    
    if st.session_state["df_apartados"].empty:
        st.info("📑 No hay reservas ni apartados registrados.")
    else:
        st.dataframe(st.session_state["df_apartados"], use_container_width=True)
        
        with st.expander("🗑️ Eliminar o Cancelar un Apartado"):
            list_ids = st.session_state["df_apartados"]["ID"].tolist()
            apt_eliminar = st.selectbox("Seleccione el ID a eliminar:", list_ids)
            if st.button("❌ Eliminar Apartado Seleccionado", type="secondary"):
                df_apt_act = st.session_state["df_apartados"][st.session_state["df_apartados"]["ID"] != apt_eliminar]
                guardar_csv(df_apt_act, FILE_APARTADOS)
                st.session_state["df_apartados"] = df_apt_act
                st.success(f"Apartado {apt_eliminar} eliminado.")
                st.rerun()


# ============================================================
#           TAB 3: INVENTARIO (PROTEGIDO)
# ============================================================
with tab_inv:
    st.session_state["active_tab"] = "inventario"
    if verificar_admin():
        st.markdown("### 📦 Control de Inventario")
        with st.expander("➕ Registrar Producto o Categoría"):
            with st.form("form_nuevo_inv"):
                col_i1, col_i2 = st.columns(2)
                p_cat = col_i1.text_input("🏷️ Categoría / Producto")
                es_titulo = col_i2.selectbox("📌 ¿Es solo un Título/Categoría?", ["NO", "SI"])
                titulos_padre = df_inv[df_inv["ES_TITULO"].astype(str).str.upper().isin(["SI", "SÍ", "TRUE", "1"])]["CATEGORIA"].tolist()
                padre_sel = col_i1.selectbox("📂 Categoría Padre", ["Ninguno"] + titulos_padre)
                p_stock = col_i2.number_input("📦 Stock Inicial", min_value=0, value=10)
                p_min = col_i1.number_input("⚠️ Stock Mínimo", min_value=0, value=2)
                p_precio = col_i2.number_input("💵 Precio Venta ($)", min_value=0.0)
                p_costo = col_i1.number_input("💲 Costo ($)", min_value=0.0)

                if st.form_submit_button("💾 Guardar Producto", use_container_width=True):
                    if p_cat:
                        nombre_final = f"{padre_sel} - {p_cat}" if padre_sel != "Ninguno" and es_titulo == "NO" else p_cat
                        nuevo_p = {
                            "CATEGORIA": nombre_final,
                            "STOCK": p_stock,
                            "STOCK_MINIMO": p_min,
                            "PRECIO": p_precio,
                            "COSTO": p_costo,
                            "MEDIDA": "Standard",
                            "CAMA_BASE": "NO",
                            "COLCHON_BASE": "NO",
                            "ES_TITULO": es_titulo,
                            "PADRE": padre_sel if padre_sel != "Ninguno" else ""
                        }
                        df_inv_act = pd.concat([st.session_state["df_inv"], pd.DataFrame([nuevo_p])], ignore_index=True)
                        guardar_csv(df_inv_act, FILE_INV)
                        st.session_state["df_inv"] = df_inv_act
                        st.success("✅ Producto agregado")
                        st.rerun()

        st.dataframe(st.session_state["df_inv"], use_container_width=True)


# ============================================================
#    TAB 4: HISTORIAL (PÚBLICO CON CLAVE SOLO PARA ELIMINAR)
# ============================================================
with tab_historial:
    st.markdown("### 📊 Historial de Ventas")
    
    if st.session_state["df_ventas"].empty:
        st.info("Sin ventas registradas.")
    else:
        st.dataframe(st.session_state["df_ventas"], use_container_width=True)
        tot_recaudado = st.session_state["df_ventas"]["TOTAL"].sum()
        st.metric(label="💰 Total Recaudado", value=f"${tot_recaudado:,.2f}")
        
        st.divider()
        
        with st.expander("🗑️ Eliminar Registro de Venta (Requiere Clave)"):
            st.write("Selecciona el registro que deseas eliminar:")
            
            opciones_ventas = [f"Fila {i}: {row['FECHA']} - {row['CLIENTE']} (${row['TOTAL']:.2f})" 
                               for i, row in st.session_state["df_ventas"].iterrows()]
            
            idx_seleccionado = st.selectbox("Seleccione la venta a eliminar:", range(len(opciones_ventas)), 
                                            format_func=lambda x: opciones_ventas[x])
            
            pass_delete = st.text_input("Ingrese Clave de Administrador para confirmar eliminación:", type="password", key="pass_del_hist")
            
            if st.button("❌ Confirmar y Eliminar Venta", type="secondary"):
                if pass_delete == ADMIN_PASSWORD:
                    df_v_act = st.session_state["df_ventas"].drop(idx_seleccionado).reset_index(drop=True)
                    guardar_csv(df_v_act, FILE_VENTAS)
                    st.session_state["df_ventas"] = df_v_act
                    st.success("✅ Venta eliminada correctamente.")
                    st.rerun()
                else:
                    st.error("❌ Clave incorrecta. No se pudo eliminar el registro.")
