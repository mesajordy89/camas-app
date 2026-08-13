from datetime import datetime
from email.message import EmailMessage
import os
import smtplib
import urllib.parse

import pandas as pd
import streamlit as st


# ============================================================
#                 CONFIGURACIÓN DEL SISTEMA
# ============================================================

st.set_page_config(
    page_title="Local Mesitas - Sistema POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
#                 DATOS PRINCIPALES
# ============================================================

CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1234"

NUMERO_1 = "593990847819"
NUMERO_2 = "593983576800"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"
CARPETA_FOTOS = "fotos_ventas"


if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)


# ============================================================
#                 FUNCIONES
# ============================================================

def enviar_correo_venta(
    destinatario,
    asunto,
    cuerpo,
    ruta_foto=None
):

    if not destinatario or "@" not in destinatario:
        return

    try:

        remitente = st.secrets["EMAIL_USER"]
        password = st.secrets["EMAIL_PASS"]

    except Exception:

        return

    try:

        msg = EmailMessage()

        msg["Subject"] = asunto
        msg["From"] = remitente
        msg["To"] = destinatario

        msg.set_content(cuerpo)

        if (
            ruta_foto
            and ruta_foto != "Sin foto"
            and os.path.exists(ruta_foto)
        ):

            with open(ruta_foto, "rb") as f:

                file_data = f.read()
                file_name = os.path.basename(ruta_foto)

            msg.add_attachment(
                file_data,
                maintype="image",
                subtype="jpeg",
                filename=file_name
            )

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as smtp:

            smtp.login(
                remitente,
                password
            )

            smtp.send_message(msg)

    except Exception as e:

        print(
            f"Error al enviar correo: {e}"
        )


def generar_link_whatsapp(
    numero,
    mensaje
):

    texto_codificado = urllib.parse.quote(
        mensaje
    )

    return (
        f"https://wa.me/{numero}"
        f"?text={texto_codificado}"
    )


def guardar_foto(
    archivo,
    prefijo=""
):

    if archivo is None:
        return "Sin foto"

    nombre_archivo = (
        f"{prefijo}"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
        f"{archivo.name}"
    )

    ruta = os.path.join(
        CARPETA_FOTOS,
        nombre_archivo
    )

    with open(ruta, "wb") as f:

        f.write(
            archivo.getbuffer()
        )

    return ruta


def mostrar_estado_stock(stock):

    stock = int(stock)

    if stock <= 0:

        return "🔴 AGOTADO"

    elif stock <= 2:

        return "🟠 STOCK BAJO"

    else:

        return "🟢 DISPONIBLE"


def contar_apartados(df):

    if df.empty:
        return 0

    if "ESTADO" not in df.columns:
        return 0

    return len(
        df[
            df["ESTADO"]
            .astype(str)
            .str.contains(
                "Apartado",
                case=False,
                na=False
            )
        ]
    )


# ============================================================
#                 INICIO DE SESIÓN
# ============================================================

if "autenticado" not in st.session_state:

    st.session_state["autenticado"] = False


if not st.session_state["autenticado"]:

    st.markdown(
        """
        <style>

        .stApp {
            background:
            linear-gradient(
                135deg,
                #0f172a 0%,
                #1e293b 50%,
                #334155 100%
            );
        }

        .login-box {

            max-width: 500px;

            margin: 100px auto 30px auto;

            padding: 45px;

            background:
            rgba(255,255,255,0.08);

            border:
            1px solid
            rgba(255,255,255,0.15);

            border-radius: 30px;

            text-align: center;

            box-shadow:
            0 25px 60px
            rgba(0,0,0,0.45);

            backdrop-filter:
            blur(15px);
        }

        .login-title {

            font-size: 42px;

            font-weight: 900;

            color: white;

            margin-bottom: 8px;
        }

        .login-subtitle {

            color: #cbd5e1;

            font-size: 18px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="login-box">

            <div style="
                font-size:70px;
                margin-bottom:10px;
            ">
                🛏️
            </div>

            <div class="login-title">
                LOCAL MESITAS
            </div>

            <div class="login-subtitle">
                Sistema de ventas y administración
            </div>

            <div style="
                font-size:55px;
                margin-top:25px;
            ">
                🔐
            </div>

            <div style="
                color:#94a3b8;
                font-size:16px;
                margin-top:10px;
            ">
                Ingrese su contraseña para continuar
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        passw = st.text_input(
            "🔑 Contraseña",
            type="password",
            key="input_pass_app"
        )

        if st.button(
            "🚀 INGRESAR AL SISTEMA",
            use_container_width=True
        ):

            if passw == CLAVE_ACCESO:

                st.session_state[
                    "autenticado"
                ] = True

                st.rerun()

            else:

                st.error(
                    "❌ Contraseña incorrecta"
                )

    st.stop()


# ============================================================
#                 CARGAR INVENTARIO
# ============================================================

if os.path.exists(FILE_INV):

    df_inv = pd.read_csv(
        FILE_INV
    )

    if "PRECIO" not in df_inv.columns:

        df_inv["PRECIO"] = 0.0

else:

    df_inv = pd.DataFrame(
        [
            {
                "CATEGORIA": "Camas",
                "STOCK": 10,
                "PRECIO": 150.0
            },
            {
                "CATEGORIA": "Colchones",
                "STOCK": 5,
                "PRECIO": 100.0
            },
            {
                "CATEGORIA": "Armarios Grandes",
                "STOCK": 3,
                "PRECIO": 200.0
            },
            {
                "CATEGORIA": "Armarios Pequeños",
                "STOCK": 3,
                "PRECIO": 120.0
            },
            {
                "CATEGORIA": "Pajaritas",
                "STOCK": 10,
                "PRECIO": 15.0
            }
        ]
    )

    df_inv.to_csv(
        FILE_INV,
        index=False
    )


# ============================================================
#                 CARGAR VENTAS
# ============================================================

if os.path.exists(FILE_VENTAS):

    df_ventas = pd.read_csv(
        FILE_VENTAS
    )

    if "ABONADO" not in df_ventas.columns:

        df_ventas["ABONADO"] = (
            df_ventas["TOTAL"]
        )

        df_ventas[
            "SALDO_PENDIENTE"
        ] = 0.0

        df_ventas[
            "ESTADO"
        ] = "Pagado y Entregado"


    if "DIRECCION" not in df_ventas.columns:

        df_ventas[
            "DIRECCION"
        ] = "S/N"


    if "FOTO" not in df_ventas.columns:

        df_ventas[
            "FOTO"
        ] = "Sin foto"


    df_ventas.to_csv(
        FILE_VENTAS,
        index=False
    )

else:

    df_ventas = pd.DataFrame(
        columns=[
            "FECHA",
            "CATEGORIA",
            "CANTIDAD",
            "PRECIO_UNITARIO",
            "TOTAL",
            "ABONADO",
            "SALDO_PENDIENTE",
            "METODO_PAGO",
            "CLIENTE",
            "CEDULA",
            "TELEFONO",
            "CORREO",
            "DIRECCION",
            "ESTADO",
            "FOTO"
        ]
    )

    df_ventas.to_csv(
        FILE_VENTAS,
        index=False
    )


# ============================================================
#                 ESTILO GENERAL
# ============================================================

st.markdown(
    """
    <style>

    .stApp {

        background-color:
        #f1f5f9;

        font-family:
        'Segoe UI',
        Arial,
        sans-serif;
    }


    /* ENCABEZADO */

    .header-box {

        background:
        linear-gradient(
            135deg,
            #0f172a,
            #1e3a8a
        );

        padding:35px;

        border-radius:25px;

        color:white;

        text-align:center;

        margin-bottom:25px;

        box-shadow:
        0 15px 35px
        rgba(15,23,42,0.20);
    }


    /* TARJETAS */

    .info-card {

        background:white;

        padding:22px;

        border-radius:20px;

        text-align:center;

        box-shadow:
        0 5px 18px
        rgba(15,23,42,0.08);

        border:
        1px solid #e2e8f0;

        height:100%;
    }


    .info-title {

        color:#64748b;

        font-size:15px;

        font-weight:700;
    }


    .info-value {

        color:#0f172a;

        font-size:29px;

        font-weight:900;

        margin-top:5px;
    }


    /* TARJETA RECIBO */

    .receipt-card {

        background:white;

        padding:28px;

        border-radius:22px;

        border-left:
        7px solid #2563eb;

        box-shadow:
        0 8px 25px
        rgba(15,23,42,0.08);

        margin-bottom:20px;
    }


    /* BOTONES */

    .stButton > button {

        border-radius:14px;

        min-height:52px;

        font-size:17px !important;

        font-weight:700;

        transition:
        all 0.2s ease;
    }


    .stButton > button:hover {

        transform:
        translateY(-2px);

        box-shadow:
        0 8px 20px
        rgba(0,0,0,0.12);
    }


    /* CAMPOS */

    input,
    textarea {

        border-radius:
        12px !important;
    }


    /* PESTAÑAS */

    div[data-baseweb="tab-list"] {

        gap:10px;

        background:#e2e8f0;

        padding:8px;

        border-radius:16px;

        margin-bottom:20px;
    }


    div[data-baseweb="tab"] {

        border-radius:12px;

        font-weight:700;

        padding:
        10px 18px !important;
    }


    /* MÉTRICAS */

    div[data-testid="stMetric"] {

        background:white;

        padding:18px;

        border-radius:18px;

        box-shadow:
        0 5px 15px
        rgba(0,0,0,0.06);
    }


    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
#                 ENCABEZADO
# ============================================================

col_title, col_logout = st.columns(
    [6, 1]
)

with col_logout:

    if st.button(
        "🔒 Salir",
        use_container_width=True
    ):

        st.session_state[
            "autenticado"
        ] = False

        st.rerun()


st.markdown(
    """
    <div class="header-box">

        <div style="
            font-size:45px;
            font-weight:900;
        ">
            🛏️ LOCAL MESITAS
        </div>

        <div style="
            font-size:20px;
            color:#cbd5e1;
            margin-top:8px;
        ">
            Sistema de Ventas • Apartados • Inventario • Caja
        </div>

        <div style="
            margin-top:15px;
            font-size:15px;
            color:#94a3b8;
        ">
            💼 Administración rápida y sencilla
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
#                 RESUMEN GENERAL
# ============================================================

if os.path.exists(FILE_VENTAS):

    df_resumen = pd.read_csv(
        FILE_VENTAS
    )

else:

    df_resumen = pd.DataFrame()


if not df_resumen.empty:

    dinero_recibido = float(
        df_resumen[
            "ABONADO"
        ].sum()
    )

    operaciones = len(
        df_resumen
    )

    cantidad_apartados = contar_apartados(
        df_resumen
    )

else:

    dinero_recibido = 0
    operaciones = 0
    cantidad_apartados = 0


productos_stock = int(
    df_inv["STOCK"].sum()
)


productos_bajos = int(
    (
        df_inv["STOCK"] <= 2
    ).sum()
)


m1, m2, m3, m4 = st.columns(4)


with m1:

    st.markdown(
        f"""
        <div class="info-card">

            <div class="info-title">
                💰 DINERO RECIBIDO
            </div>

            <div class="info-value">
                ${dinero_recibido:,.2f}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with m2:

    st.markdown(
        f"""
        <div class="info-card">

            <div class="info-title">
                📦 PRODUCTOS EN STOCK
            </div>

            <div class="info-value">
                {productos_stock}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with m3:

    st.markdown(
        f"""
        <div class="info-card">

            <div class="info-title">
                🧾 OPERACIONES
            </div>

            <div class="info-value">
                {operaciones}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with m4:

    st.markdown(
        f"""
        <div class="info-card">

            <div class="info-title">
                📦 APARTADOS ACTIVOS
            </div>

            <div class="info-value">
                {cantidad_apartados}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


st.write("")


# ============================================================
#                 ALERTA DE STOCK
# ============================================================

stock_critico = df_inv[
    df_inv["STOCK"] <= 2
]


if not stock_critico.empty:

    productos_bajos_txt = ", ".join(
        [
            f"**{row['CATEGORIA']}** "
            f"({int(row['STOCK'])} ud.)"
            for _, row
            in stock_critico.iterrows()
        ]
    )

    st.warning(
        "⚠️ **ATENCIÓN - STOCK BAJO:** "
        + productos_bajos_txt
        + " — ¡Reabastece pronto!"
    )


# ============================================================
#                 MENÚ
# ============================================================

tab_ops, tab_apartados, tab_inventario, tab_historial = st.tabs(
    [
        "⚡ Venta Directa",
        "📦 Apartados y Abonos",
        "🛠️ Inventario",
        "📜 Historial y Caja"
    ]
)


# ============================================================
#                 TAB 1 - VENTA DIRECTA
# ============================================================

with tab_ops:

    st.markdown(
        "## ⚡ Venta rápida"
    )

    st.caption(
        "Realiza una venta completa de forma rápida."
    )


    if df_inv.empty:

        st.info(
            "📦 No hay productos en el inventario."
        )

    else:

        iconos = {

            "Camas": "🛏️",

            "Colchones": "💤",

            "Armarios Grandes": "🚪",

            "Armarios Pequeños": "🚪",

            "Pajaritas": "🎀"
        }


        columnas = st.columns(
            min(
                len(df_inv),
                5
            )
        )


        for idx, row in df_inv.iterrows():

            with columnas[
                idx % len(columnas)
            ]:

                stock = int(
                    row["STOCK"]
                )

                estado = mostrar_estado_stock(
                    stock
                )


                st.markdown(
                    f"""
                    <div class="info-card">

                        <div style="
                            font-size:40px;
                        ">
                            {iconos.get(
                                row["CATEGORIA"],
                                "📦"
                            )}
                        </div>

                        <div style="
                            font-size:17px;
                            font-weight:800;
                            margin:8px;
                        ">
                            {row["CATEGORIA"]}
                        </div>

                        <div style="
                            font-size:28px;
                            font-weight:900;
                        ">
                            {stock} ud.
                        </div>

                        <div style="
                            color:#475569;
                            font-weight:600;
                        ">
                            ${float(row["PRECIO"]):,.2f}
                        </div>

                        <div style="
                            margin-top:8px;
                        ">
                            {estado}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


        st.markdown("---")


        categoria_sel = st.selectbox(
            "🛒 Selecciona el producto",
            df_inv[
                "CATEGORIA"
            ].tolist(),
            key="v_cat"
        )


        categoria_final = (
            categoria_sel
        )


        if "cama" in categoria_sel.lower():

            opciones_camas = [

                "Cama de 3 plazas tapizada",

                "Cama de dos plazas tapizada"

            ]


            tipo_cama_sel = st.selectbox(
                "🛏️ ¿Qué tipo de cama vas a vender?",
                opciones_camas,
                key="v_tipo_cama"
            )


            categoria_final = (
                f"{categoria_sel} - "
                f"{tipo_cama_sel}"
            )


        row_sel = df_inv[
            df_inv["CATEGORIA"]
            == categoria_sel
        ].iloc[0]


        stock_disp = int(
            row_sel["STOCK"]
        )

        precio_unit = float(
            row_sel["PRECIO"]
        )


        with st.form(
            "form_venta_rapida"
        ):

            st.markdown(
                "### 🧾 Datos de la venta"
            )


            c1, c2, c3 = st.columns(3)


            with c1:

                cant = st.number_input(
                    "🔢 Cantidad",
                    min_value=1,
                    max_value=max(
                        1,
                        stock_disp
                    ),
                    value=1,
                    step=1
                )


            with c2:

                pago = st.selectbox(
                    "💳 Método de pago",
                    [
                        "Efectivo",
                        "Transferencia",
                        "Tarjeta"
                    ]
                )


            with c3:

                descuento = st.number_input(
                    "🏷️ Descuento ($)",
                    min_value=0.0,
                    value=0.0,
                    step=1.0
                )


            if descuento > 10:

                st.warning(
                    "⚠️ El descuento máximo permitido es $10."
                )


            st.markdown(
                "### 👤 Información del cliente"
            )


            cliente = st.text_input(
                "Nombre del cliente",
                value="Cliente General"
            )


            cc1, cc2 = st.columns(2)


            with cc1:

                celda = st.text_input(
                    "🆔 Cédula / RUC",
                    value="S/N"
                )


            with cc2:

                telefono = st.text_input(
                    "📞 Teléfono",
                    value=""
                )


            correo = st.text_input(
                "📧 Correo electrónico",
                value=""
            )


            direccion = st.text_input(
                "📍 Dirección de entrega",
                value=""
            )


            foto_subida = st.file_uploader(
                "📸 Foto del producto (opcional)",
                type=[
                    "jpg",
                    "jpeg",
                    "png"
                ]
            )


            subtotal = (
                cant *
                precio_unit
            )


            total = max(
                0.0,
                subtotal - descuento
            )


            st.markdown(
                f"""
                <div style="
                    background:#eff6ff;
                    border:2px solid #3b82f6;
                    border-radius:20px;
                    padding:22px;
                    text-align:center;
                    margin:20px 0;
                ">

                    <div style="
                        color:#64748b;
                        font-size:16px;
                        font-weight:700;
                    ">
                        TOTAL A COBRAR
                    </div>

                    <div style="
                        color:#1d4ed8;
                        font-size:42px;
                        font-weight:900;
                    ">
                        ${total:,.2f}
                    </div>

                    <div style="
                        color:#64748b;
                    ">
                        {cant} × ${precio_unit:,.2f}
                        &nbsp; | &nbsp;
                        Descuento: ${descuento:,.2f}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


            submitted_venta = st.form_submit_button(
                "💰 COBRAR Y GENERAR RECIBO",
                use_container_width=True
            )


            if submitted_venta:

                if descuento > 10:

                    st.error(
                        "❌ No se puede procesar la venta. "
                        "El descuento máximo es $10."
                    )

                elif cant > stock_disp:

                    st.error(
                        f"❌ Stock insuficiente. "
                        f"Solo hay {stock_disp} unidades."
                    )

                else:

                    ruta_foto_guardada = guardar_foto(
                        foto_subida
                    )


                    df_inv.loc[
                        df_inv["CATEGORIA"]
                        == categoria_sel,
                        "STOCK"
                    ] -= cant


                    df_inv.to_csv(
                        FILE_INV,
                        index=False
                    )


                    df_actual_v = pd.read_csv(
                        FILE_VENTAS
                    )


                    nueva = pd.DataFrame(
                        [{
                            "FECHA":
                                datetime.now().strftime(
                                    "%Y-%m-%d %H:%M"
                                ),

                            "CATEGORIA":
                                categoria_final,

                            "CANTIDAD":
                                cant,

                            "PRECIO_UNITARIO":
                                precio_unit,

                            "TOTAL":
                                total,

                            "ABONADO":
                                total,

                            "SALDO_PENDIENTE":
                                0.0,

                            "METODO_PAGO":
                                pago,

                            "CLIENTE":
                                cliente,

                            "CEDULA":
                                celda,

                            "TELEFONO":
                                telefono,

                            "CORREO":
                                correo,

                            "DIRECCION":
                                direccion,

                            "ESTADO":
                                "Pagado y Entregado",

                            "FOTO":
                                ruta_foto_guardada
                        }]
                    )


                    pd.concat(
                        [
                            df_actual_v,
                            nueva
                        ],
                        ignore_index=True
                    ).to_csv(
                        FILE_VENTAS,
                        index=False
                    )


                    cuerpo_mail = (
                        "Nueva Venta Registrada:\n"
                        f"- Cliente: {cliente}\n"
                        f"- Producto: {cant}x "
                        f"{categoria_final}\n"
                        f"- Descuento: "
                        f"${descuento:,.2f}\n"
                        f"- Total: "
                        f"${total:,.2f}\n"
                        f"- Método: {pago}\n"
                        f"- Dirección: {direccion}"
                    )


                    enviar_correo_venta(
                        correo,
                        "🧾 Recibo de Compra - Local Mesitas",
                        cuerpo_mail,
                        ruta_foto_guardada
                    )


                    st.session_state[
                        "ultima_venta_ws"
                    ] = {

                        "mensaje":
                            f"""🚨 *NUEVA VENTA REGISTRADA* 🛏️

👤 *Cliente:* {cliente}

📞 *Tel:* {
    telefono
    if telefono
    else "N/A"
}

📦 *Producto:* {cant}x {categoria_final}

🏷️ *Descuento:* ${descuento:,.2f}

💰 *Total:* ${total:,.2f}

💳 *Pago:* {pago}

📍 *Dirección:* {direccion}

📅 *Fecha:* {
    datetime.now().strftime(
        "%Y-%m-%d %H:%M"
    )
}
"""
                    }


                    st.success(
                        "🎉 ¡Venta procesada correctamente!"
                    )

                    st.balloons()

                    st.rerun()


# ============================================================
#                 WHATSAPP
# ============================================================

if "ultima_venta_ws" in st.session_state:

    uv = st.session_state[
        "ultima_venta_ws"
    ]


    link_ws_1 = generar_link_whatsapp(
        NUMERO_1,
        uv["mensaje"]
    )


    link_ws_2 = generar_link_whatsapp(
        NUMERO_2,
        uv["mensaje"]
    )


    st.markdown(
        """
        <div style="
            background:#ecfdf5;
            border:2px solid #22c55e;
            padding:25px;
            border-radius:20px;
            text-align:center;
            margin-top:25px;
        ">

            <h2 style="
                color:#15803d;
                margin:0;
            ">
                📱 Notificación lista
            </h2>

            <p style="
                color:#475569;
            ">
                La venta fue registrada.
                Selecciona dónde enviar el reporte.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    c1, c2, c3 = st.columns(3)


    with c1:

        st.link_button(
            "💬 ENVIAR A WHATSAPP 1",
            link_ws_1,
            use_container_width=True
        )


    with c2:

        st.link_button(
            "💬 ENVIAR A WHATSAPP 2",
            link_ws_2,
            use_container_width=True
        )


    with c3:

        if st.button(
            "✖️ OCULTAR",
            use_container_width=True
        ):

            del st.session_state[
                "ultima_venta_ws"
            ]

            st.rerun()


# ============================================================
#                 TAB 2 - APARTADOS
# ============================================================

with tab_apartados:

    st.markdown(
        "## 📦 Gestión de apartados"
    )

    st.caption(
        "Crea apartados y registra los abonos de tus clientes."
    )


    # --------------------------------------------------------
    # NUEVO APARTADO
    # --------------------------------------------------------

    with st.expander(
        "➕ CREAR NUEVO APARTADO",
        expanded=True
    ):

        if df_inv.empty:

            st.warning(
                "No hay productos disponibles."
            )

        else:

            ap_cat = st.selectbox(
                "📦 Producto a apartar",
                df_inv[
                    "CATEGORIA"
                ].tolist(),
                key="ap_cat_sel"
            )


            ap_categoria_final = (
                ap_cat
            )


            if "cama" in ap_cat.lower():

                opciones_camas_ap = [

                    "Cama de 3 plazas tapizada",

                    "Cama de dos plazas tapizada"

                ]


                tipo_cama_ap_sel = st.selectbox(
                    "🛏️ Tipo de cama",
                    opciones_camas_ap,
                    key="ap_tipo_cama"
                )


                ap_categoria_final = (
                    f"{ap_cat} - "
                    f"{tipo_cama_ap_sel}"
                )


            p_info = df_inv[
                df_inv["CATEGORIA"]
                == ap_cat
            ].iloc[0]


            with st.form(
                "form_nuevo_ap"
            ):

                st.markdown(
                    "### 👤 Datos del cliente"
                )


                c1, c2 = st.columns(2)


                with c1:

                    ap_cliente = st.text_input(
                        "Nombre y apellido"
                    )


                with c2:

                    ap_tel = st.text_input(
                        "📞 Teléfono"
                    )


                c3, c4 = st.columns(2)


                with c3:

                    ap_ced = st.text_input(
                        "🆔 Cédula / DNI"
                    )


                with c4:

                    ap_corr = st.text_input(
                        "📧 Correo electrónico"
                    )


                ap_dir = st.text_input(
                    "📍 Dirección exacta"
                )


                st.markdown(
                    "### 💰 Información del apartado"
                )


                c_a1, c_a2 = st.columns(2)


                with c_a1:

                    ap_cant = st.number_input(
                        "🔢 Cantidad",
                        min_value=1,
                        value=1,
                        step=1
                    )


                with c_a2:

                    ap_abono = st.number_input(
                        "💵 Abono inicial ($)",
                        min_value=0.0,
                        value=10.0,
                        step=5.0
                    )


                ap_foto = st.file_uploader(
                    "📸 Foto del producto (opcional)",
                    type=[
                        "jpg",
                        "jpeg",
                        "png"
                    ],
                    key="foto_ap"
                )


                precio_p = float(
                    p_info["PRECIO"]
                )


                tot_p = (
                    ap_cant *
                    precio_p
                )


                saldo_p = (
                    tot_p -
                    ap_abono
                )


                if ap_abono > tot_p:

                    saldo_mostrar = 0.0

                else:

                    saldo_mostrar = saldo_p


                st.markdown(
                    f"""
                    <div style="
                        background:#f8fafc;
                        border-radius:18px;
                        padding:20px;
                        border:1px solid #e2e8f0;
                        text-align:center;
                        margin:15px 0;
                    ">

                        <div style="
                            font-size:16px;
                            color:#64748b;
                        ">
                            VALOR TOTAL
                        </div>

                        <div style="
                            font-size:32px;
                            font-weight:900;
                        ">
                            ${tot_p:,.2f}
                        </div>

                        <div style="
                            color:#16a34a;
                            font-weight:700;
                        ">
                            Abono: ${ap_abono:,.2f}
                        </div>

                        <div style="
                            color:#dc2626;
                            font-size:22px;
                            font-weight:800;
                            margin-top:5px;
                        ">
                            Saldo:
                            ${max(0,saldo_mostrar):,.2f}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


                guardar_apartado = st.form_submit_button(
                    "💾 GUARDAR APARTADO",
                    use_container_width=True
                )


                if guardar_apartado:

                    if not ap_cliente.strip():

                        st.warning(
                            "⚠️ Ingresa el nombre del cliente."
                        )

                    elif ap_abono > tot_p:

                        st.error(
                            "❌ El abono no puede ser mayor "
                            "al valor total."
                        )

                    else:

                        ruta_foto_ap = guardar_foto(
                            ap_foto,
                            "ap_"
                        )


                        df_actual_v = pd.read_csv(
                            FILE_VENTAS
                        )


                        saldo_real = max(
                            0.0,
                            saldo_p
                        )


                        if saldo_real <= 0:

                            estado_ap = (
                                "Pagado y Entregado"
                            )

                        else:

                            estado_ap = (
                                "Apartado (Pendiente)"
                            )


                        nuevo_ap = pd.DataFrame(
                            [{
                                "FECHA":
                                    datetime.now().strftime(
                                        "%Y-%m-%d %H:%M"
                                    ),

                                "CATEGORIA":
                                    ap_categoria_final,

                                "CANTIDAD":
                                    ap_cant,

                                "PRECIO_UNITARIO":
                                    precio_p,

                                "TOTAL":
                                    tot_p,

                                "ABONADO":
                                    ap_abono,

                                "SALDO_PENDIENTE":
                                    saldo_real,

                                "METODO_PAGO":
                                    "Efectivo",

                                "CLIENTE":
                                    ap_cliente,

                                "CEDULA":
                                    ap_ced,

                                "TELEFONO":
                                    ap_tel,

                                "CORREO":
                                    ap_corr,

                                "DIRECCION":
                                    ap_dir,

                                "ESTADO":
                                    estado_ap,

                                "FOTO":
                                    ruta_foto_ap
                            }]
                        )


                        # Si paga todo,
                        # se descuenta del inventario

                        if saldo_real <= 0:

                            df_inv.loc[
                                df_inv["CATEGORIA"]
                                == ap_cat,
                                "STOCK"
                            ] -= ap_cant

                            df_inv.to_csv(
                                FILE_INV,
                                index=False
                            )


                        pd.concat(
                            [
                                df_actual_v,
                                nuevo_ap
                            ],
                            ignore_index=True
                        ).to_csv(
                            FILE_VENTAS,
                            index=False
                        )


                        cuerpo_mail = (
                            "Nuevo Apartado:\n"
                            f"Cliente: {ap_cliente}\n"
                            f"Producto: {ap_cant}x "
                            f"{ap_categoria_final}\n"
                            f"Total: ${tot_p:,.2f}\n"
                            f"Abono: ${ap_abono:,.2f}\n"
                            f"Saldo: "
                            f"${saldo_real:,.2f}"
                        )


                        enviar_correo_venta(
                            ap_corr,
                            "🧾 Recibo de Apartado - Local Mesitas",
                            cuerpo_mail,
                            ruta_foto_ap
                        )


                        st.session_state[
                            "ultima_venta_ws"
                        ] = {

                            "mensaje":
                                f"""📦 *NUEVO APARTADO REGISTRADO*

👤 *Cliente:* {ap_cliente}

📞 *Tel:* {ap_tel}

📦 *Producto:* {ap_cant}x {ap_categoria_final}

💰 *Total:* ${tot_p:,.2f}

📥 *Abono:* ${ap_abono:,.2f}

🔴 *Saldo:* ${saldo_real:,.2f}

📌 *Estado:* {estado_ap}
"""
                        }


                        if saldo_real <= 0:

                            st.success(
                                "🎉 ¡El cliente pagó todo!"
                            )

                        else:

                            st.success(
                                f"✅ Apartado guardado "
                                f"para {ap_cliente}."
                            )


                        st.rerun()


    # --------------------------------------------------------
    # APARTADOS ACTIVOS
    # --------------------------------------------------------

    st.markdown("---")

    st.markdown(
        "### 📋 Apartados activos"
    )


    df_v = pd.read_csv(
        FILE_VENTAS
    )


    if not df_v.empty:

        if "DIRECCION" not in df_v.columns:

            df_v[
                "DIRECCION"
            ] = "S/N"


        if "FOTO" not in df_v.columns:

            df_v[
                "FOTO"
            ] = "Sin foto"


        pendientes = df_v[
            df_v["ESTADO"]
            .astype(str)
            .str.contains(
                "Apartado",
                case=False,
                na=False
            )
        ]


        if pendientes.empty:

            st.success(
                "✨ No hay apartados pendientes."
            )

        else:

            lista_recibos = [

                (
                    f"Fila {i} ➔ "
                    f"{r['CLIENTE']} | "
                    f"{r['CATEGORIA']} | "
                    f"Debe: "
                    f"${float(r['SALDO_PENDIENTE']):,.2f}"
                )

                for i, r
                in pendientes.iterrows()
            ]


            recibo_sel = st.selectbox(
                "🔍 Selecciona un apartado",
                lista_recibos,
                key="recibo_sel"
            )


            if recibo_sel:

                idx_sel = int(
                    recibo_sel
                    .split(" ➔ ")[0]
                    .replace(
                        "Fila ",
                        ""
                    )
                )


                r_data = df_v.loc[
                    idx_sel
                ]


                col_recibo_txt, col_recibo_img = st.columns(
                    [1.5, 1]
                )


                with col_recibo_txt:

                    st.markdown(
                        f"""
                        <div class="receipt-card">

                            <h2 style="
                                color:#2563eb;
                                margin-top:0;
                            ">
                                🧾 RECIBO DE APARTADO
                            </h2>

                            <p>
                                <b>📅 Fecha:</b>
                                {r_data['FECHA']}
                            </p>

                            <p>
                                <b>👤 Cliente:</b>
                                {r_data['CLIENTE']}
                            </p>

                            <p>
                                <b>📞 Teléfono:</b>
                                {r_data['TELEFONO']}
                            </p>

                            <p>
                                <b>🆔 Cédula:</b>
                                {r_data['CEDULA']}
                            </p>

                            <p>
                                <b>📍 Dirección:</b>
                                {r_data['DIRECCION']}
                            </p>

                            <hr>

                            <p>
                                <b>📦 Producto:</b>
                                {r_data['CANTIDAD']}x
                                {r_data['CATEGORIA']}
                            </p>

                            <p>
                                <b>💰 Total:</b>
                                ${float(r_data['TOTAL']):,.2f}
                            </p>

                            <p style="
                                color:#16a34a;
                            ">
                                <b>✅ Abonado:</b>
                                ${float(r_data['ABONADO']):,.2f}
                            </p>

                            <p style="
                                color:#dc2626;
                                font-size:24px;
                            ">
                                <b>🔴 SALDO:</b>
                                ${float(r_data['SALDO_PENDIENTE']):,.2f}
                            </p>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                with col_recibo_img:

                    st.markdown(
                        "### 🖼️ Producto"
                    )


                    foto_path = str(
                        r_data.get(
                            "FOTO",
                            "Sin foto"
                        )
                    )


                    if (
                        foto_path != "Sin foto"
                        and os.path.exists(
                            foto_path
                        )
                    ):

                        st.image(
                            foto_path,
                            caption=(
                                f"{r_data['CATEGORIA']} "
                                f"- {r_data['CLIENTE']}"
                            ),
                            use_container_width=True
                        )

                    else:

                        st.info(
                            "📷 Sin foto."
                        )


                # ------------------------------------------------
                # ABONO
                # ------------------------------------------------

                with st.form(
                    f"form_abono_{idx_sel}"
                ):

                    st.markdown(
                        "### 💸 Registrar nuevo abono"
                    )


                    saldo_actual = float(
                        r_data[
                            "SALDO_PENDIENTE"
                        ]
                    )


                    cant_abonar = st.number_input(
                        f"💵 ¿Cuánto dinero trae "
                        f"{r_data['CLIENTE']} hoy?",
                        min_value=0.0,
                        max_value=saldo_actual,
                        value=saldo_actual,
                        step=5.0
                    )


                    registrar_abono = st.form_submit_button(
                        "📥 REGISTRAR ABONO",
                        use_container_width=True
                    )


                    if registrar_abono:

                        nuevo_abonado = (
                            float(
                                r_data["ABONADO"]
                            )
                            + cant_abonar
                        )


                        nuevo_saldo = (
                            saldo_actual
                            - cant_abonar
                        )


                        df_v.loc[
                            idx_sel,
                            "ABONADO"
                        ] = nuevo_abonado


                        df_v.loc[
                            idx_sel,
                            "SALDO_PENDIENTE"
                        ] = max(
                            0.0,
                            nuevo_saldo
                        )


                        if nuevo_saldo <= 0:

                            df_v.loc[
                                idx_sel,
                                "ESTADO"
                            ] = (
                                "Pagado y Entregado"
                            )


                            cant_entregar = int(
                                r_data[
                                    "CANTIDAD"
                                ]
                            )


                            c_prod = (
                                r_data[
                                    "CATEGORIA"
                                ]
                                .split(
                                    " - "
                                )[0]
                            )


                            if (
                                c_prod
                                in df_inv[
                                    "CATEGORIA"
                                ].values
                            ):

                                df_inv.loc[
                                    df_inv[
                                        "CATEGORIA"
                                    ] == c_prod,
                                    "STOCK"
                                ] -= (
                                    cant_entregar
                                )


                                df_inv.to_csv(
                                    FILE_INV,
                                    index=False
                                )


                            st.session_state[
                                "msg_exito"
                            ] = (
                                f"""
                                <div style="
                                    background:
                                    linear-gradient(
                                        135deg,
                                        #16a34a,
                                        #15803d
                                    );

                                    padding:30px;

                                    border-radius:20px;

                                    text-align:center;

                                    color:white;

                                    margin:15px 0;
                                ">

                                    <h1>
                                        🎉 ¡DEUDA SALDADA!
                                    </h1>

                                    <h3>
                                        EL CLIENTE
                                        <b>
                                            {r_data['CLIENTE'].upper()}
                                        </b>
                                        TERMINÓ DE PAGAR.
                                    </h3>

                                    <p style="
                                        font-size:21px;
                                    ">
                                        📦
                                        <b>
                                            ENTREGUE EL PRODUCTO:
                                        </b>

                                        {cant_entregar}x
                                        {r_data['CATEGORIA']}
                                    </p>

                                </div>
                                """
                            )

                        else:

                            st.success(
                                f"✅ Abono registrado. "
                                f"Nuevo saldo: "
                                f"${nuevo_saldo:,.2f}"
                            )


                        df_v.to_csv(
                            FILE_VENTAS,
                            index=False
                        )


                        cuerpo_mail = (
                            f"Abono registrado para "
                            f"{r_data['CLIENTE']}\n"
                            f"Abono: "
                            f"${cant_abonar:,.2f}\n"
                            f"Saldo Pendiente: "
                            f"${max(0.0, nuevo_saldo):,.2f}"
                        )


                        enviar_correo_venta(
                            r_data["CORREO"],
                            "🧾 Comprobante de Abono - Local Mesitas",
                            cuerpo_mail,
                            r_data["FOTO"]
                        )


                        st.session_state[
                            "ultima_venta_ws"
                        ] = {

                            "mensaje":
                                f"""💵 *NUEVO ABONO REGISTRADO*

👤 *Cliente:* {r_data['CLIENTE']}

📥 *Abono recibido:* ${cant_abonar:,.2f}

🔴 *Nuevo saldo:* ${max(0.0, nuevo_saldo):,.2f}

📌 *Estado:* {df_v.loc[idx_sel, 'ESTADO']}
"""
                        }


                        st.rerun()


# ============================================================
#                 MENSAJE DE DEUDA SALDADA
# ============================================================

if "msg_exito" in st.session_state:

    st.markdown(
        st.session_state[
            "msg_exito"
        ],
        unsafe_allow_html=True
    )


    if st.button(
        "✖️ Cerrar aviso"
    ):

        del st.session_state[
            "msg_exito"
        ]

        st.rerun()


# ============================================================
#                 TAB 3 - INVENTARIO
# ============================================================

with tab_inventario:

    st.markdown(
        "## 🛠️ Inventario"
    )

    st.caption(
        "Zona protegida para modificar productos, stock y precios."
    )


    pass_inv = st.text_input(
        "🔐 Clave de administrador",
        type="password",
        key="p_inv"
    )


    if pass_inv == CLAVE_ADMIN:

        st.success(
            "✅ Acceso de administrador concedido"
        )


        c1, c2 = st.columns(2)


        # ----------------------------------------------------
        # MODIFICAR
        # ----------------------------------------------------

        with c1:

            st.markdown(
                "### ✏️ Modificar producto"
            )


            if not df_inv.empty:

                prod_m = st.selectbox(
                    "📦 Producto",
                    df_inv[
                        "CATEGORIA"
                    ].tolist(),
                    key="prod_mod"
                )


                fila_prod = df_inv[
                    df_inv["CATEGORIA"]
                    == prod_m
                ].iloc[0]


                act_s = st.number_input(
                    "📦 Sumar / Restar stock",
                    value=0,
                    step=1
                )


                nue_p = st.number_input(
                    "💰 Nuevo precio",
                    min_value=0.0,
                    value=float(
                        fila_prod["PRECIO"]
                    ),
                    step=1.0
                )


                st.markdown(
                    f"""
                    <div class="info-card">

                        <div class="info-title">
                            STOCK ACTUAL
                        </div>

                        <div class="info-value">
                            {int(fila_prod['STOCK'])}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


                if st.button(
                    "💾 ACTUALIZAR",
                    use_container_width=True
                ):

                    idx = df_inv[
                        df_inv["CATEGORIA"]
                        == prod_m
                    ].index[0]


                    df_inv.loc[
                        idx,
                        "STOCK"
                    ] = max(
                        0,
                        int(
                            df_inv.loc[
                                idx,
                                "STOCK"
                            ]
                        )
                        + act_s
                    )


                    df_inv.loc[
                        idx,
                        "PRECIO"
                    ] = nue_p


                    df_inv.to_csv(
                        FILE_INV,
                        index=False
                    )


                    st.success(
                        "✅ Inventario actualizado."
                    )

                    st.rerun()


        # ----------------------------------------------------
        # AGREGAR
        # ----------------------------------------------------

        with c2:

            st.markdown(
                "### ➕ Agregar producto"
            )


            cat_base_opciones = (
                df_inv[
                    "CATEGORIA"
                ].tolist()
                if not df_inv.empty
                else []
            )


            cat_base_opciones.append(
                "✨ [Crear Categoría Nueva]"
            )


            sel_cat_base = st.selectbox(
                "📂 Categoría",
                cat_base_opciones,
                key="sel_cat_base"
            )


            if (
                sel_cat_base
                == "✨ [Crear Categoría Nueva]"
            ):

                nombre_subprod = st.text_input(
                    "Nombre del nuevo producto"
                )

            else:

                nombre_sub = st.text_input(
                    "Nombre del subproducto",
                    placeholder="Ej: De 3 plazas"
                )


                if nombre_sub.strip():

                    nombre_subprod = (
                        f"{sel_cat_base} - "
                        f"{nombre_sub}"
                    )

                else:

                    nombre_subprod = (
                        sel_cat_base
                    )


            n_stk = st.number_input(
                "📦 Stock inicial",
                min_value=0,
                value=5,
                step=1,
                key="ns_stk"
            )


            n_prc = st.number_input(
                "💰 Precio",
                min_value=0.0,
                value=50.0,
                step=1.0,
                key="ns_prc"
            )


            if st.button(
                "➕ CREAR PRODUCTO",
                use_container_width=True
            ):

                if (
                    nombre_subprod
                    and nombre_subprod.strip()
                ):

                    if (
                        nombre_subprod.strip()
                        in df_inv[
                            "CATEGORIA"
                        ].values
                    ):

                        st.error(
                            "❌ Ese producto ya existe."
                        )

                    else:

                        nuevo_reg = pd.DataFrame(
                            [{
                                "CATEGORIA":
                                    nombre_subprod.strip(),

                                "STOCK":
                                    n_stk,

                                "PRECIO":
                                    n_prc
                            }]
                        )


                        pd.concat(
                            [
                                df_inv,
                                nuevo_reg
                            ],
                            ignore_index=True
                        ).to_csv(
                            FILE_INV,
                            index=False
                        )


                        st.success(
                            "🎉 Producto creado correctamente."
                        )

                        st.rerun()


        st.markdown("---")


        # ----------------------------------------------------
        # INVENTARIO VISUAL
        # ----------------------------------------------------

        st.markdown(
            "### 📊 Inventario actual"
        )


        if not df_inv.empty:

            for _, row in df_inv.iterrows():

                stock = int(
                    row["STOCK"]
                )


                estado = mostrar_estado_stock(
                    stock
                )


                col1, col2, col3, col4 = st.columns(
                    [3, 1, 1, 2]
                )


                with col1:

                    st.write(
                        f"📦 **{row['CATEGORIA']}**"
                    )


                with col2:

                    st.write(
                        f"{stock} ud."
                    )


                with col3:

                    st.write(
                        f"${float(row['PRECIO']):,.2f}"
                    )


                with col4:

                    st.write(
                        estado
                    )


        st.markdown("---")


        # ----------------------------------------------------
        # ELIMINAR
        # ----------------------------------------------------

        st.markdown(
            "### 🗑️ Eliminar producto"
        )


        if not df_inv.empty:

            prod_a_borrar = st.selectbox(
                "Selecciona el producto",
                df_inv[
                    "CATEGORIA"
                ].tolist(),
                key="sel_borrar_prod"
            )


            confirmar_eliminar = st.checkbox(
                "⚠️ Confirmo que deseo eliminar este producto",
                key="confirmar_eliminar"
            )


            if st.button(
                "❌ ELIMINAR PRODUCTO",
                use_container_width=True
            ):

                if not confirmar_eliminar:

                    st.warning(
                        "Debes confirmar la eliminación."
                    )

                else:

                    df_inv = df_inv[
                        df_inv[
                            "CATEGORIA"
                        ]
                        != prod_a_borrar
                    ].reset_index(
                        drop=True
                    )


                    df_inv.to_csv(
                        FILE_INV,
                        index=False
                    )


                    st.success(
                        f"✅ Producto eliminado: "
                        f"{prod_a_borrar}"
                    )

                    st.rerun()


    elif pass_inv != "":

        st.error(
            "❌ Clave incorrecta"
        )


# ============================================================
#                 TAB 4 - HISTORIAL Y CAJA
# ============================================================

with tab_historial:

    st.markdown(
        "## 📜 Historial y caja"
    )


    if os.path.exists(FILE_VENTAS):

        df_h = pd.read_csv(
            FILE_VENTAS
        )


        if not df_h.empty:

            # ------------------------------------------------
            # RESUMEN DE CAJA
            # ------------------------------------------------

            total_caja = float(
                df_h[
                    "ABONADO"
                ].sum()
            )


            total_ventas = len(
                df_h
            )


            total_apartados = contar_apartados(
                df_h
            )


            h1, h2, h3 = st.columns(3)


            with h1:

                st.metric(
                    "💰 DINERO RECIBIDO",
                    f"${total_caja:,.2f}"
                )


            with h2:

                st.metric(
                    "🧾 OPERACIONES",
                    total_ventas
                )


            with h3:

                st.metric(
                    "📦 APARTADOS",
                    total_apartados
                )


            st.markdown("---")


            # ------------------------------------------------
            # FILTROS
            # ------------------------------------------------

            st.markdown(
                "### 🔎 Buscar registros"
            )


            f1, f2 = st.columns(2)


            with f1:

                buscar_cliente = st.text_input(
                    "👤 Cliente",
                    key="buscar_cliente"
                )


            with f2:

                buscar_producto = st.text_input(
                    "📦 Producto",
                    key="buscar_producto"
                )


            df_filtrado = df_h.copy()


            if buscar_cliente.strip():

                df_filtrado = df_filtrado[
                    df_filtrado[
                        "CLIENTE"
                    ]
                    .astype(str)
                    .str.contains(
                        buscar_cliente,
                        case=False,
                        na=False
                    )
                ]


            if buscar_producto.strip():

                df_filtrado = df_filtrado[
                    df_filtrado[
                        "CATEGORIA"
                    ]
                    .astype(str)
                    .str.contains(
                        buscar_producto,
                        case=False,
                        na=False
                    )
                ]


            st.markdown(
                "### 📋 Registros"
            )


            st.dataframe(
                df_filtrado,
                use_container_width=True,
                hide_index=True
            )


            # ------------------------------------------------
            # FOTO
            # ------------------------------------------------

            st.markdown("---")

            st.markdown(
                "### 🖼️ Ver foto de un registro"
            )


            lista_hist = [

                (
                    f"Fila {i} | "
                    f"Fecha: {r['FECHA']} | "
                    f"Cliente: {r['CLIENTE']} | "
                    f"Producto: {r['CATEGORIA']}"
                )

                for i, r
                in df_h.iterrows()
            ]


            if lista_hist:

                reg_foto_sel = st.selectbox(
                    "Selecciona un registro",
                    lista_hist,
                    key="reg_foto_sel"
                )


                if reg_foto_sel:

                    idx_h = int(
                        reg_foto_sel
                        .split(" | ")[0]
                        .replace(
                            "Fila ",
                            ""
                        )
                    )


                    path_f = str(
                        df_h.loc[
                            idx_h
                        ].get(
                            "FOTO",
                            "Sin foto"
                        )
                    )


                    if (
                        path_f != "Sin foto"
                        and os.path.exists(
                            path_f
                        )
                    ):

                        st.image(
                            path_f,
                            width=400,
                            caption=(
                                f"Foto de "
                                f"{df_h.loc[idx_h]['CATEGORIA']}"
                            )
                        )

                    else:

                        st.info(
                            "📷 Este registro no tiene foto."
                        )


            # ------------------------------------------------
            # DESCARGA
            # ------------------------------------------------

            st.markdown("---")


            st.markdown(
                "### 📥 Reporte"
            )


            st.download_button(

                "📥 DESCARGAR REPORTE CSV",

                df_h.to_csv(
                    index=False
                ).encode("utf-8"),

                "reporte_local_mesitas.csv",

                "text/csv",

                use_container_width=True
            )


            # ------------------------------------------------
            # ELIMINAR REGISTRO
            # ------------------------------------------------

            st.markdown("---")


            st.markdown(
                "### 🗑️ Eliminar registro"
            )


            st.warning(
                "⚠️ Esta opción es únicamente "
                "para corregir registros equivocados."
            )


            pass_del = st.text_input(
                "🔐 Contraseña de administrador",
                type="password",
                key="pass_del_reg"
            )


            if pass_del == CLAVE_ADMIN:

                lista_borrar = [

                    (
                        f"Fila {i} | "
                        f"Fecha: {r['FECHA']} | "
                        f"Cliente: {r['CLIENTE']} | "
                        f"Total: ${float(r['TOTAL']):,.2f}"
                    )

                    for i, r
                    in df_h.iterrows()
                ]


                if lista_borrar:

                    reg_a_borrar = st.selectbox(
                        "Selecciona el registro",
                        lista_borrar,
                        key="sel_borrar"
                    )


                    confirmar_borrar = st.checkbox(
                        "⚠️ Confirmo que quiero eliminar este registro",
                        key="confirmar_borrar"
                    )


                    if st.button(
                        "❌ BORRAR REGISTRO",
                        use_container_width=True
                    ):

                        if not confirmar_borrar:

                            st.warning(
                                "Debes confirmar la eliminación."
                            )

                        else:

                            idx_del = int(
                                reg_a_borrar
                                .split(" | ")[0]
                                .replace(
                                    "Fila ",
                                    ""
                                )
                            )


                            foto_a_borrar = str(
                                df_h.loc[
                                    idx_del
                                ].get(
                                    "FOTO",
                                    "Sin foto"
                                )
                            )


                            if (
                                foto_a_borrar
                                != "Sin foto"
                                and os.path.exists(
                                    foto_a_borrar
                                )
                            ):

                                try:

                                    os.remove(
                                        foto_a_borrar
                                    )

                                except Exception:

                                    pass


                            df_h = df_h.drop(
                                idx_del
                            ).reset_index(
                                drop=True
                            )


                            df_h.to_csv(
                                FILE_VENTAS,
                                index=False
                            )


                            st.success(
                                "✅ Registro eliminado correctamente."
                            )

                            st.rerun()


            elif pass_del != "":

                st.error(
                    "❌ Contraseña incorrecta."
                )


        else:

            st.info(
                "📭 Todavía no existen registros."
            )

    else:

        st.info(
            "📭 Todavía no existen ventas registradas."
        )


# ============================================================
#                 PIE DE PÁGINA
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        margin-top:40px;
        padding:20px;
        color:#64748b;
        border-top:1px solid #e2e8f0;
    ">

        🛏️ <b>LOCAL MESITAS</b>

        <br>

        Sistema POS • Inventario • Apartados • Caja

        <br>

        <small>
            Administración de ventas
        </small>

    </div>
    """,
    unsafe_allow_html=True
)
