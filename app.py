        if df_pending.empty:
            st.info("🎉 No hay apartados pendientes de pago.")
        else:
            opciones_p = [f"ID {idx}: {row['CLIENTE']} - {row['CATEGORIA']} (Saldo: ${row['SALDO_PENDIENTE']:,.2f})" for idx, row in df_pending.iterrows()]
            sel_p = st.selectbox("👉 Seleccionar Cliente/Apartado", opciones_p)
            
            idx_real = int(sel_p.split(":")[0].replace("ID ", "").strip())
            row_sel = df_pending.loc[idx_real]

            st.write(f"**Cliente:** {row_sel['CLIENTE']} | **Teléfono:** {row_sel['TELEFONO']}")
            st.write(f"**Total Deuda:** ${row_sel['TOTAL']:,.2f} | **Saldo Restante:** ${row_sel['SALDO_PENDIENTE']:,.2f}")

            nuevo_abono = st.number_input("💵 Monto a Abonar ($)", min_value=0.01, max_value=float(row_sel['SALDO_PENDIENTE']), value=float(row_sel['SALDO_PENDIENTE']))

            if st.button("🤝 REGISTRAR ABONO", use_container_width=True):
                nuevo_abono = min(float(nuevo_abono), float(df_ventas.loc[idx_real, "SALDO_PENDIENTE"]))
                df_ventas.loc[idx_real, "ABONADO"] += nuevo_abono
                df_ventas.loc[idx_real, "SALDO_PENDIENTE"] = max(
                    0.0, float(df_ventas.loc[idx_real, "SALDO_PENDIENTE"]) - nuevo_abono
                )
                
                if df_ventas.loc[idx_real, "SALDO_PENDIENTE"] <= 0:
                    df_ventas.loc[idx_real, "ESTADO"] = "Pagado y Entregado"
                
                guardar_ventas(df_ventas)
                st.session_state["df_ventas"] = df_ventas
                st.success("✅ ¡Abono procesado con éxito!")
                st.rerun()

# ------------------------------------------------------------
# TAB 3: INVENTARIO (CREACIÓN Y EDICIÓN RÁPIDA)
# ------------------------------------------------------------
with tab_inventario:
    st.markdown("### 🛠️ Gestión y Reabastecimiento de Inventario")
    
    if not df_inv.empty and "STOCK_MINIMO" in df_inv.columns and "STOCK" in df_inv.columns:
        agotados = df_inv[df_inv["STOCK"] <= df_inv["STOCK_MINIMO"]]
        if not agotados.empty:
            st.warning("⚠️ **Atención: Productos bajo el Stock Mínimo Recomendado**")
            st.dataframe(agotados[["CATEGORIA", "STOCK", "STOCK_MINIMO"]], hide_index=True, use_container_width=True)

    if st.text_input("🔐 Clave Administrador", type="password", key="pwd_inv") == CLAVE_ADMIN:
        principales = [n for n in df_inv["CATEGORIA"].tolist() if " - " not in str(n)]
        opciones = ["✨ Crear Repositorio Principal", "📦 Crear Producto Simple"] + principales
        opc = st.selectbox("Acción / Categoría Padre", opciones)

        if opc == "✨ Crear Repositorio Principal":
            nom = st.text_input("Nombre de la Categoría Principal (Ej: CAMAS)")
            if st.button("➕ CREAR REPOSITORIO"):
                if nom.strip() and not existe_producto(df_inv, nom.strip()):
                    nuevo_df = pd.DataFrame([{"CATEGORIA": nom.strip(), "STOCK": 0, "PRECIO": 0.0, "STOCK_MINIMO": 1}])
                    df_inv = pd.concat([df_inv, nuevo_df], ignore_index=True)
                    guardar_inventario(df_inv)
                    st.session_state["df_inv"] = df_inv
                    st.success("Creado correctamente.")
                    st.rerun()

        elif opc == "📦 Crear Producto Simple":
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombre del Producto")
            stk = c2.number_input("Stock Inicial", min_value=0, value=1)
            prc = c3.number_input("Precio ($)", min_value=0.0, value=10.0)
            if st.button("➕ CREAR PRODUCTO"):
                if nom.strip() and not existe_producto(df_inv, nom.strip()):
                    nuevo_df = pd.DataFrame([{"CATEGORIA": nom.strip(), "STOCK": stk, "PRECIO": prc, "STOCK_MINIMO": 1}])
                    df_inv = pd.concat([df_inv, nuevo_df], ignore_index=True)
                    guardar_inventario(df_inv)
                    st.session_state["df_inv"] = df_inv
                    st.success("Creado correctamente.")
                    st.rerun()
        else:
            sub_nom = st.text_input(f"Subproducto para '{opc}'")
            stk = st.number_input("Stock Subproducto", min_value=0, value=1)
            prc = st.number_input("Precio Subproducto", min_value=0.0, value=10.0)
            if st.button("➕ CREAR SUBPRODUCTO"):
                full_nom = f"{opc} - {sub_nom.strip()}"
                if sub_nom.strip() and not existe_producto(df_inv, full_nom):
                    nuevo_df = pd.DataFrame([{"CATEGORIA": full_nom, "STOCK": stk, "PRECIO": prc, "STOCK_MINIMO": 1}])
                    df_inv = pd.concat([df_inv, nuevo_df], ignore_index=True)
                    guardar_inventario(df_inv)
                    st.session_state["df_inv"] = df_inv
                    st.success("Subproducto creado.")
                    st.rerun()

        st.markdown("---")
        st.subheader("Tabla Completa de Inventario")
        st.dataframe(df_inv, use_container_width=True)

# ------------------------------------------------------------
# TAB 4: HISTORIAL PROTEGIDO (CONSULTA Y EXPORTACIÓN)
# ------------------------------------------------------------
with tab_historial:
    st.markdown("### 📜 Historial de ventas")
    st.caption("Registro de consulta. Para cuidar la trazabilidad, las ventas no se borran desde esta pantalla.")

    if not df_ventas.empty:
        filtro_cliente = st.text_input("Buscar por cliente, producto o teléfono", key="buscar_historial")
        vista = df_ventas.copy()
        if filtro_cliente.strip():
            mascara = vista.astype(str).apply(
                lambda columna: columna.str.contains(filtro_cliente.strip(), case=False, na=False, regex=False)
            ).any(axis=1)
            vista = vista[mascara]

        csv_data = vista.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇️ Descargar registros visibles (CSV)",
            data=csv_data,
            file_name=f"ventas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=False,
        )
        st.dataframe(
            vista,
            hide_index=True,
            use_container_width=True,
            column_config={
                "TOTAL": st.column_config.NumberColumn("Total", format="$%.2f"),
                "ABONADO": st.column_config.NumberColumn("Abonado", format="$%.2f"),
                "SALDO_PENDIENTE": st.column_config.NumberColumn("Saldo pendiente", format="$%.2f"),
            },
        )
        st.caption(f"Mostrando {len(vista)} de {len(df_ventas)} registros.")
    else:
        st.info("Todavía no hay ventas registradas.")
