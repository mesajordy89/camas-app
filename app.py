# ============================================================
#            TAB 1: VENDER Y CATÁLOGO MEJORADO
# ============================================================
with tab_venta:
    if df_inv.empty:
        st.info("📦 No hay productos registrados en el inventario.")
    else:
        # ESTILOS MEJORADOS PARA EL CATÁLOGO
        html("""
        <style>
        .catalog-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        .card-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge-ok { background-color: #dcfce7; color: #15803d; }
        .badge-low { background-color: #fef3c7; color: #b45309; }
        .badge-out { background-color: #fee2e2; color: #b91c1c; }
        .prod-card-v2 {
            background: white;
            border-radius: 18px;
            padding: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.04);
            transition: transform 0.2s ease;
            height: 100%;
        }
        .prod-title {
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            margin-top: 8px;
            margin-bottom: 4px;
            min-height: 44px;
        }
        .prod-price {
            font-size: 24px;
            font-weight: 900;
            color: #2563eb;
            margin: 6px 0;
        }
        </style>
        """)

        st.markdown("### 🛍️ Catálogo de Productos")
        
        # BUSCADOR Y FILTROS
        col_busqueda, col_filtro = st.columns([3, 1])
        with col_busqueda:
            busqueda = st.text_input("🔍 Buscar producto en el catálogo...", "", key="search_catalog")
        with col_filtro:
            filtro_stock = st.selectbox("Filtrar por", ["Todos", "En Stock", "Agotados"])

        # OBTENER PRODUCTOS VENDIBLES
        vendibles = df_inv[df_inv["CATEGORIA"].apply(lambda x: producto_es_vendible(df_inv, x))].copy()

        # APLICAR FILTROS
        if busqueda.strip():
            vendibles = vendibles[vendibles["CATEGORIA"].str.contains(busqueda, case=False, na=False)]
        
        if filtro_stock == "En Stock":
            vendibles = vendibles[vendibles["STOCK"] > 0]
        elif filtro_stock == "Agotados":
            vendibles = vendibles[vendibles["STOCK"] <= 0]

        # MOSTRAR GRILLA DE PRODUCTOS
        if vendibles.empty:
            st.warning("🔍 No se encontraron productos con el filtro aplicado.")
        else:
            cols_grid = st.columns(3)
            for i, (_, row) in enumerate(vendibles.iterrows()):
                stk = int(row['STOCK'])
                stk_min = int(row['STOCK_MINIMO'])
                
                if stk <= 0:
                    badge_class, badge_text = "badge-out", "Agotado"
                elif stk <= stk_min:
                    badge_class, badge_text = "badge-low", f"Últimas {stk} uds"
                else:
                    badge_class, badge_text = "badge-ok", f"Stock: {stk} uds"

                with cols_grid[i % 3]:
                    st.markdown(f"""
                    <div class="prod-card-v2">
                        <span class="card-badge {badge_class}">{badge_text}</span>
                        <div class="prod-title">🛏️ {row['CATEGORIA']}</div>
                        <div class="prod-price">${row['PRECIO']:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botón para seleccionar directo desde la tarjeta
                    if stk > 0:
                        if st.button(f"🛒 Seleccionar", key=f"btn_select_{i}", use_container_width=True):
                            st.session_state["sel_venta_prod"] = row['CATEGORIA']
                            st.rerun()
                    else:
                        st.button("❌ Sin Stock", key=f"btn_select_dis_{i}", disabled=True, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📦 Procesar Venta Directa")
        
        lista_productos = obtener_productos_vendibles(df_inv)
        OPCION_COMBO = "🎁 Combo (Cama + Colchón)"
        opciones_venta = [OPCION_COMBO] + lista_productos

        # Si el producto se seleccionó desde el catálogo, se posiciona automáticamente
        idx_default = 0
        if "sel_venta_prod" in st.session_state and st.session_state["sel_venta_prod"] in opciones_venta:
            idx_default = opciones_venta.index(st.session_state["sel_venta_prod"])

        producto_elegido = st.selectbox("👉 Producto seleccionado para la venta", opciones_venta, index=idx_default, key="sel_venta_prod_main")
        es_combo = (producto_elegido == OPCION_COMBO)

        if es_combo:
            camas = [p for p in lista_productos if "cama" in p.lower()]
            colchones = [p for p in lista_productos if "colchon" in p.lower() or "colchón" in p.lower()]

            if not camas or not colchones:
                st.error("⚠️ Para vender un combo, debe existir al menos 1 Cama y 1 Colchón disponibles.")
            else:
                c1, c2 = st.columns(2)
                cama_combo = c1.selectbox("🛏️ Seleccionar Cama", camas)
                colchon_combo = c2.selectbox("💤 Seleccionar Colchón", colchones)

                stock_cama = int(df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]["STOCK"])
                stock_colchon = int(df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]["STOCK"])
                stock_disp = min(stock_cama, stock_colchon)

                sugerido = float(df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]["PRECIO"]) + float(df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]["PRECIO"])
                precio_unitario = st.number_input("🏷️ Precio Final Combo ($)", min_value=0.0, value=sugerido, step=5.0)
                nombre_venta = f"COMBO: {cama_combo} + {colchon_combo}"
                st.info(f"💡 Combos armables en stock: **{stock_disp}** unidades")
        else:
            fila = df_inv[df_inv["CATEGORIA"] == producto_elegido].iloc[0]
            stock_disp = int(fila["STOCK"])
            precio_unitario = float(fila["PRECIO"])
            nombre_venta = producto_elegido

        if not es_combo or (camas and colchones):
            if stock_disp <= 0:
                st.error(f"🔴 **{nombre_venta}** se encuentra totalmente agotado.")
            else:
                with st.form("form_venta"):
                    a1, a2, a3 = st.columns(3)
                    cantidad = 1 if es_combo else a1.number_input("🔢 Cantidad", min_value=1, max_value=stock_disp, value=1)
                    metodo_pago = a2.selectbox("💳 Método de Pago", ["Efectivo", "Transferencia", "Tarjeta"])
                    descuento = a3.number_input("🏷️ Descuento ($ Máx $10)", min_value=0.0, max_value=10.0, value=0.0, step=1.0)

                    c_nom = st.text_input("👤 Nombre Cliente", value="Cliente General")
                    c_ced = st.text_input("🆔 Cédula/RUC", value="S/N")
                    c_tel = st.text_input("📞 Teléfono", value="")
                    c_dir = st.text_input("📍 Dirección Entrega", value="")

                    total_final = max(0.0, (cantidad * precio_unitario) - descuento)
                    st.markdown(f'<div class="total-card">TOTAL A COBRAR: ${total_final:,.2f}</div>', unsafe_allow_html=True)

                    if st.form_submit_button("💰 COMPLETAR VENTA", use_container_width=True):
                        if es_combo:
                            df_inv.loc[df_inv["CATEGORIA"] == cama_combo, "STOCK"] -= 1
                            df_inv.loc[df_inv["CATEGORIA"] == colchon_combo, "STOCK"] -= 1
                        else:
                            df_inv.loc[df_inv["CATEGORIA"] == producto_elegido, "STOCK"] -= cantidad

                        guardar_csv(df_inv, FILE_INV)
                        st.session_state["df_inv"] = df_inv

                        nueva_v_dict = {
                            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "CATEGORIA": nombre_venta, "CANTIDAD": cantidad,
                            "PRECIO_UNITARIO": precio_unitario, "TOTAL": total_final,
                            "ABONADO": total_final, "SALDO_PENDIENTE": 0.0,
                            "METODO_PAGO": metodo_pago, "CLIENTE": c_nom,
                            "CEDULA": c_ced, "TELEFONO": c_tel, "CORREO": "",
                            "DIRECCION": c_dir, "ESTADO": "Pagado y Entregado", "FOTO": "Sin foto"
                        }
                        df_v_actualizado = pd.concat([st.session_state["df_ventas"], pd.DataFrame([nueva_v_dict])], ignore_index=True)
                        guardar_csv(df_v_actualizado, FILE_VENTAS)
                        st.session_state["df_ventas"] = df_v_actualizado
                        st.session_state["ultima_venta"] = nueva_v_dict

                        st.success("✅ ¡Venta efectuada con éxito!")
                        st.rerun()

        if st.session_state.get("ultima_venta"):
            st.markdown("---")
            st.markdown("### 📄 Opciones de Recibo y Envío")
            v_ult = st.session_state["ultima_venta"]

            c_w1, c_w2 = st.columns(2)
            with c_w1:
                link_w1 = generar_link_whatsapp("593990847819", v_ult)
                st.markdown(f'<a href="{link_w1}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📲 ENVIAR RECIBO A 0990847819</button></a>', unsafe_allow_html=True)

            with c_w2:
                link_w2 = generar_link_whatsapp("593983576800", v_ult)
                st.markdown(f'<a href="{link_w2}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">📲 ENVIAR RECIBO A 0983576800</button></a>', unsafe_allow_html=True)

            if HAS_REPORTLAB:
                pdf_buf = generar_pdf_recibo(v_ult)
                st.write("")
                st.download_button("📄 Descargar Recibo PDF", data=pdf_buf, file_name=f"recibo_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf", use_container_width=True)
