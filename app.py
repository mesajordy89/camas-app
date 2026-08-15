# ============================================================
#                 TAB 1 - VENDER (CON CARRITO EN VIVO)
# ============================================================
with tab_venta:
    col_catalogo, col_carrito = st.columns([3, 2])

    with col_catalogo:
        st.subheader("🛍️ Catalogo de Productos")
        
        # Filtro o buscador rápido
        busqueda = st.text_input("🔍 Buscar producto...", "")
        prods_filtrados = [p for p in df_inv["CATEGORIA"].tolist() if busqueda.lower() in p.lower()]
        
        # Grid de Productos
        cols = st.columns(2)
        for idx, prod in enumerate(prods_filtrados):
            row = df_inv[df_inv["CATEGORIA"] == prod].iloc[0]
            stock = int(row["STOCK"])
            precio = float(row["PRECIO"])
            
            with cols[idx % 2]:
                st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:15px; border:1px solid #e2e8f0; text-align:center;">
                    <div style="font-size:30px;">📦</div>
                    <div style="font-weight:bold; font-size:16px;">{prod}</div>
                    <div style="color:#2563eb; font-size:20px; font-weight:bold;">${precio:,.2f}</div>
                    <div style="font-size:12px; color:{'#10b981' if stock > 0 else '#ef4444'};">Stock: {stock} ud.</div>
                </div>
                """, unsafe_allow_html=True)
                
                if stock > 0:
                    if st.button(f"➕ Agregar", key=f"add_{prod}"):
                        if "carrito" not in st.session_state:
                            st.session_state["carrito"] = {}
                        st.session_state["carrito"][prod] = st.session_state["carrito"].get(prod, 0) + 1
                        st.rerun()

    with col_carrito:
        st.subheader("🛒 Carrito de Compras")
        
        if "carrito" not in st.session_state or not st.session_state["carrito"]:
            st.info("El carrito está vacío. Haz clic en 'Agregar' en algún producto.")
        else:
            total_general = 0.0
            for item, cant in list(st.session_state["carrito"].items()):
                p_unit = float(df_inv[df_inv["CATEGORIA"] == item]["PRECIO"].values[0])
                subt = p_unit * cant
                total_general += subt
                
                c_item, c_cant, c_del = st.columns([3, 2, 1])
                c_item.write(f"**{item}**\n${p_unit:.2f} c/u")
                c_cant.write(f"Cant: **{cant}** (${subt:.2f})")
                if c_del.button("❌", key=f"del_{item}"):
                    del st.session_state["carrito"][item]
                    st.rerun()
            
            st.markdown(f"### **Total:** :green[${total_general:,.2f}]")
            
            with st.form("form_cobro_carrito"):
                cliente = st.text_input("Cliente", value="Cliente General")
                pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
                
                if st.form_submit_button("💳 COBRAR Y FINALIZAR", use_container_width=True):
                    # Descontar de inventario y guardar ventas
                    for item, cant in st.session_state["carrito"].items():
                        idx = df_inv[df_inv["CATEGORIA"] == item].index[0]
                        df_inv.loc[idx, "STOCK"] -= cant
                    
                    guardar_csv(df_inv, FILE_INV)
                    st.session_state["carrito"] = {}
                    st.success("¡Venta completada con éxito!")
                    st.rerun()

# ============================================================
#                 TAB 2 - APARTADOS CON ABONOS DINÁMICOS
# ============================================================
with tab_apartado:
    st.subheader("📋 Gestión de Apartados y Créditos")
    
    # Filtrar solo ventas en estado "Apartado"
    apartados_activos = df_ventas[df_ventas["ESTADO"].str.contains("Apartado", case=False, na=False)]
    
    if apartados_activos.empty:
        st.info("No hay apartados pendientes por cobrar.")
    else:
        for idx, row in apartados_activos.iterrows():
            total = float(row["TOTAL"])
            abonado = float(row["ABONADO"])
            saldo = float(row["SALDO_PENDIENTE"])
            pct = min(1.0, abonado / total) if total > 0 else 1.0
            
            with st.expander(f"👤 {row['CLIENTE']} | 📦 {row['CATEGORIA']} | Pendiente: ${saldo:,.2f}"):
                c1, c2 = st.columns(2)
                c1.write(f"**Total:** ${total:,.2f}")
                c1.write(f"**Abonado:** ${abonado:,.2f}")
                c2.progress(pct, text=f"{int(pct*100)}% Pagado")
                
                with st.form(f"form_abono_{idx}"):
                    monto_abono = st.number_input("Monto a Abonar ($)", min_value=1.0, max_value=saldo, value=min(10.0, saldo))
                    if st.form_submit_button("💵 REGISTRAR ABONO"):
                        nuevo_abonado = abonado + monto_abono
                        nuevo_saldo = total - nuevo_abonado
                        nuevo_estado = "Pagado y Entregado" if nuevo_saldo <= 0 else "Apartado (Pendiente)"
                        
                        df_ventas.loc[idx, "ABONADO"] = nuevo_abonado
                        df_ventas.loc[idx, "SALDO_PENDIENTE"] = nuevo_saldo
                        df_ventas.loc[idx, "ESTADO"] = nuevo_estado
                        
                        guardar_csv(df_ventas, FILE_VENTAS)
                        st.success(f"Abono de ${monto_abono:.2f} registrado.")
                        st.rerun()
