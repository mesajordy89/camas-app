import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# Configuración de página
st.set_page_config(page_title="Local Mesitas - Sistema POS", layout="wide")

# Rutas de archivos
FILE_INV = "inventario_mesitas.csv"
FILE_VENTAS = "ventas_mesitas.csv"
FILE_APARTADOS = "apartados_mesitas.csv"

# Diccionario de números de WhatsApp para vendedores
NUMEROS_WHATSAPP = {
    "Vendedor 1 (0990847819)": "593990847819",
    "Vendedor 2 (0983576800)": "593983576800"
}

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    
    .prod-card-v2 {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        position: relative;
    }
    
    .prod-title { font-weight: 700; font-size: 1.1rem; color: #1e293b; margin-top: 5px; }
    .prod-price { font-weight: 800; font-size: 1.3rem; color: #2563eb; }
    
    .card-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-ok { background: #dcfce7; color: #15803d; }
    .badge-low { background: #fef3c7; color: #b45309; }
    .badge-out { background: #fee2e2; color: #b91c1c; }

    .cart-container {
        background-color: #ffffff;
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
    }

    .total-card {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        padding: 12px;
        border-radius: 8px;
        color: #166534;
        font-weight: bold;
        font-size: 1.2rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# --- FUNCIONES AUXILIARES ---
def cargar_csv(filepath, columnas_defecto):
    if os.path.exists(filepath):
        try:
            return pd.read_csv(filepath)
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
    
    mensaje_encoded = urllib.parse.quote(mensaje)
    return f"https://wa.me/{numero}?text={mensaje_encoded}"

def producto_es_vendible(df_inv, categoria):
    fila = df_inv[df_inv["CATEGORIA"] == categoria]
    if fila.empty:
        return False
    row = fila.iloc[0]
    return row.get("CAMA_BASE", "") != "SI" and row.get("COLCHON_BASE", "") != "SI"

def agregar_combo_al_carrito(sel_cama, sel_colchon, precio_combo):
    prc_c = float(st.session_state["df_inv"][st.session_state["df_inv"]["CATEGORIA"] == sel_cama]["PRECIO"].values[0]) if sel_cama else 0.0
    prc_m = float(st.session_state["df_inv"][st.session_state["df_inv"]["CATEGORIA"] == sel_colchon]["PRECIO"].values[0]) if sel_colchon else 0.0
    suma_individual = prc_c + prc_m

    if suma_individual > 0:
        factor_cama = prc_c / suma_individual
        factor_colchon = prc_m / suma_individual
    else:
        factor_cama = 0.5
        factor_colchon = 0.5

    precio_cama = round(precio_combo * factor_cama, 2)
    precio_colchon = round(precio_combo - precio_cama, 2)

    st.session_state["carrito"].append({"producto": sel_cama, "cantidad": 1, "precio": precio_cama})
    st.session_state["carrito"].append({"producto": sel_colchon, "cantidad": 1, "precio": precio_colchon})
    return True


# --- CARGA DE DATOS Y ESTADO DE SESIÓN ---
COLS_INV = ["CATEGORIA", "STOCK", "STOCK_MINIMO", "PRECIO", "COSTO", "MEDIDA", "CAMA_BASE", "COLCHON_BASE"]
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
if "mostrar_carrito" not in st.session_state:
    st.session_state["mostrar_carrito"] = False

df_inv = st.session_state["df_inv"]
df_ventas = st.session_state["df_ventas"]
df_apartados = st.session_state["df_apartados"]

# Redirección automática a WhatsApp
if st.session_state["redirect_url"]:
    url = st.session_state["redirect_url"]
    st.session_state["redirect_url"] = None
    st.markdown(f'<meta http-equiv="refresh" content="0;url={url}">', unsafe_allow_html=True)
    st.success("Redirigiendo a WhatsApp para enviar el comprobante...")


# --- INTERFAZ PRINCIPAL CON PESTAÑAS ---
tab_venta, tab_apartados, tab_inv, tab_historial = st.tabs([
    "🛒 VENDER", "📑 APARTADOS", "📦 INVENTARIO", "📊 HISTORIAL"
])


# ============================================================
#                 TAB 1: VENDER
# ============================================================
with tab_venta:
    if df_inv.empty:
        st.info("📦 No hay productos registrados en el inventario.")
    else:
        # 1. Promoción: Armar Combo
        st.markdown("### 🎁 Promoción: Armar Combo (Cama + Colchón)")
        
        camas_disponibles = df_inv[
            df_inv["CATEGORIA"].str.contains("CAMA", case=False, na=False) & (df_inv["STOCK"] > 0)
        ]["CATEGORIA"].tolist()
        
        colchones_disponibles = df_inv[
            df_inv["CATEGORIA"].str.contains("COLCHON|COLCHÓN", case=False, na=False) & (df_inv["STOCK"] > 0)
        ]["CATEGORIA"].tolist()

        if camas_disponibles and colchones_disponibles:
            c_combo1, c_combo2, c_combo3, c_combo4 = st.columns([3, 3, 2, 2])
            
            sel_cama = c_combo1.selectbox("🛏️ Seleccionar Cama", camas_disponibles, key="combo_cama_sel")
            sel_colchon = c_combo2.selectbox("💤 Seleccionar Colchón", colchones_disponibles, key="combo_colchon_sel")

            prc_c = float(df_inv[df_inv["CATEGORIA"] == sel_cama]["PRECIO"].values[0]) if sel_cama else 0.0
            prc_m = float(df_inv[df_inv["CATEGORIA"] == sel_colchon]["PRECIO"].values[0]) if sel_colchon else 0.0
            precio_sugerido = prc_c + prc_m

            precio_combo = c_combo3.number_input("💵 Precio Combo ($)", min_value=0.0, value=precio_sugerido, key="combo_precio_input")

            st.write("")
            if c_combo4.button("⚡ AGREGAR COMBO", use_container_width=True, type="primary"):
                if agregar_combo_al_carrito(sel_cama, sel_colchon, precio_combo):
                    st.session_state["mostrar_carrito"] = True
                    st.success("✅ Combo agregado al carrito")
                    st.rerun()

        st.markdown("---")

        # 2. BOTÓN DE APERTURA DIRECTA DEL CARRITO
        cant_items_cart = sum([item['cantidad'] for item in st.session_state["carrito"]])
        texto_btn = f"🛒 VER Y EDITAR CARRITO DE COMPRAS ({cant_items_cart} productos)"
        
        if st.button(texto_btn, type="primary", use_container_width=True):
            st.session_state["mostrar_carrito"] = not st.session_state["mostrar_carrito"]
            st.rerun()

        # 3. SECCIÓN DIRECTA DEL CARRITO EN LA MISMA PÁGINA
        if st.session_state["mostrar_carrito"]:
            st.markdown('<div class="cart-container">', unsafe_allow_html=True)
            st.markdown("### 🛒 Carrito de Compras Actual")
            
            if not st.session_state["carrito"]:
                st.info("El carrito está vacío.")
            else:
                subtotal = 0.0
                st.write("---")
                
                # Listar productos
                for i, item in enumerate(list(st.session_state["carrito"])):
                    tot_item = item["cantidad"] * item["precio"]
                    subtotal += tot_item
                    c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                    c1.write(f"**{item['producto']}**")
                    c2.write(f"x{item['cantidad']}")
                    c3.write(f"${tot_item:,.2f}")
                    
                    # Eliminar producto sin cerrar la sección
                    if c4.button("❌", key=f"del_cart_item_{i}"):
                        st.session_state["carrito"].pop(i)
                        st.rerun()

                st.write("---")
                
                # BOTÓN AÑADIR MÁS PRODUCTOS
                if st.button("➕ Añadir más productos (Ir al Catálogo)", use_container_width=True):
                    st.toast("👇 Selecciona más productos en el catálogo de abajo")

                st.write("")
                descuento = st.number_input("🏷️ Descuento General ($)", min_value=0.0, max_value=float(subtotal), value=0.0, key="desc_general")
                total_final = max(0.0, subtotal - descuento)
                
                st.markdown(f'<div class="total-card">TOTAL A PAGAR: ${total_final:,.2f}</div>', unsafe_allow_html=True)
                st.write("")

                with st.form("form_finalizar_venta_directa"):
                    m_pago = st.selectbox("💳 Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
                    c_nom = st.text_input("👤 Nombre Cliente", value="Cliente General")
                    c_ced = st.text_input("🆔 Cédula/RUC", value="S/N")
                    c_tel = st.text_input("📞 Teléfono", value="")
                    c_dir = st.text_input("📍 Dirección Entrega", value="")

                    destino_recibo = st.selectbox(
                        "📲 Enviar Recibo por WhatsApp",
                        list(NUMEROS_WHATSAPP.keys())
                    )

                    if st.form_submit_button("💰 FINALIZAR VENTA Y REGISTRAR", use_container_width=True):
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
                            "CLIENTE": c_nom,
                            "CEDULA": c_ced,
                            "TELEFONO": c_tel,
                            "CORREO": "",
                            "DIRECCION": c_dir,
                            "ESTADO": "Pagado y Entregado",
                            "FOTO": "Sin foto"
                        }

                        df_v_act = pd.concat([st.session_state["df_ventas"], pd.DataFrame([nueva_v_dict])], ignore_index=True)
                        guardar_csv(df_v_act, FILE_VENTAS)
                        st.session_state["df_ventas"] = df_v_act
                        st.session_state["ultima_venta"] = nueva_v_dict
                        st.session_state["carrito"] = []
                        st.session_state["mostrar_carrito"] = False

                        num_dest = NUMEROS_WHATSAPP[destino_recibo]
                        st.session_state["redirect_url"] = generar_link_whatsapp(num_dest, nueva_v_dict)
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # 4. CATÁLOGO DE PRODUCTOS ABAJO
        st.markdown("### 🛍️ Catálogo de Productos")
        
        cols_grid = st.columns(3)
        vendibles = df_inv[df_inv["CATEGORIA"].apply(lambda x: producto_es_vendible(df_inv, x))].copy()

        for i, (_, row) in enumerate(vendibles.iterrows()):
            stk = int(row['STOCK'])
            stk_min = int(row['STOCK_MINIMO'])
            
            if stk <= 0: badge_class, badge_text = "badge-out", "Agotado"
            elif stk <= stk_min: badge_class, badge_text = "badge-low", f"Últimas {stk} uds"
            else: badge_class, badge_text = "badge-ok", f"Stock: {stk} uds"

            with cols_grid[i % 3]:
                st.markdown(f"""
                <div class="prod-card-v2">
                    <span class="card-badge {badge_class}">{badge_text}</span>
                    <div class="prod-title">🛏️ {row['CATEGORIA']}</div>
                    <div class="prod-price">${row['PRECIO']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if stk > 0:
                    if st.button("🛒 Agregar al Carrito", key=f"btn_add_cart_{i}", use_container_width=True):
                        encontrado = False
                        for item in st.session_state["carrito"]:
                            if item["producto"] == row['CATEGORIA']:
                                if item["cantidad"] + 1 <= stk:
                                    item["cantidad"] += 1
                                    encontrado = True
                                break
                        if not encontrado:
                            st.session_state["carrito"].append({
                                "producto": row['CATEGORIA'],
                                "cantidad": 1,
                                "precio": float(row['PRECIO'])
                            })
                        st.session_state["mostrar_carrito"] = True
                        st.rerun()
                else:
                    st.button("❌ Sin Stock", key=f"btn_select_dis_{i}", disabled=True, use_container_width=True)


# ============================================================
#                 TAB 2: APARTADOS Y RESERVAS
# ============================================================
with tab_apartados:
    st.markdown("### 📑 Gestión de Apartados y Reservas")
    
    with st.expander("➕ Registrar Nuevo Apartado", expanded=False):
        with st.form("form_nuevo_apartado"):
            col_ap1, col_ap2 = st.columns(2)
            c_cliente = col_ap1.text_input("👤 Nombre Cliente")
            c_tel = col_ap2.text_input("📞 Teléfono WhatsApp")
            
            prods_inv = df_inv["CATEGORIA"].tolist() if not df_inv.empty else []
            c_prod = col_ap1.selectbox("🛏️ Producto a Reservar", prods_inv)
            
            c_tot = col_ap2.number_input("💵 Precio Total ($)", min_value=0.0, step=5.0)
            c_abono = col_ap1.number_input("💰 Abono Inicial ($)", min_value=0.0, step=5.0)
            c_fecha_ent = col_ap2.date_input("📅 Fecha Estimada de Entrega")

            if st.form_submit_button("📌 Registrar Apartado", use_container_width=True):
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
                    st.success("✅ Apartado registrado con éxito")
                    st.rerun()
                else:
                    st.error("Por favor completa los datos requeridos.")

    st.write("---")
    st.dataframe(st.session_state["df_apartados"], use_container_width=True)


# ============================================================
#                 TAB 3: INVENTARIO DE PRODUCTOS
# ============================================================
with tab_inv:
    st.markdown("### 📦 Control de Inventario y Productos")
    
    with st.expander("➕ Agregar Nuevo Producto al Inventario", expanded=False):
        with st.form("form_nuevo_inv"):
            col_i1, col_i2 = st.columns(2)
            p_cat = col_i1.text_input("🏷️ Categoría / Nombre Producto")
            p_stock = col_i2.number_input("📦 Stock Inicial", min_value=0, value=10, step=1)
            p_min = col_i1.number_input("⚠️ Stock Mínimo Alerta", min_value=0, value=2, step=1)
            p_precio = col_i2.number_input("💵 Precio Venta ($)", min_value=0.0, value=0.0, step=5.0)
            p_costo = col_i1.number_input("💲 Costo ($)", min_value=0.0, value=0.0, step=5.0)
            p_medida = col_i2.text_input("📏 Medida / Tamaño", value="1.5 Plazas")

            if st.form_submit_button("💾 Guardar Producto", use_container_width=True):
                if p_cat:
                    nuevo_p = {
                        "CATEGORIA": p_cat,
                        "STOCK": p_stock,
                        "STOCK_MINIMO": p_min,
                        "PRECIO": p_precio,
                        "COSTO": p_costo,
                        "MEDIDA": p_medida,
                        "CAMA_BASE": "NO",
                        "COLCHON_BASE": "NO"
                    }
                    df_inv_act = pd.concat([st.session_state["df_inv"], pd.DataFrame([nuevo_p])], ignore_index=True)
                    guardar_csv(df_inv_act, FILE_INV)
                    st.session_state["df_inv"] = df_inv_act
                    st.success("✅ Producto agregado correctamente")
                    st.rerun()

    st.write("---")
    
    # Edición de stock rápido
    st.dataframe(st.session_state["df_inv"], use_container_width=True)


# ============================================================
#                 TAB 4: HISTORIAL DE VENTAS
# ============================================================
with tab_historial:
    st.markdown("### 📊 Historial de Ventas Registradas")
    
    if st.session_state["df_ventas"].empty:
        st.info("No hay registro de ventas realizadas.")
    else:
        st.dataframe(st.session_state["df_ventas"], use_container_width=True)
        
        tot_recaudado = st.session_state["df_ventas"]["TOTAL"].sum() if "TOTAL" in st.session_state["df_ventas"].columns else 0.0
        st.metric(label="💰 Total Recaudado en Ventas", value=f"${tot_recaudado:,.2f}")
