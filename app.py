from datetime import datetime
from email.message import EmailMessage
import mimetypes
import os
import smtplib
import textwrap
import urllib.parse

import pandas as pd
import streamlit as st


# ============================================================
#                 LOCAL MESITAS - SISTEMA POS
#        VERSIÓN CORREGIDA - PRODUCTOS Y SUBPRODUCTOS
# ============================================================

st.set_page_config(
    page_title="Local Mesitas - Sistema POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
#                 CONFIGURACIÓN
# ============================================================

CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1234"

NUMERO_1 = "593990847819"
NUMERO_2 = "593983576800"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"
CARPETA_FOTOS = "fotos_ventas"

os.makedirs(CARPETA_FOTOS, exist_ok=True)

COLUMNAS_VENTAS = [
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
    "FOTO",
]


# ============================================================
#            FUNCIÓN PARA HTML
# ============================================================

def html(contenido):
    """
    Permite utilizar HTML correctamente en Streamlit
    eliminando saltos de línea y sangrías redundantes.
    """
    texto_limpio = textwrap.dedent(contenido).strip()
    texto_limpio = " ".join(line.strip() for line in texto_limpio.splitlines())
    return st.markdown(
        texto_limpio,
        unsafe_allow_html=True,
    )


# ============================================================
#                 FUNCIONES DE DATOS
# ============================================================

def guardar_csv(df, ruta):
    """Guarda un DataFrame en CSV."""
    df.to_csv(
        ruta,
        index=False,
        encoding="utf-8-sig",
    )


def normalizar_inventario(df):
    """Normaliza el inventario."""

    if "CATEGORIA" not in df.columns:
        df["CATEGORIA"] = ""

    if "STOCK" not in df.columns:
        df["STOCK"] = 0

    if "PRECIO" not in df.columns:
        df["PRECIO"] = 0.0

    df["CATEGORIA"] = (
        df["CATEGORIA"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["STOCK"] = pd.to_numeric(
        df["STOCK"],
        errors="coerce",
    ).fillna(0).astype(int)

    df["STOCK"] = df["STOCK"].clip(
        lower=0
    )

    df["PRECIO"] = pd.to_numeric(
        df["PRECIO"],
        errors="coerce",
    ).fillna(0.0)

    df["PRECIO"] = df["PRECIO"].clip(
        lower=0
    )

    df = df[
        df["CATEGORIA"] != ""
    ].reset_index(drop=True)

    return df[
        [
            "CATEGORIA",
            "STOCK",
            "PRECIO",
        ]
    ]


def normalizar_ventas(df):
    """Asegura que existan todas las columnas de ventas."""

    for columna in COLUMNAS_VENTAS:

        if columna in df.columns:
            continue

        if columna == "ABONADO":

            if "TOTAL" in df.columns:

                df[columna] = pd.to_numeric(
                    df["TOTAL"],
                    errors="coerce",
                ).fillna(0.0)

            else:

                df[columna] = 0.0

        elif columna == "SALDO_PENDIENTE":

            df[columna] = 0.0

        elif columna == "ESTADO":

            df[columna] = "Pagado y Entregado"

        elif columna == "DIRECCION":

            df[columna] = "S/N"

        elif columna == "FOTO":

            df[columna] = "Sin foto"

        else:

            df[columna] = ""

    for columna in [
        "CANTIDAD",
        "PRECIO_UNITARIO",
        "TOTAL",
        "ABONADO",
        "SALDO_PENDIENTE",
    ]:

        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce",
        ).fillna(0.0)

    df["CANTIDAD"] = (
        df["CANTIDAD"]
        .astype(int)
        .clip(lower=0)
    )

    for columna in [
        "PRECIO_UNITARIO",
        "TOTAL",
        "ABONADO",
        "SALDO_PENDIENTE",
    ]:

        df[columna] = df[columna].clip(
            lower=0
        )

    for columna in [
        "FECHA",
        "CATEGORIA",
        "METODO_PAGO",
        "CLIENTE",
        "CEDULA",
        "TELEFONO",
        "CORREO",
        "DIRECCION",
        "ESTADO",
        "FOTO",
    ]:

        df[columna] = (
            df[columna]
            .fillna("")
            .astype(str)
        )

    return df[
        COLUMNAS_VENTAS
    ]


def cargar_inventario():

    if os.path.exists(FILE_INV):

        try:

            df = pd.read_csv(
                FILE_INV,
                encoding="utf-8-sig",
            )

        except Exception:

            df = pd.DataFrame()

    else:

        df = pd.DataFrame()

    df = normalizar_inventario(df)

    guardar_csv(
        df,
        FILE_INV,
    )

    return df


def cargar_ventas():

    if os.path.exists(FILE_VENTAS):

        try:

            df = pd.read_csv(
                FILE_VENTAS,
                encoding="utf-8-sig",
            )

        except Exception:

            df = pd.DataFrame()

    else:

        df = pd.DataFrame()

    df = normalizar_ventas(df)

    guardar_csv(
        df,
        FILE_VENTAS,
    )

    return df


# ============================================================
#                 FOTOS
# ============================================================

def guardar_foto(
    archivo,
    prefijo="",
):

    if archivo is None:
        return "Sin foto"

    nombre = (
        f"{prefijo}"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_"
        f"{os.path.basename(archivo.name)}"
    )

    ruta = os.path.join(
        CARPETA_FOTOS,
        nombre,
    )

    try:

        with open(
            ruta,
            "wb",
        ) as archivo_salida:

            archivo_salida.write(
                archivo.getbuffer()
            )

        return ruta

    except Exception:

        return "Sin foto"


# ============================================================
#                 WHATSAPP
# ============================================================

def generar_link_whatsapp(
    numero,
    mensaje,
):

    texto = urllib.parse.quote(
        mensaje
    )

    return (
        f"https://wa.me/"
        f"{numero}?text={texto}"
    )


# ============================================================
#                 CORREO
# ============================================================

def enviar_correo_venta(
    destinatario,
    asunto,
    cuerpo,
    ruta_foto=None,
):

    if (
        not destinatario
        or "@"
        not in str(destinatario)
    ):
        return

    try:

        remitente = st.secrets[
            "EMAIL_USER"
        ]

        password = st.secrets[
            "EMAIL_PASS"
        ]

    except Exception:

        return

    try:

        mensaje = EmailMessage()

        mensaje["Subject"] = asunto
        mensaje["From"] = remitente
        mensaje["To"] = destinatario

        mensaje.set_content(
            cuerpo
        )

        if (
            ruta_foto
            and ruta_foto != "Sin foto"
            and os.path.exists(ruta_foto)
        ):

            with open(
                ruta_foto,
                "rb",
            ) as f:

                datos = f.read()

            tipo_mime, _ = (
                mimetypes.guess_type(
                    ruta_foto
                )
            )

            if not tipo_mime:
                tipo_mime = "image/jpeg"

            maintype, subtype = (
                tipo_mime.split(
                    "/",
                    1,
                )
            )

            mensaje.add_attachment(
                datos,
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(
                    ruta_foto
                ),
            )

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
        ) as smtp:

            smtp.login(
                remitente,
                password,
            )

            smtp.send_message(
                mensaje
            )

    except Exception as error:

        print(
            f"Error al enviar correo: {error}"
        )


# ============================================================
#                 FUNCIONES VISUALES
# ============================================================

def obtener_icono(categoria):

    texto = str(
        categoria
    ).lower()

    if "combo" in texto:
        return "🎁"

    if "cama" in texto:
        return "🛏️"

    if (
        "colchon" in texto
        or "colchón" in texto
    ):
        return "💤"

    if "armario" in texto:
        return "🚪"

    if "pajarita" in texto:
        return "🎀"

    return "📦"


def estado_stock(stock):

    stock = max(
        0,
        int(stock),
    )

    if stock == 0:
        return (
            "🔴 AGOTADO",
            "#dc2626",
        )

    if stock <= 2:
        return (
            "🟠 POCO STOCK",
            "#ea580c",
        )

    return (
        "🟢 DISPONIBLE",
        "#16a34a",
    )


def contar_apartados(df):

    if (
        df.empty
        or "ESTADO"
        not in df.columns
    ):
        return 0

    return int(
        df["ESTADO"]
        .astype(str)
        .str.contains(
            "Apartado",
            case=False,
            na=False,
        )
        .sum()
    )


# ============================================================
#                 PRODUCTOS / SUBPRODUCTOS
# ============================================================

def es_subproducto(nombre):

    return " - " in str(
        nombre
    )


def base_producto(categoria):

    return str(
        categoria
    ).split(
        " - "
    )[0].strip()


def obtener_subproductos(
    df,
    principal,
):

    prefijo = (
        str(principal).strip()
        + " - "
    )

    return df[
        df["CATEGORIA"]
        .astype(str)
        .str.startswith(
            prefijo,
            na=False,
        )
    ].copy()


def es_categoria_principal(
    df,
    nombre,
):

    nombre = str(
        nombre
    ).strip()

    return not obtener_subproductos(
        df,
        nombre,
    ).empty


def producto_es_vendible(
    df,
    nombre,
):

    nombre = str(
        nombre
    ).strip()

    if es_subproducto(
        nombre
    ):
        return True

    return not es_categoria_principal(
        df,
        nombre,
    )


def obtener_productos_vendibles(
    df,
):

    return [
        nombre
        for nombre
        in df["CATEGORIA"].tolist()
        if producto_es_vendible(
            df,
            nombre,
        )
    ]


def existe_producto(
    df,
    nombre,
):

    return (
        nombre.strip().lower()
        in
        df["CATEGORIA"]
        .astype(str)
        .str.strip()
        .str.lower()
        .values
    )


# ============================================================
#                 LOGIN
# ============================================================

if "autenticado" not in st.session_state:

    st.session_state[
        "autenticado"
    ] = False


if not st.session_state[
    "autenticado"
]:

    html(
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
            max-width:520px;
            margin:80px auto 25px auto;
            padding:45px;
            background:rgba(255,255,255,0.08);
            border:1px solid rgba(255,255,255,0.15);
            border-radius:30px;
            text-align:center;
            box-shadow:0 25px 60px rgba(0,0,0,0.45);
            backdrop-filter:blur(15px);
        }

        .login-title {
            font-size:42px;
            color:white;
            font-weight:900;
        }

        .login-subtitle {
            font-size:18px;
            color:#cbd5e1;
            margin-top:8px;
        }
        </style>
        """
    )

    html(
        """
        <div class="login-box">

            <div style="font-size:72px;">
                🛏️
            </div>

            <div class="login-title">
                LOCAL MESITAS
            </div>

            <div class="login-subtitle">
                Sistema de ventas y administración
            </div>

            <div style="
                font-size:48px;
                margin-top:25px;
            ">
                🔐
            </div>

            <div style="
                color:#94a3b8;
                font-size:16px;
            ">
                Escriba su contraseña y presione INGRESAR
            </div>

        </div>
        """
    )

    c1, c2, c3 = st.columns(
        [1, 2, 1]
    )

    with c2:

        clave = st.text_input(
            "🔑 Contraseña",
            type="password",
            key="clave_login",
        )

        if st.button(
            "🚀 INGRESAR",
            use_container_width=True,
        ):

            if clave == CLAVE_ACCESO:

                st.session_state[
                    "autenticado"
                ] = True

                st.rerun()

            else:

                st.error(
                    "❌ La contraseña es incorrecta."
                )

    st.stop()


# ============================================================
#                 CARGAR INFORMACIÓN
# ============================================================

df_inv = cargar_inventario()
df_ventas = cargar_ventas()


# ============================================================
#                 ESTILOS GENERALES
# ============================================================

html(
    """
    <style>

    .stApp {
        background:#f1f5f9;
        font-family:
            'Segoe UI',
            'Arial',
            sans-serif;
    }

    .header-box {
        background:
        linear-gradient(
            135deg,
            #0f172a,
            #1e3a8a
        );

        padding:30px;
        border-radius:25px;
        color:white;
        text-align:center;
        margin-bottom:20px;

        box-shadow:
            0 12px 30px
            rgba(15,23,42,0.18);
    }

    .info-card {
        background:white;
        padding:20px;
        border-radius:20px;
        text-align:center;
        border:1px solid #e2e8f0;

        box-shadow:
            0 6px 18px
            rgba(15,23,42,0.07);
    }

    .product-card {
        background:white;
        border:1px solid #e2e8f0;
        border-radius:22px;
        padding:20px 12px;
        text-align:center;
        min-height:220px;

        box-shadow:
            0 8px 25px
            rgba(15,23,42,0.08);

        margin-bottom:15px;
    }

    .total-card {
        background:
        linear-gradient(
            135deg,
            #eff6ff,
            #dbeafe
        );

        border:2px solid #3b82f6;
        border-radius:22px;
        padding:24px;
        text-align:center;
    }

    .receipt-card {
        background:white;
        padding:26px;
        border-radius:22px;
        border-left:7px solid #2563eb;

        box-shadow:
            0 8px 25px
            rgba(15,23,42,0.08);
    }

    .stButton > button {
        border-radius:14px;
        min-height:54px;
        font-weight:800;
        font-size:17px !important;
    }

    input,
    textarea,
    select {
        border-radius:12px !important;
    }

    .stSelectbox label,
    .stTextInput label,
    .stNumberInput label,
    .stFileUploader label,
    .stTextArea label {
        font-size:17px !important;
        font-weight:700 !important;
    }

    div[data-baseweb="tab-list"] {
        gap:8px;
        background:#e2e8f0;
        padding:8px;
        border-radius:16px;
    }

    div[data-baseweb="tab"] {
        border-radius:12px;
        font-weight:800;
        padding:11px 18px !important;
        font-size:16px !important;
    }

    div[data-testid="stAlert"] {
        border-radius:15px;
    }

    div[data-testid="stMetric"] {
        background:white;
        padding:16px;
        border-radius:18px;

        box-shadow:
            0 5px 15px
            rgba(0,0,0,0.06);
    }

    </style>
    """
)


# ============================================================
#                 ENCABEZADO
# ============================================================

col_titulo, col_salir = st.columns(
    [6, 1]
)

with col_salir:

    if st.button(
        "🔒 SALIR",
        use_container_width=True,
    ):

        st.session_state[
            "autenticado"
        ] = False

        st.rerun()


html(
    """
    <div class="header-box">

        <div style="
            font-size:44px;
            font-weight:900;
        ">
            🛏️ LOCAL MESITAS
        </div>

        <div style="
            font-size:19px;
            color:#cbd5e1;
            margin-top:7px;
        ">
            Sistema de Ventas • Apartados • Inventario • Caja
        </div>

        <div style="
            font-size:15px;
            color:#94a3b8;
            margin-top:8px;
        ">
            💼 Todo en un solo lugar
        </div>

    </div>
    """
)


# ============================================================
#                 RESUMEN
# ============================================================

dinero_recibido = (
    float(
        df_ventas[
            "ABONADO"
        ].sum()
    )
    if not df_ventas.empty
    else 0.0
)

total_operaciones = len(
    df_ventas
)

total_apartados = contar_apartados(
    df_ventas
)

total_stock = (
    int(
        df_inv[
            "STOCK"
        ].sum()
    )
    if not df_inv.empty
    else 0
)


r1, r2, r3, r4 = st.columns(
    4
)


with r1:

    html(
        f"""
        <div class="info-card">

            <div style="
                font-size:15px;
                color:#64748b;
                font-weight:800;
            ">
                💰 DINERO RECIBIDO
            </div>

            <div style="
                font-size:29px;
                font-weight:900;
                color:#0f172a;
            ">
                ${dinero_recibido:,.2f}
            </div>

        </div>
        """
    )


with r2:

    html(
        f"""
        <div class="info-card">

            <div style="
                font-size:15px;
                color:#64748b;
                font-weight:800;
            ">
                📦 PRODUCTOS EN STOCK
            </div>

            <div style="
                font-size:29px;
                font-weight:900;
                color:#0f172a;
            ">
                {total_stock}
            </div>

        </div>
        """
    )


with r3:

    html(
        f"""
        <div class="info-card">

            <div style="
                font-size:15px;
                color:#64748b;
                font-weight:800;
            ">
                🧾 OPERACIONES
            </div>

            <div style="
                font-size:29px;
                font-weight:900;
                color:#0f172a;
            ">
                {total_operaciones}
            </div>

        </div>
        """
    )


with r4:

    html(
        f"""
        <div class="info-card">

            <div style="
                font-size:15px;
                color:#64748b;
                font-weight:800;
            ">
                📦 APARTADOS ACTIVOS
            </div>

            <div style="
                font-size:29px;
                font-weight:900;
                color:#0f172a;
            ">
                {total_apartados}
            </div>

        </div>
        """
    )


st.write("")


# ============================================================
#                 MENÚ
# ============================================================

tab_venta, tab_apartado, tab_inventario, tab_historial = st.tabs(
    [
        "⚡ VENDER",
        "📦 APARTADOS",
        "🛠️ INVENTARIO",
        "📜 HISTORIAL",
    ]
)


# ============================================================
#                 TAB 1 - VENDER
# ============================================================

with tab_venta:

    html(
        """
        <div style="
            background:
            linear-gradient(
                135deg,
                #ffffff,
                #eff6ff
            );

            padding:25px;
            border-radius:22px;
            border:1px solid #dbeafe;
            margin-bottom:20px;
        ">

            <div style="
                font-size:32px;
                font-weight:900;
                color:#0f172a;
            ">
                ⚡ VENDER PRODUCTO O COMBO
            </div>

            <div style="
                font-size:16px;
                color:#64748b;
                margin-top:6px;
            ">
                Elija el tipo de producto o seleccione la opción de Combo
                para vender Cama + Colchón.
            </div>

        </div>
        """
    )


    if df_inv.empty:

        st.info(
            "📦 No hay productos registrados."
        )

    else:

        st.markdown(
            "### 📦 1. Productos disponibles"
        )

        # ----------------------------------------------------
        # MOSTRAR CATEGORÍAS
        # ----------------------------------------------------

        categorias = [
            nombre
            for nombre
            in df_inv["CATEGORIA"].tolist()
            if " - " not in str(nombre)
        ]

        for principal in categorias:

            subproductos = obtener_subproductos(
                df_inv,
                principal,
            )

            # ------------------------------------------------
            # CATEGORÍA CON SUBPRODUCTOS
            # ------------------------------------------------

            if not subproductos.empty:

                html(
                    f"""
                    <div class="product-card"
                         style="min-height:165px;">

                        <div style="
                            font-size:55px;
                        ">
                            {obtener_icono(principal)}
                        </div>

                        <div style="
                            font-size:27px;
                            font-weight:900;
                            color:#0f172a;
                        ">
                            {principal}
                        </div>

                        <div style="
                            font-size:18px;
                            color:#64748b;
                            margin-top:8px;
                        ">
                            {len(subproductos)}
                            tipos disponibles
                        </div>

                        <div style="
                            font-size:14px;
                            color:#2563eb;
                            font-weight:900;
                            margin-top:7px;
                        ">
                            👇 Cada tipo tiene su propio precio
                        </div>

                    </div>
                    """
                )

                columnas = st.columns(
                    min(
                        max(
                            len(subproductos),
                            1,
                        ),
                        4,
                    )
                )

                for indice_sub, (
                    _,
                    sub,
                ) in enumerate(
                    subproductos.iterrows()
                ):

                    with columnas[
                        indice_sub
                        % len(columnas)
                    ]:

                        stock_sub = max(
                            0,
                            int(
                                sub[
                                    "STOCK"
                                ]
                            ),
                        )

                        precio_sub = float(
                            sub[
                                "PRECIO"
                            ]
                        )

                        estado_sub, color_sub = (
                            estado_stock(
                                stock_sub
                            )
                        )

                        nombre_completo = str(
                            sub[
                                "CATEGORIA"
                            ]
                        )

                        nombre_mostrar = (
                            nombre_completo
                            .replace(
                                principal
                                + " - ",
                                "",
                                1,
                            )
                        )

                        html(
                            f"""
                            <div class="product-card">

                                <div style="
                                    font-size:45px;
                                ">
                                    {obtener_icono(
                                        nombre_completo
                                    )}
                                </div>

                                <div style="
                                    font-size:18px;
                                    font-weight:900;
                                    color:#0f172a;
                                    min-height:45px;
                                ">
                                    {nombre_mostrar}
                                </div>

                                <div style="
                                    font-size:28px;
                                    font-weight:900;
                                    color:#1e3a8a;
                                    margin-top:8px;
                                ">
                                    ${precio_sub:,.2f}
                                </div>

                                <div style="
                                    font-size:15px;
                                    color:#64748b;
                                    margin-top:5px;
                                ">
                                    📦 {stock_sub}
                                    unidades
                                </div>

                                <div style="
                                    font-size:13px;
                                    font-weight:900;
                                    color:{color_sub};
                                    margin-top:8px;
                                ">
                                    {estado_sub}
                                </div>

                            </div>
                            """
                        )

            # ------------------------------------------------
            # PRODUCTO NORMAL
            # ------------------------------------------------

            else:

                fila_normal = df_inv[
                    df_inv[
                        "CATEGORIA"
                    ]
                    == principal
                ]

                if not fila_normal.empty:

                    fila_normal = (
                        fila_normal.iloc[0]
                    )

                    stock = max(
                        0,
                        int(
                            fila_normal[
                                "STOCK"
                            ]
                        ),
                    )

                    precio = float(
                        fila_normal[
                            "PRECIO"
                        ]
                    )

                    estado, color = (
                        estado_stock(
                            stock
                        )
                    )

                    html(
                        f"""
                        <div class="product-card"
                             style="max-width:320px;">

                            <div style="
                                font-size:55px;
                            ">
                                {obtener_icono(
                                    principal
                                )}
                            </div>

                            <div style="
                                font-size:20px;
                                font-weight:900;
                                color:#0f172a;
                            ">
                                {principal}
                            </div>

                            <div style="
                                font-size:29px;
                                font-weight:900;
                                color:#1e3a8a;
                                margin-top:8px;
                            ">
                                ${precio:,.2f}
                            </div>

                            <div style="
                                font-size:16px;
                                color:#64748b;
                            ">
                                📦 {stock} unidades
                            </div>

                            <div style="
                                font-size:13px;
                                font-weight:900;
                                color:{color};
                                margin-top:8px;
                            ">
                                {estado}
                            </div>

                        </div>
                        """
                    )


        st.markdown("---")

        # ----------------------------------------------------
        # SELECCIONAR PRODUCTO / COMBO
        # ----------------------------------------------------

        lista_productos = (
            obtener_productos_vendibles(
                df_inv
            )
        )

        OPCION_COMBO = "🎁 Combo (Cama + Colchón)"
        opciones_venta = [OPCION_COMBO] + lista_productos

        producto_elegido = (
            st.selectbox(
                "👉 Seleccione lo que desea vender",
                opciones_venta,
                key="venta_producto_final",
            )
        )

        es_combo = (producto_elegido == OPCION_COMBO)

        if es_combo:
            camas_disp = [
                p for p in df_inv["CATEGORIA"].tolist()
                if "cama" in p.lower() and producto_es_vendible(df_inv, p)
            ]
            colchones_disp = [
                p for p in df_inv["CATEGORIA"].tolist()
                if ("colchon" in p.lower() or "colchón" in p.lower()) and producto_es_vendible(df_inv, p)
            ]

            if not camas_disp or not colchones_disp:
                st.error("⚠️ Debe tener al menos una Cama y un Colchón registrados en el inventario para formar un combo.")
                st.stop()

            st.info("💡 Al vender un combo se descontará **1 unidad** de la Cama seleccionada y **1 unidad** del Colchón seleccionado.")

            col_cama, col_colchon = st.columns(2)
            with col_cama:
                cama_combo = st.selectbox("🛏️ Seleccionar Cama del combo", camas_disp, key="combo_cama_sel")
                fila_cama = df_inv[df_inv["CATEGORIA"] == cama_combo].iloc[0]
                stock_cama = int(fila_cama["STOCK"])
                st.caption(f"Stock disponible de Cama: **{stock_cama}**")

            with col_colchon:
                colchon_combo = st.selectbox("💤 Seleccionar Colchón del combo", colchones_disp, key="combo_colchon_sel")
                fila_colchon = df_inv[df_inv["CATEGORIA"] == colchon_combo].iloc[0]
                stock_colchon = int(fila_colchon["STOCK"])
                st.caption(f"Stock disponible de Colchón: **{stock_colchon}**")

            sugerido = float(fila_cama["PRECIO"]) + float(fila_colchon["PRECIO"])

            precio_combo = st.number_input(
                "🏷️ Precio especial del Combo ($)",
                min_value=0.0,
                value=sugerido,
                step=5.0,
                key="precio_combo_input",
                help="Puede ajustar el precio de oferta del combo si aplica un valor diferente a la suma."
            )

            html(
                f"""
                <div style="
                    background:white;
                    border:2px solid #cbd5e1;
                    border-radius:18px;
                    padding:18px;
                    margin:10px 0 20px 0;
                ">
                    <div style="font-size:24px; font-weight:900;">
                        🎁 COMBO SELECCIONADO
                    </div>
                    <div style="font-size:17px; margin-top:8px;">
                        • Cama: <b>{cama_combo}</b> (Stock: {stock_cama})<br>
                        • Colchón: <b>{colchon_combo}</b> (Stock: {stock_colchon})<br>
                        • Precio especial: <b>${precio_combo:,.2f}</b>
                    </div>
                </div>
                """
            )

            stock_disponible = min(stock_cama, stock_colchon)
            precio_producto = precio_combo
            nombre_producto_visible = f"Combo ({cama_combo} + {colchon_combo})"

        else:

            fila_producto = df_inv[
                df_inv[
                    "CATEGORIA"
                ]
                == producto_elegido
            ].iloc[0]

            stock_disponible = max(
                0,
                int(
                    fila_producto[
                        "STOCK"
                    ]
                ),
            )

            precio_producto = float(
                fila_producto[
                    "PRECIO"
                ]
            )

            nombre_producto_visible = (
                producto_elegido
            )

            if " - " in producto_elegido:

                nombre_producto_visible = (
                    producto_elegido.split(
                        " - ",
                        1,
                    )[1]
                )

            html(
                f"""
                <div style="
                    background:white;
                    border:2px solid #cbd5e1;
                    border-radius:18px;
                    padding:18px;
                    margin:10px 0 20px 0;
                ">

                    <div style="
                        font-size:24px;
                        font-weight:900;
                    ">
                        {obtener_icono(
                            producto_elegido
                        )}
                        {nombre_producto_visible}
                    </div>

                    <div style="
                        font-size:18px;
                        margin-top:8px;
                    ">
                        💰 Precio de venta:
                        <b>
                            ${precio_producto:,.2f}
                        </b>
                    </div>

                    <div style="
                        font-size:18px;
                        margin-top:5px;
                    ">
                        📦 Existencia:
                        <b>
                            {stock_disponible}
                            unidades
                        </b>
                    </div>

                </div>
                """
            )


        if stock_disponible <= 0:

            st.error(
                f"🔴 **{nombre_producto_visible} "
                "no tiene suficiente stock.** "
                "Entre a INVENTARIO para agregar existencias."
            )

        else:

            with st.form(
                "form_venta_principal"
            ):

                st.markdown(
                    "### 🧾 2. Datos de la venta"
                )

                a1, a2, a3 = (
                    st.columns(3)
                )

                with a1:

                    if es_combo:
                        cantidad = 1
                        st.number_input("🔢 Cantidad (Combos)", value=1, disabled=True)
                    else:
                        cantidad = (
                            st.number_input(
                                "🔢 Cantidad",
                                min_value=1,
                                max_value=(
                                    stock_disponible
                                ),
                                value=1,
                                step=1,
                            )
                        )

                with a2:

                    metodo_pago = (
                        st.selectbox(
                            "💳 Forma de pago",
                            [
                                "Efectivo",
                                "Transferencia",
                                "Tarjeta",
                            ],
                        )
                    )

                with a3:

                    descuento = (
                        st.number_input(
                            "🏷️ Descuento",
                            min_value=0.0,
                            max_value=100.0,
                            value=0.0,
                            step=1.0,
                        )
                    )

                st.markdown(
                    "### 👤 3. Datos del cliente"
                )

                nombre_cliente = (
                    st.text_input(
                        "👤 Nombre",
                        value="Cliente General",
                    )
                )

                b1, b2 = st.columns(
                    2
                )

                with b1:

                    cedula_cliente = (
                        st.text_input(
                            "🆔 Cédula / RUC",
                            value="S/N",
                        )
                    )

                with b2:

                    telefono_cliente = (
                        st.text_input(
                            "📞 Teléfono",
                            value="",
                        )
                    )

                correo_cliente = (
                    st.text_input(
                        "📧 Correo electrónico",
                        value="",
                    )
                )

                direccion_cliente = (
                    st.text_input(
                        "📍 Dirección de entrega",
                        value="",
                    )
                )

                foto_venta = (
                    st.file_uploader(
                        "📸 Foto del producto (opcional)",
                        type=[
                            "jpg",
                            "jpeg",
                            "png",
                        ],
                        key="foto_venta_principal",
                    )
                )

                subtotal = (
                    cantidad
                    * precio_producto
                )

                total = max(
                    0.0,
                    subtotal
                    - descuento,
                )

                html(
                    f"""
                    <div class="total-card">

                        <div style="
                            font-size:15px;
                            color:#64748b;
                            font-weight:900;
                        ">
                            ✅ 4. TOTAL DE LA VENTA
                        </div>

                        <div style="
                            font-size:20px;
                            font-weight:900;
                            margin:8px 0;
                        ">
                            {cantidad} ×
                            {nombre_producto_visible}
                        </div>

                        <div style="
                            color:#475569;
                        ">
                            Subtotal:
                            <b>
                                ${subtotal:,.2f}
                            </b>
                        </div>

                        <div style="
                            color:#dc2626;
                        ">
                            Descuento:
                            <b>
                                -${descuento:,.2f}
                            </b>
                        </div>

                        <div style="
                            font-size:44px;
                            font-weight:900;
                            color:#1d4ed8;
                            margin-top:7px;
                        ">
                            ${total:,.2f}
                        </div>

                    </div>
                    """
                )

                st.write("")

                confirmar_venta = (
                    st.form_submit_button(
                        "💰 COBRAR Y GUARDAR VENTA",
                        use_container_width=True,
                    )
                )

                if confirmar_venta:

                    if not nombre_cliente.strip():

                        st.warning(
                            "⚠️ Escriba el nombre del cliente."
                        )

                    elif cantidad > stock_disponible:

                        st.error(
                            "❌ No hay suficiente stock."
                        )

                    else:

                        ruta_foto = (
                            guardar_foto(
                                foto_venta
                            )
                        )

                        if es_combo:
                            idx_cama = df_inv[df_inv["CATEGORIA"] == cama_combo].index[0]
                            idx_colchon = df_inv[df_inv["CATEGORIA"] == colchon_combo].index[0]

                            df_inv.loc[idx_cama, "STOCK"] = max(0, int(df_inv.loc[idx_cama, "STOCK"]) - 1)
                            df_inv.loc[idx_colchon, "STOCK"] = max(0, int(df_inv.loc[idx_colchon, "STOCK"]) - 1)

                            guardar_csv(df_inv, FILE_INV)
                            cat_guardar = f"COMBO: {cama_combo} + {colchon_combo}"
                            msj_exito_det = f"🎉 Venta de Combo registrada a ${precio_producto:,.2f}. Se descontó 1 unidad de {cama_combo} y 1 de {colchon_combo}."

                        else:

                            indice_producto = (
                                df_inv[
                                    df_inv[
                                        "CATEGORIA"
                                    ]
                                    == producto_elegido
                                ].index[0]
                            )

                            nuevo_stock = max(
                                0,
                                int(
                                    df_inv.loc[
                                        indice_producto,
                                        "STOCK",
                                    ]
                                )
                                - cantidad,
                            )

                            df_inv.loc[
                                indice_producto,
                                "STOCK",
                            ] = nuevo_stock

                            guardar_csv(
                                df_inv,
                                FILE_INV,
                            )

                            cat_guardar = producto_elegido
                            msj_exito_det = f"🎉 Venta guardada. Quedan {nuevo_stock} unidades de {nombre_producto_visible}."

                        fecha = (
                            datetime.now()
                            .strftime(
                                "%Y-%m-%d %H:%M"
                            )
                        )

                        nueva_venta = (
                            pd.DataFrame(
                                [
                                    {
                                        "FECHA": fecha,
                                        "CATEGORIA": cat_guardar,
                                        "CANTIDAD": cantidad,
                                        "PRECIO_UNITARIO": precio_producto,
                                        "TOTAL": total,
                                        "ABONADO": total,
                                        "SALDO_PENDIENTE": 0.0,
                                        "METODO_PAGO": metodo_pago,
                                        "CLIENTE": nombre_cliente,
                                        "CEDULA": cedula_cliente,
                                        "TELEFONO": telefono_cliente,
                                        "CORREO": correo_cliente,
                                        "DIRECCION": direccion_cliente,
                                        "ESTADO": "Pagado y Entregado",
                                        "FOTO": ruta_foto,
                                    }
                                ]
                            )
                        )

                        df_ventas = pd.concat(
                            [
                                df_ventas,
                                nueva_venta,
                            ],
                            ignore_index=True,
                        )

                        guardar_csv(
                            df_ventas,
                            FILE_VENTAS,
                        )

                        cuerpo = (
                            "NUEVA VENTA REGISTRADA\n\n"
                            f"Cliente: {nombre_cliente}\n"
                            f"Producto: {cantidad}x "
                            f"{cat_guardar}\n"
                            f"Precio unitario: "
                            f"${precio_producto:,.2f}\n"
                            f"Descuento: "
                            f"${descuento:,.2f}\n"
                            f"Total: "
                            f"${total:,.2f}\n"
                            f"Forma de pago: "
                            f"{metodo_pago}\n"
                            f"Dirección: "
                            f"{direccion_cliente}\n"
                            f"Fecha: {fecha}"
                        )

                        enviar_correo_venta(
                            correo_cliente,
                            "🧾 Recibo de Compra - Local Mesitas",
                            cuerpo,
                            ruta_foto,
                        )

                        st.session_state[
                            "ultima_operacion_whatsapp"
                        ] = {
                            "mensaje": (
                                "🚨 *NUEVA VENTA REGISTRADA* 🛏️\n\n"
                                f"👤 *Cliente:* "
                                f"{nombre_cliente}\n"
                                f"📞 *Tel:* "
                                f"{telefono_cliente or 'N/A'}\n"
                                f"📦 *Producto:* "
                                f"{cantidad}x "
                                f"{cat_guardar}\n"
                                f"💰 *Total:* "
                                f"${total:,.2f}\n"
                                f"💳 *Pago:* "
                                f"{metodo_pago}\n"
                                f"📍 *Dirección:* "
                                f"{direccion_cliente}\n"
                                f"📅 *Fecha:* "
                                f"{fecha}"
                            )
                        }

                        st.session_state[
                            "mensaje_exito"
                        ] = msj_exito_det

                        st.balloons()

                        st.rerun()


# ============================================================
#                 WHATSAPP
# ============================================================

if (
    "ultima_operacion_whatsapp"
    in st.session_state
):

    mensaje_ws = (
        st.session_state[
            "ultima_operacion_whatsapp"
        ][
            "mensaje"
        ]
    )

    enlace1 = generar_link_whatsapp(
        NUMERO_1,
        mensaje_ws,
    )

    enlace2 = generar_link_whatsapp(
        NUMERO_2,
        mensaje_ws,
    )

    html(
        f"""
        <div style="
            background:#ecfdf5;
            border:2px solid #22c55e;
            padding:25px;
            border-radius:20px;
            text-align:center;
            margin-top:20px;
        ">

            <div style="
                font-size:28px;
                font-weight:900;
                color:#15803d;
            ">
                📱 NOTIFICACIÓN LISTA
            </div>

            <div style="
                font-size:16px;
                color:#475569;
                margin:10px 0 20px 0;
            ">
                Presione un botón para enviar
                el reporte por WhatsApp.
            </div>

            <a href="{enlace1}"
               target="_blank"
               style="
                    background:#25d366;
                    color:white;
                    padding:15px 22px;
                    border-radius:14px;
                    text-decoration:none;
                    font-weight:900;
                    display:inline-block;
                    margin:5px;
               ">
                💬 WHATSAPP 1
            </a>

            <a href="{enlace2}"
               target="_blank"
               style="
                    background:#128c7e;
                    color:white;
                    padding:15px 22px;
                    border-radius:14px;
                    text-decoration:none;
                    font-weight:900;
                    display:inline-block;
                    margin:5px;
               ">
                💬 WHATSAPP 2
            </a>

        </div>
        """
    )

    if st.button(
        "✖️ CERRAR NOTIFICACIÓN",
        key="cerrar_whatsapp",
    ):

        del st.session_state[
            "ultima_operacion_whatsapp"
        ]

        st.rerun()


if (
    "mensaje_exito"
    in st.session_state
):

    st.success(
        st.session_state[
            "mensaje_exito"
        ]
    )

    if st.button(
        "✖️ Cerrar mensaje",
        key="cerrar_mensaje_exito",
    ):

        del st.session_state[
            "mensaje_exito"
        ]

        st.rerun()


# ============================================================
#                 TAB 2 - APARTADOS
# ============================================================

with tab_apartado:

    html(
        """
        <div style="
            background:
            linear-gradient(
                135deg,
                #ffffff,
                #f0fdf4
            );

            padding:25px;
            border-radius:22px;
            border:1px solid #bbf7d0;
            margin-bottom:20px;
        ">

            <div style="
                font-size:32px;
                font-weight:900;
                color:#0f172a;
            ">
                📦 APARTADOS Y ABONOS
            </div>

            <div style="
                font-size:16px;
                color:#64748b;
                margin-top:6px;
            ">
                Registre el apartado y luego
                los pagos del cliente.
            </div>

        </div>
        """
    )


    with st.expander(
        "➕ CREAR NUEVO APARTADO",
        expanded=True,
    ):

        productos_para_apartar = (
            obtener_productos_vendibles(
                df_inv
            )
        )

        if not productos_para_apartar:

            st.info(
                "No existen productos para apartar."
            )

        else:

            producto_apartado = (
                st.selectbox(
                    "📦 1. Producto",
                    productos_para_apartar,
                    key="producto_apartado",
                )
            )

            fila_apartado = df_inv[
                df_inv[
                    "CATEGORIA"
                ]
                == producto_apartado
            ].iloc[0]

            stock_apartado = max(
                0,
                int(
                    fila_apartado[
                        "STOCK"
                    ]
                ),
            )

            precio_apartado = float(
                fila_apartado[
                    "PRECIO"
                ]
            )

            nombre_apartado_visible = (
                producto_apartado
            )

            if " - " in producto_apartado:

                nombre_apartado_visible = (
                    producto_apartado.split(
                        " - ",
                        1,
                    )[1]
                )

            st.info(
                f"💰 Precio: "
                f"**${precio_apartado:,.2f}**  |  "
                f"📦 Stock: "
                f"**{stock_apartado}**"
            )

            with st.form(
                "form_nuevo_apartado"
            ):

                st.markdown(
                    "### 👤 2. Datos del cliente"
                )

                cliente_apartado = (
                    st.text_input(
                        "👤 Nombre y apellido"
                    )
                )

                c1, c2 = st.columns(
                    2
                )

                with c1:

                    cedula_apartado = (
                        st.text_input(
                            "🆔 Cédula / DNI"
                        )
                    )

                with c2:

                    telefono_apartado = (
                        st.text_input(
                            "📞 Teléfono"
                        )
                    )

                correo_apartado = (
                    st.text_input(
                        "📧 Correo electrónico"
                    )
                )

                direccion_apartado = (
                    st.text_input(
                        "📍 Dirección"
                    )
                )

                st.markdown(
                    "### 💵 3. Cantidad y abono"
                )

                a1, a2 = st.columns(
                    2
                )

                with a1:

                    cantidad_apartado = (
                        st.number_input(
                            "🔢 Cantidad",
                            min_value=1,
                            max_value=max(
                                1,
                                stock_apartado,
                            ),
                            value=1,
                            step=1,
                        )
                    )

                with a2:

                    abono_inicial = (
                        st.number_input(
                            "💵 Abono de hoy",
                            min_value=0.0,
                            value=10.0,
                            step=5.0,
                        )
                    )

                foto_apartado = (
                    st.file_uploader(
                        "📸 Foto del producto (opcional)",
                        type=[
                            "jpg",
                            "jpeg",
                            "png",
                        ],
                        key="foto_apartado_final",
                    )
                )

                total_apartado = (
                    cantidad_apartado
                    * precio_apartado
                )

                saldo_apartado = max(
                    0.0,
                    total_apartado
                    - abono_inicial,
                )

                html(
                    f"""
                    <div class="total-card">

                        <div style="
                            font-weight:900;
                            color:#64748b;
                        ">
                            📋 RESUMEN DEL APARTADO
                        </div>

                        <div style="
                            font-size:27px;
                            font-weight:900;
                        ">
                            ${total_apartado:,.2f}
                        </div>

                        <div style="
                            color:#16a34a;
                            font-size:18px;
                        ">
                            ✅ Abono:
                            ${abono_inicial:,.2f}
                        </div>

                        <div style="
                            color:#dc2626;
                            font-size:23px;
                            font-weight:900;
                            margin-top:5px;
                        ">
                            🔴 Falta:
                            ${saldo_apartado:,.2f}
                        </div>

                    </div>
                    """
                )

                guardar_apartado = (
                    st.form_submit_button(
                        "💾 GUARDAR APARTADO",
                        use_container_width=True,
                    )
                )

                if guardar_apartado:

                    if not cliente_apartado.strip():

                        st.warning(
                            "⚠️ Escriba el nombre del cliente."
                        )

                    elif (
                        abono_inicial
                        > total_apartado
                    ):

                        st.error(
                            "❌ El abono no puede ser mayor que el total."
                        )

                    elif (
                        cantidad_apartado
                        > stock_apartado
                    ):

                        st.error(
                            "❌ No hay suficiente stock."
                        )

                    else:

                        ruta_foto_ap = (
                            guardar_foto(
                                foto_apartado,
                                "ap_",
                            )
                        )

                        estado_ap = (
                            "Pagado y Entregado"
                            if saldo_apartado <= 0
                            else "Apartado (Pendiente)"
                        )

                        fecha_ap = (
                            datetime.now()
                            .strftime(
                                "%Y-%m-%d %H:%M"
                            )
                        )

                        nuevo_apartado = (
                            pd.DataFrame(
                                [
                                    {
                                        "FECHA": fecha_ap,
                                        "CATEGORIA": producto_apartado,
                                        "CANTIDAD": cantidad_apartado,
                                        "PRECIO_UNITARIO": precio_apartado,
                                        "TOTAL": total_apartado,
                                        "ABONADO": abono_inicial,
                                        "SALDO_PENDIENTE": saldo_apartado,
                                        "METODO_PAGO": "Efectivo",
                                        "CLIENTE": cliente_apartado,
                                        "CEDULA": cedula_apartado,
                                        "TELEFONO": telefono_apartado,
                                        "CORREO": correo_apartado,
                                        "DIRECCION": direccion_apartado,
                                        "ESTADO": estado_ap,
                                        "FOTO": ruta_foto_ap,
                                    }
                                ]
                            )
                        )

                        if saldo_apartado <= 0:

                            indice = df_inv[
                                df_inv[
                                    "CATEGORIA"
                                ]
                                == producto_apartado
                            ].index[0]

                            df_inv.loc[
                                indice,
                                "STOCK",
                            ] = max(
                                0,
                                int(
                                    df_inv.loc[
                                        indice,
                                        "STOCK",
                                    ]
                                )
                                - cantidad_apartado,
                            )

                            guardar_csv(
                                df_inv,
                                FILE_INV,
                            )

                        df_ventas = pd.concat(
                            [
                                df_ventas,
                                nuevo_apartado,
                            ],
                            ignore_index=True,
                        )

                        guardar_csv(
                            df_ventas,
                            FILE_VENTAS,
                        )

                        cuerpo_ap = (
                            "NUEVO APARTADO\n\n"
                            f"Cliente: "
                            f"{cliente_apartado}\n"
                            f"Producto: "
                            f"{cantidad_apartado}x "
                            f"{producto_apartado}\n"
                            f"Total: "
                            f"${total_apartado:,.2f}\n"
                            f"Abono: "
                            f"${abono_inicial:,.2f}\n"
                            f"Saldo: "
                            f"${saldo_apartado:,.2f}"
                        )

                        enviar_correo_venta(
                            correo_apartado,
                            "🧾 Recibo de Apartado - Local Mesitas",
                            cuerpo_ap,
                            ruta_foto_ap,
                        )

                        st.session_state[
                            "ultima_operacion_whatsapp"
                        ] = {
                            "mensaje": (
                                "📦 *NUEVO APARTADO REGISTRADO*\n\n"
                                f"👤 *Cliente:* "
                                f"{cliente_apartado}\n"
                                f"📞 *Tel:* "
                                f"{telefono_apartado or 'N/A'}\n"
                                f"📦 *Producto:* "
                                f"{cantidad_apartado}x "
                                f"{producto_apartado}\n"
                                f"💰 *Total:* "
                                f"${total_apartado:,.2f}\n"
                                f"📥 *Abono:* "
                                f"${abono_inicial:,.2f}\n"
                                f"🔴 *Saldo:* "
                                f"${saldo_apartado:,.2f}\n"
                                f"📌 *Estado:* "
                                f"{estado_ap}"
                            )
                        }

                        st.session_state[
                            "mensaje_exito"
                        ] = (
                            "✅ Apartado guardado correctamente."
                        )

                        st.rerun()


    st.markdown("---")

    st.markdown(
        "### 📋 5. Apartados pendientes"
    )

    pendientes = df_ventas[
        df_ventas[
            "ESTADO"
        ]
        .astype(str)
        .str.contains(
            "Apartado",
            case=False,
            na=False,
        )
    ]

    if pendientes.empty:

        st.success(
            "✨ No hay apartados pendientes."
        )

    else:

        opciones_ap = [
            (
                f"Fila {i} | "
                f"{r['CLIENTE']} | "
                f"{r['CATEGORIA']} | "
                f"Debe: "
                f"${float(r['SALDO_PENDIENTE']):,.2f}"
            )
            for i, r
            in pendientes.iterrows()
        ]

        seleccion_ap = (
            st.selectbox(
                "🔍 Seleccione al cliente",
                opciones_ap,
                key="seleccionar_apartado",
            )
        )

        indice_ap = int(
            seleccion_ap
            .split(" | ")[0]
            .replace(
                "Fila ",
                "",
            )
        )

        registro_ap = df_ventas.loc[
            indice_ap
        ]

        col_datos, col_foto = (
            st.columns([1.5, 1])
        )

        with col_datos:

            html(
                f"""
                <div class="receipt-card">

                    <div style="
                        font-size:28px;
                        font-weight:900;
                        color:#2563eb;
                    ">
                        🧾 RECIBO
                    </div>

                    <p>
                        <b>📅 Fecha:</b>
                        {registro_ap["FECHA"]}
                    </p>

                    <p>
                        <b>👤 Cliente:</b>
                        {registro_ap["CLIENTE"]}
                    </p>

                    <p>
                        <b>📞 Teléfono:</b>
                        {registro_ap["TELEFONO"]}
                    </p>

                    <p>
                        <b>🆔 Cédula:</b>
                        {registro_ap["CEDULA"]}
                    </p>

                    <p>
                        <b>📍 Dirección:</b>
                        {registro_ap["DIRECCION"]}
                    </p>

                    <hr>

                    <p>
                        <b>📦 Producto:</b>
                        {registro_ap["CANTIDAD"]}x
                        {registro_ap["CATEGORIA"]}
                    </p>

                    <p>
                        <b>💰 Total:</b>
                        ${float(registro_ap["TOTAL"]):,.2f}
                    </p>

                    <p style="
                        color:#16a34a;
                    ">
                        <b>✅ Abonado:</b>
                        ${float(registro_ap["ABONADO"]):,.2f}
                    </p>

                    <p style="
                        color:#dc2626;
                        font-size:25px;
                        font-weight:900;
                    ">
                        🔴 Falta:
                        ${float(registro_ap["SALDO_PENDIENTE"]):,.2f}
                    </p>

                </div>
                """
            )

        with col_foto:

            st.markdown(
                "### 🖼️ Foto"
            )

            ruta = str(
                registro_ap.get(
                    "FOTO",
                    "Sin foto",
                )
            )

            if (
                ruta != "Sin foto"
                and os.path.exists(ruta)
            ):

                st.image(
                    ruta,
                    caption=str(
                        registro_ap[
                            "CATEGORIA"
                        ]
                    ),
                    use_container_width=True,
                )

            else:

                st.info(
                    "📷 No hay foto."
                )

        saldo_actual = float(
            registro_ap[
                "SALDO_PENDIENTE"
            ]
        )

        with st.form(
            f"form_abono_{indice_ap}"
        ):

            st.markdown(
                "### 💵 Registrar nuevo abono"
            )

            abono_hoy = (
                st.number_input(
                    "¿Cuánto dinero trae el cliente?",
                    min_value=0.0,
                    max_value=saldo_actual,
                    value=saldo_actual,
                    step=5.0,
                )
            )

            registrar_abono = (
                st.form_submit_button(
                    "📥 GUARDAR ABONO",
                    use_container_width=True,
                )
            )

            if registrar_abono:

                nuevo_abonado = (
                    float(
                        registro_ap[
                            "ABONADO"
                        ]
                    )
                    + abono_hoy
                )

                nuevo_saldo = max(
                    0.0,
                    saldo_actual
                    - abono_hoy,
                )

                df_ventas.loc[
                    indice_ap,
                    "ABONADO",
                ] = nuevo_abonado

                df_ventas.loc[
                    indice_ap,
                    "SALDO_PENDIENTE",
                ] = nuevo_saldo

                if nuevo_saldo <= 0:

                    df_ventas.loc[
                        indice_ap,
                        "ESTADO",
                    ] = (
                        "Pagado y Entregado"
                    )

                    producto_entregado = str(
                        registro_ap[
                            "CATEGORIA"
                        ]
                    )

                    if (
                        producto_entregado
                        in df_inv[
                            "CATEGORIA"
                        ].values
                    ):

                        indice_producto = (
                            df_inv[
                                df_inv[
                                    "CATEGORIA"
                                ]
                                == producto_entregado
                            ].index[0]
                        )

                        cantidad_entregar = int(
                            registro_ap[
                                "CANTIDAD"
                            ]
                        )

                        stock_nuevo = max(
                            0,
                            int(
                                df_inv.loc[
                                    indice_producto,
                                    "STOCK",
                                ]
                            )
                            - cantidad_entregar,
                        )

                        df_inv.loc[
                            indice_producto,
                            "STOCK",
                        ] = stock_nuevo

                        guardar_csv(
                            df_inv,
                            FILE_INV,
                        )

                    mensaje_pago = (
                        "🎉 DEUDA SALDADA. "
                        "El producto está listo para entregar."
                    )

                else:

                    df_ventas.loc[
                        indice_ap,
                        "ESTADO",
                    ] = (
                        "Apartado (Pendiente)"
                    )

                    mensaje_pago = (
                        f"✅ Abono guardado. "
                        f"Falta "
                        f"${nuevo_saldo:,.2f}."
                    )

                guardar_csv(
                    df_ventas,
                    FILE_VENTAS,
                )

                cuerpo_abono = (
                    f"Abono para "
                    f"{registro_ap['CLIENTE']}\n"
                    f"Producto: "
                    f"{registro_ap['CATEGORIA']}\n"
                    f"Abono recibido: "
                    f"${abono_hoy:,.2f}\n"
                    f"Saldo nuevo: "
                    f"${nuevo_saldo:,.2f}\n"
                    f"Estado: "
                    f"{df_ventas.loc[indice_ap, 'ESTADO']}"
                )

                enviar_correo_venta(
                    registro_ap[
                        "CORREO"
                    ],
                    "🧾 Comprobante de Abono - Local Mesitas",
                    cuerpo_abono,
                    registro_ap[
                        "FOTO"
                    ],
                )

                st.session_state[
                    "ultima_operacion_whatsapp"
                ] = {
                    "mensaje": (
                        "💵 *NUEVO ABONO REGISTRADO*\n\n"
                        f"👤 *Cliente:* "
                        f"{registro_ap['CLIENTE']}\n"
                        f"📦 *Producto:* "
                        f"{registro_ap['CATEGORIA']}\n"
                        f"📥 *Abono:* "
                        f"${abono_hoy:,.2f}\n"
                        f"🔴 *Saldo:* "
                        f"${nuevo_saldo:,.2f}\n"
                        f"📌 *Estado:* "
                        f"{df_ventas.loc[indice_ap, 'ESTADO']}"
                    )
                }

                st.session_state[
                    "mensaje_exito"
                ] = mensaje_pago

                st.rerun()


# ============================================================
#                 TAB 3 - INVENTARIO
# ============================================================

with tab_inventario:

    html(
        """
        <div style="
            background:
            linear-gradient(
                135deg,
                #ffffff,
                #fff7ed
            );

            padding:25px;
            border-radius:22px;
            border:1px solid #fed7aa;
            margin-bottom:20px;
        ">

            <div style="
                font-size:32px;
                font-weight:900;
                color:#0f172a;
            ">
                🛠️ INVENTARIO
            </div>

            <div style="
                font-size:16px;
                color:#64748b;
                margin-top:6px;
            ">
                Aquí puede cambiar precios,
                agregar productos y aumentar existencias.
            </div>

        </div>
        """
    )

    # ALERTA DE STOCK EXCLUSIVA DE ESTA SECCIÓN
    stock_critico = df_inv[
        (df_inv["STOCK"] <= 2) &
        (df_inv.apply(lambda r: producto_es_vendible(df_inv, r["CATEGORIA"]), axis=1))
    ]

    if not stock_critico.empty:
        lista_criticos = ", ".join(
            [
                f"{r['CATEGORIA']} ({int(r['STOCK'])} ud.)"
                for _, r in stock_critico.iterrows()
            ]
        )
        st.warning(f"⚠️ **PRODUCTOS CON STOCK BAJO O AGOTADO:** {lista_criticos}")

    clave_admin = st.text_input(
        "🔐 Clave de administrador",
        type="password",
        key="clave_admin_inventario",
    )

    if clave_admin == CLAVE_ADMIN:

        st.success(
            "✅ Acceso concedido."
        )

        st.markdown(
            "### ✏️ 1. Cambiar stock o precio"
        )

        if not df_inv.empty:

            producto_modificar = (
                st.selectbox(
                    "📦 Producto",
                    df_inv[
                        "CATEGORIA"
                    ].tolist(),
                    key="producto_modificar",
                )
            )

            fila_mod = df_inv[
                df_inv[
                    "CATEGORIA"
                ]
                == producto_modificar
            ].iloc[0]

            m1, m2 = st.columns(
                2
            )

            with m1:

                st.info(
                    f"📦 Stock actual: "
                    f"**{int(fila_mod['STOCK'])}**"
                )

            with m2:

                if es_categoria_principal(
                    df_inv,
                    producto_modificar,
                ):

                    st.info(
                        "ℹ️ Esta categoría "
                        "usa los precios de sus subproductos."
                    )

                else:

                    st.info(
                        f"💰 Precio actual: "
                        f"**${float(fila_mod['PRECIO']):,.2f}**"
                    )

            cambio_stock = (
                st.number_input(
                    "📦 Sumar o restar stock",
                    value=0,
                    step=1,
                    help=(
                        "Ejemplo: 5 para agregar 5. "
                        "-2 para sacar 2."
                    ),
                    key="cambio_stock_inventario",
                )
            )

            if es_categoria_principal(
                df_inv,
                producto_modificar,
            ):

                st.info(
                    "💡 No se modifica el precio de "
                    "una categoría principal. "
                    "Cada subproducto tiene su propio precio."
                )

                precio_nuevo = float(
                    fila_mod["PRECIO"]
                )

            else:

                precio_nuevo = (
                    st.number_input(
                        "💰 Precio de este producto",
                        min_value=0.0,
                        value=float(
                            fila_mod["PRECIO"]
                        ),
                        step=5.0,
                        key="precio_nuevo_inventario",
                    )
                )

            if st.button(
                "💾 GUARDAR CAMBIOS",
                use_container_width=True,
            ):

                indice = df_inv[
                    df_inv[
                        "CATEGORIA"
                    ]
                    == producto_modificar
                ].index[0]

                df_inv.loc[
                    indice,
                    "STOCK",
                ] = max(
                    0,
                    int(
                        df_inv.loc[
                            indice,
                            "STOCK",
                        ]
                    )
                    + cambio_stock,
                )

                if not es_categoria_principal(
                    df_inv,
                    producto_modificar,
                ):

                    df_inv.loc[
                        indice,
                        "PRECIO",
                    ] = max(
                        0.0,
                        precio_nuevo,
                    )

                else:

                    df_inv.loc[
                        indice,
                        "PRECIO",
                    ] = 0.0

                guardar_csv(
                    df_inv,
                    FILE_INV,
                )

                st.success(
                    "✅ Cambios guardados."
                )

                st.rerun()


        st.markdown("---")

        st.markdown(
            "### ➕ 2. Agregar producto o subproducto"
        )

        st.info(
            "💡 Cada subproducto tendrá "
            "su propio precio y su propio stock."
        )

        opciones_principales = [
            nombre
            for nombre
            in df_inv[
                "CATEGORIA"
            ].tolist()
            if " - "
            not in str(nombre)
        ]

        opciones_principales.append(
            "✨ CREAR PRODUCTO NUEVO"
        )

        principal = st.selectbox(
            "📂 Producto principal",
            opciones_principales,
            key="producto_principal_nuevo",
        )

        if (
            principal
            == "✨ CREAR PRODUCTO NUEVO"
        ):

            nuevo_nombre = (
                st.text_input(
                    "📦 Nombre del producto",
                    placeholder="Ejemplo: Camas",
                    key="nuevo_nombre_producto",
                )
            )

        else:

            nuevo_subproducto = (
                st.text_input(
                    "🛏️ Nombre del subproducto",
                    placeholder=(
                        "Ejemplo: "
                        "Cama de 3 plazas"
                    ),
                    key="nuevo_subproducto",
                )
            )

            if nuevo_subproducto.strip():

                nuevo_nombre = (
                    f"{principal} - "
                    f"{nuevo_subproducto.strip()}"
                )

            else:

                nuevo_nombre = ""

        s1, s2 = st.columns(
            2
        )

        with s1:

            nuevo_stock = (
                st.number_input(
                    "📦 Stock inicial",
                    min_value=0,
                    value=1,
                    step=1,
                    key="nuevo_stock",
                )
            )

        with s2:

            nuevo_precio = (
                st.number_input(
                    "💰 Precio de ESTE producto",
                    min_value=0.0,
                    value=0.0,
                    step=5.0,
                    key="nuevo_precio",
                )
            )

        st.info(
            "💡 Ejemplo: "
            "Camas - Cama de 3 plazas "
            "→ $350.00"
        )

        if st.button(
            "➕ CREAR PRODUCTO / SUBPRODUCTO",
            use_container_width=True,
        ):

            nombre_final = (
                nuevo_nombre.strip()
            )

            if not nombre_final:

                st.warning(
                    "⚠️ Escriba el nombre."
                )

            elif nuevo_precio <= 0:

                st.warning(
                    "⚠️ Escriba un precio mayor que $0."
                )

            elif existe_producto(
                df_inv,
                nombre_final,
            ):

                st.error(
                    "❌ Ese producto ya existe."
                )

            else:

                nuevo_registro = (
                    pd.DataFrame(
                        [
                            {
                                "CATEGORIA": nombre_final,
                                "STOCK": nuevo_stock,
                                "PRECIO": nuevo_precio,
                            }
                        ]
                    )
                )

                df_inv = pd.concat(
                    [
                        df_inv,
                        nuevo_registro,
                    ],
                    ignore_index=True,
                )

                guardar_csv(
                    df_inv,
                    FILE_INV,
                )

                st.success(
                    f"🎉 Creado: "
                    f"{nombre_final} "
                    f"por "
                    f"${nuevo_precio:,.2f}"
                )

                st.rerun()


        st.markdown("---")

        st.markdown(
            "### 📊 3. Productos y precios"
        )

        for _, fila in df_inv.iterrows():

            nombre = str(
                fila["CATEGORIA"]
            )

            stock = max(
                0,
                int(
                    fila["STOCK"]
                ),
            )

            precio = float(
                fila["PRECIO"]
            )

            estado, color = (
                estado_stock(
                    stock
                )
            )

            es_principal = (
                es_categoria_principal(
                    df_inv,
                    nombre,
                )
            )

            c1, c2, c3, c4 = (
                st.columns(
                    [
                        3.5,
                        1.2,
                        1.4,
                        2,
                    ]
                )
            )

            with c1:

                if es_principal:

                    st.write(
                        f"{obtener_icono(nombre)} "
                        f"**{nombre}** "
                        f"📂 Categoría"
                    )

                else:

                    nombre_visual = (
                        nombre
                    )

                    st.write(
                        f"{obtener_icono(nombre)} "
                        f"**{nombre_visual}**"
                    )

            with c2:

                st.write(
                    f"{stock} ud."
                )

            with c3:

                if es_principal:

                    st.write(
                        "—"
                    )

                else:

                    st.write(
                        f"${precio:,.2f}"
                    )

            with c4:

                html(
                    f"""
                    <span style="
                        color:{color};
                        font-weight:900;
                    ">
                        {estado}
                    </span>
                    """
                )


        st.markdown("---")

        st.markdown(
            "### 🗑️ 4. Eliminar producto"
        )

        producto_eliminar = (
            st.selectbox(
                "📦 Producto",
                df_inv[
                    "CATEGORIA"
                ].tolist(),
                key="producto_eliminar",
            )
        )

        confirmar_eliminar = (
            st.checkbox(
                "⚠️ Confirmo que deseo eliminarlo.",
                key="confirmar_eliminar_inventario",
            )
        )

        if st.button(
            "❌ ELIMINAR PRODUCTO",
            use_container_width=True,
        ):

            if not confirmar_eliminar:

                st.warning(
                    "Marque la confirmación antes de eliminar."
                )

            else:

                df_inv = df_inv[
                    df_inv[
                        "CATEGORIA"
                    ]
                    != producto_eliminar
                ].reset_index(
                    drop=True
                )

                guardar_csv(
                    df_inv,
                    FILE_INV,
                )

                st.success(
                    f"✅ Eliminado: "
                    f"{producto_eliminar}"
                )

                st.rerun()

    elif clave_admin:

        st.error(
            "❌ La clave es incorrecta."
        )


# ============================================================
#                 TAB 4 - HISTORIAL Y CAJA
# ============================================================

with tab_historial:

    html(
        """
        <div style="
            background:
            linear-gradient(
                135deg,
                #ffffff,
                #f8fafc
            );

            padding:25px;
            border-radius:22px;
            border:1px solid #e2e8f0;
            margin-bottom:20px;
        ">

            <div style="
                font-size:32px;
                font-weight:900;
                color:#0f172a;
            ">
                📜 HISTORIAL Y CAJA
            </div>

            <div style="
                font-size:16px;
                color:#64748b;
                margin-top:6px;
            ">
                Consulte ventas, apartados,
                dinero recibido y reportes.
            </div>

        </div>
        """
    )


    if df_ventas.empty:

        st.info(
            "📭 Todavía no hay operaciones."
        )

    else:

        total_caja = float(
            df_ventas[
                "ABONADO"
            ].sum()
        )

        h1, h2, h3 = st.columns(
            3
        )

        with h1:

            st.metric(
                "💰 DINERO RECIBIDO",
                f"${total_caja:,.2f}",
            )

        with h2:

            st.metric(
                "🧾 OPERACIONES",
                len(df_ventas),
            )

        with h3:

            st.metric(
                "📦 APARTADOS ACTIVOS",
                contar_apartados(
                    df_ventas
                ),
            )

        st.markdown("---")

        st.markdown(
            "### 🔎 Buscar una venta"
        )

        f1, f2 = st.columns(
            2
        )

        with f1:

            filtro_cliente = (
                st.text_input(
                    "👤 Nombre del cliente",
                    key="filtro_cliente",
                )
            )

        with f2:

            filtro_producto = (
                st.text_input(
                    "📦 Producto",
                    key="filtro_producto",
                )
            )

        df_filtrado = (
            df_ventas.copy()
        )

        if filtro_cliente.strip():

            df_filtrado = (
                df_filtrado[
                    df_filtrado[
                        "CLIENTE"
                    ].str.contains(
                        filtro_cliente,
                        case=False,
                        na=False,
                    )
                ]
            )

        if filtro_producto.strip():

            df_filtrado = (
                df_filtrado[
                    df_filtrado[
                        "CATEGORIA"
                    ].str.contains(
                        filtro_producto,
                        case=False,
                        na=False,
                    )
                ]
            )

        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        st.markdown(
            "### 🖼️ Ver foto de un registro"
        )

        opciones_fotos = [
            (
                f"Fila {i} | "
                f"{r['FECHA']} | "
                f"{r['CLIENTE']} | "
                f"{r['CATEGORIA']}"
            )
            for i, r
            in df_ventas.iterrows()
        ]

        seleccion_foto = (
            st.selectbox(
                "Seleccione un registro",
                opciones_fotos,
                key="foto_historial",
            )
        )

        indice_foto = int(
            seleccion_foto
            .split(" | ")[0]
            .replace(
                "Fila ",
                "",
            )
        )

        ruta_foto = str(
            df_ventas.loc[
                indice_foto
            ].get(
                "FOTO",
                "Sin foto",
            )
        )

        if (
            ruta_foto != "Sin foto"
            and os.path.exists(
                ruta_foto
            )
        ):

            st.image(
                ruta_foto,
                caption=str(
                    df_ventas.loc[
                        indice_foto,
                        "CATEGORIA",
                    ]
                ),
                width=420,
            )

        else:

            st.info(
                "📷 Este registro no tiene foto."
            )

        st.markdown("---")

        st.markdown(
            "### 📥 Descargar reporte"
        )

        st.download_button(
            "📥 DESCARGAR REPORTE CSV",
            df_ventas.to_csv(
                index=False
            ).encode(
                "utf-8-sig"
            ),
            "reporte_local_mesitas.csv",
            "text/csv",
            use_container_width=True,
        )

        st.markdown("---")

        st.markdown(
            "### 🗑️ Corregir un registro"
        )

        st.warning(
            "⚠️ Use esta opción solamente "
            "si se registró una venta por error."
        )

        clave_borrar = st.text_input(
            "🔐 Clave de administrador",
            type="password",
            key="clave_borrar_historial",
        )

        if clave_borrar == CLAVE_ADMIN:

            opciones_borrar = [
                (
                    f"Fila {i} | "
                    f"{r['FECHA']} | "
                    f"{r['CLIENTE']} | "
                    f"${float(r['TOTAL']):,.2f}"
                )
                for i, r
                in df_ventas.iterrows()
            ]

            registro_borrar = (
                st.selectbox(
                    "Seleccione el registro",
                    opciones_borrar,
                    key="registro_borrar_historial",
                )
            )

            confirmar_borrado = (
                st.checkbox(
                    "⚠️ Confirmo que deseo eliminar este registro.",
                    key="confirmar_borrado_historial",
                )
            )

            if st.button(
                "❌ ELIMINAR REGISTRO",
                use_container_width=True,
            ):

                if not confirmar_borrado:

                    st.warning(
                        "Marque la confirmación primero."
                    )

                else:

                    indice_borrar = int(
                        registro_borrar
                        .split(" | ")[0]
                        .replace(
                            "Fila ",
                            "",
                        )
                    )

                    foto_borrar = str(
                        df_ventas.loc[
                            indice_borrar
                        ].get(
                            "FOTO",
                            "Sin foto",
                        )
                    )

                    if (
                        foto_borrar
                        != "Sin foto"
                        and os.path.exists(
                            foto_borrar
                        )
                    ):

                        try:

                            os.remove(
                                foto_borrar
                            )

                        except Exception:

                            pass

                    df_ventas = (
                        df_ventas
                        .drop(
                            indice_borrar
                        )
                        .reset_index(
                            drop=True
                        )
                    )

                    guardar_csv(
                        df_ventas,
                        FILE_VENTAS,
                    )

                    st.success(
                        "✅ Registro eliminado."
                    )

                    st.rerun()

        elif clave_borrar:

            st.error(
                "❌ Clave incorrecta."
            )


# ============================================================
#                 PIE DE PÁGINA
# ============================================================

html(
    """
    <div style="
        text-align:center;
        margin-top:40px;
        padding:20px;
        color:#64748b;
        border-top:1px solid #e2e8f0;
        font-size:15px;
    ">

        <b>🛏️ LOCAL MESITAS</b>

        <br>

        Sistema POS • Ventas • Apartados
        • Inventario • Caja

        <br>

        <span style="font-size:13px;">
            Diseñado para ser simple y fácil de usar
        </span>

    </div>
    """
) 
