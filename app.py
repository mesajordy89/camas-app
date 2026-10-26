
from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os
from pathlib import Path
from werkzeug.utils import secure_filename

app = Flask(__name__)

CARPETA = Path(__file__).resolve().parent
CARPETA_FOTOS = CARPETA / "static" / "fotos"
BASE_DATOS = CARPETA / "camas.db"

CARPETA_FOTOS.mkdir(parents=True, exist_ok=True)

EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}

def conectar():
    conexion = sqlite3.connect(BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    return conexion

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
                foto TEXT
            )
        """)

preparar_base_datos()

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sistema de Camas</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f3f5f9;
    color: #243047;
}
header {
    background: #172554;
    color: white;
    padding: 24px;
}
header h1 { margin: 0 0 8px; }
header p { margin: 0; color: #dbeafe; }
main { max-width: 1100px; margin: 25px auto; padding: 0 16px; }
.panel {
    background: white;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 22px;
    box-shadow: 0 3px 12px #0000000d;
}
h2 { margin-top: 0; }
form {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}
.campo { display: flex; flex-direction: column; gap: 6px; }
.campo.completo { grid-column: 1 / -1; }
input, select, textarea {
    width: 100%;
    padding: 11px;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    font-size: 15px;
}
button {
    border: 0;
    border-radius: 7px;
    padding: 12px 18px;
    background: #2563eb;
    color: white;
    cursor: pointer;
    font-size: 15px;
}
button:hover { background: #1d4ed8; }
.tabla { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td {
    text-align: left;
    padding: 12px;
    border-bottom: 1px solid #e2e8f0;
}
th { background: #f8fafc; }
.foto { width: 75px; height: 65px; object-fit: cover; border-radius: 6px; }
.eliminar { background: #dc2626; padding: 8px 10px; }
.mensaje {
    background: #dcfce7;
    padding: 12px;
    border-radius: 7px;
    margin-bottom: 16px;
}
.vacio { color: #64748b; }
@media (max-width: 600px) {
    form { grid-template-columns: 1fr; }
    .campo.completo { grid-column: auto; }
    header { padding: 18px; }
}
</style>
</head>
<body>
<header>
    <h1>🛏️ Sistema de Camas</h1>
    <p>Administración de camas, colchones y productos</p>
</header>

<main>
    {% if mensaje %}
    <div class="mensaje">{{ mensaje }}</div>
    {% endif %}

    <section class="panel">
        <h2>➕ Agregar producto</h2>
        <form action="{{ url_for('agregar') }}" method="POST"
              enctype="multipart/form-data">
            <div class="campo">
                <label>Nombre del producto *</label>
                <input name="nombre" required placeholder="Ej. Cama moderna">
            </div>

            <div class="campo">
                <label>Tipo *</label>
                <select name="tipo" required>
                    <option value="Cama">Cama</option>
                    <option value="Colchón">Colchón</option>
                    <option value="Base">Base</option>
                    <option value="Cabecera">Cabecera</option>
                    <option value="Juego de dormitorio">Juego de dormitorio</option>
                    <option value="Otro">Otro</option>
                </select>
            </div>

            <div class="campo">
                <label>Medida *</label>
                <select name="medida" required>
                    <option value="1 plaza">1 plaza</option>
                    <option value="1½ plazas">1½ plazas</option>
                    <option value="2 plazas">2 plazas</option>
                    <option value="Queen">Queen</option>
                    <option value="King">King</option>
                    <option value="Otra">Otra</option>
                </select>
            </div>

            <div class="campo">
                <label>Precio en dólares *</label>
                <input type="number" name="precio" min="0" step="0.01"
                       required placeholder="350.00">
            </div>

            <div class="campo">
                <label>Stock disponible *</label>
                <input type="number" name="stock" min="0" step="1"
                       required value="1">
            </div>

            <div class="campo">
                <label>Fotografía</label>
                <input type="file" name="foto"
                       accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp">
            </div>

            <div class="campo completo">
                <label>Descripción</label>
                <textarea name="descripcion" rows="3"
                          placeholder="Detalles del producto"></textarea>
            </div>

            <div class="campo completo">
                <button type="submit">Guardar producto</button>
            </div>
        </form>
    </section>

    <section class="panel">
        <h2>📦 Productos registrados ({{ productos|length }})</h2>
        <div class="tabla">
        <table>
            <thead>
                <tr>
                    <th>Foto</th>
                    <th>Producto</th>
                    <th>Medida</th>
                    <th>Precio</th>
                    <th>Stock</th>
                    <th>Acción</th>
                </tr>
            </thead>
            <tbody>
            {% for p in productos %}
                <tr>
                    <td>
                    {% if p['foto'] %}
                        <img class="foto"
                             src="{{ url_for('static', filename='fotos/' + p['foto']) }}"
                             alt="Foto del producto">
                    {% else %}
                        🛏️
                    {% endif %}
                    </td>
                    <td>
                        <strong>{{ p['nombre'] }}</strong><br>
                        <small>{{ p['tipo'] }}</small><br>
                        <small>{{ p['descripcion'] or '' }}</small>
                    </td>
                    <td>{{ p['medida'] }}</td>
                    <td>${{ "%.2f"|format(p['precio']) }}</td>
                    <td>{{ p['stock'] }}</td>
                    <td>
                        <form action="{{ url_for('eliminar', id=p['id']) }}"
                              method="POST"
                              onsubmit="return confirm('¿Eliminar este producto?')">
                            <button class="eliminar" type="submit">
                                Eliminar
                            </button>
                        </form>
                    </td>
                </tr>
            {% else %}
                <tr>
                    <td colspan="6" class="vacio">
                        Todavía no hay productos. Agrega el primero arriba.
                    </td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
        </div>
    </section>
</main>
</body>
</html>
"""

@app.route("/")
def inicio():
    with conectar() as db:
        productos = db.execute(
            "SELECT * FROM productos ORDER BY id DESC"
        ).fetchall()

    return render_template_string(
        HTML,
        productos=productos,
        mensaje=request.args.get("mensaje", "")
    )

@app.route("/agregar", methods=["POST"])
def agregar():
    nombre = request.form.get("nombre", "").strip()
    tipo = request.form.get("tipo", "").strip()
    medida = request.form.get("medida", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    try:
        precio = float(request.form.get("precio", ""))
        stock = int(request.form.get("stock", ""))
        if not nombre or not tipo or not medida:
            raise ValueError
        if precio < 0 or stock < 0:
            raise ValueError
    except (ValueError, TypeError):
        return redirect(url_for(
            "inicio", mensaje="Revisa los datos del producto."
        ))

    archivo = request.files.get("foto")
    nombre_foto = None

    if archivo and archivo.filename:
        nombre_seguro = secure_filename(archivo.filename)
        extension = nombre_seguro.rsplit(".", 1)[-1].lower() if "." in nombre_seguro else ""

        if extension not in EXTENSIONES_PERMITIDAS:
            return redirect(url_for(
                "inicio", mensaje="La foto debe ser JPG, PNG o WEBP."
            ))

        import uuid
        nombre_foto = f"{uuid.uuid4().hex}.{extension}"
        archivo.save(CARPETA_FOTOS / nombre_foto)

    try:
        with conectar() as db:
            db.execute("""
                INSERT INTO productos
                (nombre, tipo, medida, precio, stock, descripcion, foto)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                nombre, tipo, medida, precio, stock,
                descripcion, nombre_foto
            ))
    except Exception:
        if nombre_foto:
            (CARPETA_FOTOS / nombre_foto).unlink(missing_ok=True)
        raise

    return redirect(url_for(
        "inicio", mensaje="Producto guardado correctamente."
    ))

@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    with conectar() as db:
        producto = db.execute(
            "SELECT foto FROM productos WHERE id = ?", (id,)
        ).fetchone()

        if producto:
            db.execute("DELETE FROM productos WHERE id = ?", (id,))

    if producto and producto["foto"]:
        ruta = CARPETA_FOTOS / producto["foto"]
        ruta.unlink(missing_ok=True)

    return redirect(url_for(
        "inicio", mensaje="Producto eliminado."
    ))

if __name__ == "__main__":
    app.run(debug=True)
