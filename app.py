
import streamlit as st
import sqlite3
from pathlib import Path
from PIL import Image
from io import BytesIO

# ---------------------------------
# CONFIGURACION
# ---------------------------------
st.set_page_config(
    page_title="Sistema de Camas",
    page_icon="🛏️",
    layout="wide"
)

CARPETA = Path(__file__).resolve().parent
BASE_DATOS = CARPETA / "camas.db"

st.title("🛏️ Sistema de Camas y Colchones")
st.caption("Administración de productos, precios y existencias")

# ---------------------------------
# BASE DE DATOS
# ---------------------------------
def conectar():
    return sqlite3.connect(BASE_DATOS)

def preparar_base_datos():
    with conectar() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                medida TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL,
                descripcion TEXT,
                foto BLOB
            )
        """)

preparar_base_datos()

# ---------------------------------
# MENU
# ---------------------------------
pagina = st.sidebar.radio(
    "MENÚ PRINCIPAL",
    [
        "Inicio",
        "Agregar producto",
        "Ver productos",
        "Eliminar producto"
    ]
)

# ---------------------------------
# INICIO
# ---------------------------------
if pagina == "Inicio":
    st.header("Panel principal")

    with conectar() as db:
        total = db.execute(
            "SELECT COUNT(*) FROM productos"
        ).fetchone()[0]

        unidades = db.execute(
            "SELECT COALESCE(SUM(stock), 0) FROM productos"
        ).fetchone()[0]

        valor = db.execute(
            "SELECT COALESCE(SUM(precio * stock), 0) FROM productos"
        ).fetchone()[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Productos registrados", total)
    c2.metric("Unidades en stock", unidades)
    c3.metric("Valor del inventario", f"${valor:,.2f}")

    st.info(
        "Usa el menú de la izquierda para registrar camas, "
        "colchones, bases y otros productos."
    )

# ---------------------------------
# AGREGAR PRODUCTO
# ---------------------------------
elif pagina == "Agregar producto":
    st.header("➕ Registrar producto")

    with st.form("formulario_producto", clear_on_submit=True):
        nombre = st.text_input(
            "Nombre del producto *",
            placeholder="Ej. Cama moderna"
        )

        tipo = st.selectbox(
            "Tipo de producto",
            [
                "Cama",
                "Colchón",
                "Base",
                "Cabecera",
                "Juego de dormitorio",
                "Otro"
            ]
        )

        medida = st.selectbox(
            "Medida",
            [
                "1 plaza",
                "1½ plazas",
                "2 plazas",
                "Queen",
                "King",
                "Otra"
            ]
        )

        c1, c2 = st.columns(2)

        with c1:
            precio = st.number_input(
                "Precio en dólares ($)",
                min_value=0.0,
                value=0.0,
                step=5.0
            )

        with c2:
            stock = st.number_input(
                "Cantidad disponible",
                min_value=0,
                value=1,
                step=1
            )

        descripcion = st.text_area("Descripción del producto")

        foto = st.file_uploader(
            "Subir fotografía",
            type=["jpg", "jpeg", "png", "webp"]
        )

        guardar = st.form_submit_button(
            "💾 Guardar producto",
            use_container_width=True
        )

    if guardar:
        if not nombre.strip():
            st.error("Debes escribir el nombre del producto.")
        else:
            foto_bytes = None

            if foto is not None:
                try:
                    imagen = Image.open(foto)
                    if imagen.format not in ["JPEG", "PNG", "WEBP"]:
                        st.error("Formato de imagen no válido.")
                        st.stop()

                    if imagen.width > 5000 or imagen.height > 5000:
                        st.error("La imagen es demasiado grande.")
                        st.stop()

                    imagen.thumbnail((1200, 1200))
                    salida = BytesIO()

                    if imagen.mode not in ("RGB", "RGBA"):
                        imagen = imagen.convert("RGB")

                    formato = "PNG" if imagen.mode == "RGBA" else "JPEG"
                    if formato == "JPEG" and imagen.mode != "RGB":
                        imagen = imagen.convert("RGB")

                    imagen.save(salida, format=formato, quality=85)
                    foto_bytes = salida.getvalue()

                except Exception:
                    st.error("No se pudo leer la fotografía.")
                    st.stop()

            with conectar() as db:
                db.execute(
                    """
                    INSERT INTO productos
                    (nombre, tipo, medida, precio, stock, descripcion, foto)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        nombre.strip(),
                        tipo,
                        medida,
                        float(precio),
                        int(stock),
                        descripcion.strip(),
                        foto_bytes
                    )
                )

            st.success("¡Producto guardado correctamente!")
            st.rerun()

# ---------------------------------
# VER PRODUCTOS
# ---------------------------------
elif pagina == "Ver productos":
    st.header("📦 Productos registrados")

    with conectar() as db:
        productos = db.execute(
            """
            SELECT id, nombre, tipo, medida, precio,
                   stock, descripcion, foto
            FROM productos
            ORDER BY id DESC
            """
        ).fetchall()

    if not productos:
        st.info("Todavía no hay productos registrados.")
    else:
        busqueda = st.text_input(
            "🔎 Buscar por nombre o tipo",
            placeholder="Ej. Cama Queen"
        )

        filtrados = [
            p for p in productos
            if busqueda.strip().lower() in
            (p[1] + " " + p[2] + " " + p[3]).lower()
        ]

        st.write(f"Productos encontrados: {len(filtrados)}")

        for p in filtrados:
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])

                with col1:
                    if p[7]:
                        st.image(BytesIO(p[7]), use_container_width=True)
                    else:
                        st.markdown("### 🛏️")

                with col2:
                    st.subheader(p[1])
                    st.write(f"**Código:** {p[0]}")
                    st.write(f"**Tipo:** {p[2]}")
                    st.write(f"**Medida:** {p[3]}")
                    st.write(f"**Precio:** ${p[4]:,.2f}")
                    st.write(f"**Stock:** {p[5]} unidades")

                    if p[6]:
                        st.write(p[6])

# ---------------------------------
# ELIMINAR PRODUCTO
# ---------------------------------
elif pagina == "Eliminar producto":
    st.header("🗑️ Eliminar producto")

    with conectar() as db:
        productos = db.execute(
            "SELECT id, nombre, medida, precio FROM productos ORDER BY nombre"
        ).fetchall()

    if not productos:
        st.info("No hay productos para eliminar.")
    else:
        opciones = {
            f"#{p[0]} - {p[1]} ({p[2]}) - ${p[3]:,.2f}": p[0]
            for p in productos
        }

        seleccionado = st.selectbox(
            "Selecciona el producto",
            list(opciones.keys())
        )

        confirmar = st.checkbox(
            "Confirmo que deseo eliminar este producto"
        )

        if st.button("Eliminar producto", type="primary"):
            if not confirmar:
                st.warning("Marca la casilla para confirmar.")
            else:
                producto_id = opciones[seleccionado]

                with conectar() as db:
                    db.execute(
                        "DELETE FROM productos WHERE id = ?",
                        (producto_id,)
                    )

                st.success("Producto eliminado.")
                st.rerun()

