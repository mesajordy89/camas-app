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
#                 LOCAL MESITAS - SISTEMA POS
#        VERSIÓN CORREGIDA - PRODUCTOS Y SUBPRODUCTOS
# ============================================================

st.set_page_config(
    page_title="Local Mesitas - Sistema POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
#                 CONFIGURACIÓN
# ============================================================

CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "199818"

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
#            FUNCIÓN PARA HTML
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
#                 FUNCIONES DE DATOS
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
#                 FOTOS
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
#                 WHATSAPP
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
#                 CORREO
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
#                 FUNCIONES VISUALES
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
#                 PRODUCTOS / SUBPRODUCTOS
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
#                 LOGIN
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
#                 CARGAR INFORMACIÓN
# ============================================================

df_inv = cargar_inventario()
df_ventas = cargar_ventas()


# ============================================================
#                 ESTILOS GENERALES
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
#                 ENCABEZADO
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
#                 RESUMEN
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
#                 MENÚ
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
#                 TAB 1 - VENDER
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
