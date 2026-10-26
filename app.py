import os
import base64
import traceback
from flask import Flask, render_template, request, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'clave_super_segura_jenopro'

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url and "postgresql://" in database_url and "sslmode" not in database_url:
    separator = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{separator}sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_prod = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    imagen = db.Column(db.Text, nullable=True)  # Guardamos la imagen en Base64 directamente en la BD

with app.app_context():
    db.create_all()

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('panel'))

@app.errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()
    return f"<h2>Error Interno Detectado:</h2><pre>{tb}</pre>", 500

@app.route('/', methods=['GET', 'POST'])
def panel():
    if request.method == 'POST':
        nombre_prod = request.form.get('nombre_prod')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        
        imagen_data = None
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '':
                # Convertimos la foto directamente a texto Base64 para que nunca se borre en Render
                file_bytes = file.read()
                encoded = base64.b64encode(file_bytes).decode('utf-8')
                # Detectamos el tipo de imagen automáticamente
                mimetype = file.mimetype or 'image/jpeg'
                imagen_data = f"data:{mimetype};base64,{encoded}"

        try:
            nuevo_prod = Producto(
                nombre_prod=nombre_prod,
                precio=float(precio or 0),
                descripcion=descripcion,
                imagen=imagen_data
            )
            db.session.add(nuevo_prod)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            
        return redirect(url_for('panel'))

    productos = Producto.query.all()
    return render_template('panel.html', productos=productos)

@app.route('/eliminar/<int:id>')
def eliminar_producto(id):
    producto = Producto.query.get(id)
    if producto:
        db.session.delete(producto)
        db.session.commit()
    return redirect(url_for('panel'))

HTML_MENU_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INGENIO EN MADERA - Catálogo Digital</title>
    <style>
        body { background: #121212; color: #f4f1ea; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; padding-bottom: 110px; }
        .header { background: linear-gradient(135deg, #2c1d11, #1a120b); border-bottom: 3px solid #dda15e; text-align: center; padding: 30px 15px; box-shadow: 0 6px 15px rgba(0,0,0,0.6); }
        .header h1 { margin: 0; font-size: 24px; color: #dda15e; text-transform: uppercase; font-weight: 900; letter-spacing: 1.5px; }
        .header p { margin: 8px 0 0; color: #bc6c25; font-size: 13px; font-weight: 600; }
        
        .container { max-width: 900px; margin: 20px auto; padding: 0 12px; }
        
        .grid-menu { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
        @media (min-width: 600px) { .grid-menu { grid-template-columns: repeat(3, 1fr); } }
        
        .wood-card { background: #1e1b18; border-radius: 14px; overflow: hidden; box-shadow: 0 8px 20px rgba(0,0,0,0.5); display: flex; flex-direction: column; border: 1px solid #3d2c1d; transition: transform 0.2s; }
        .wood-card:hover { transform: translateY(-3px); }
        
        .wood-img-container { width: 100%; height: 160px; background: #28211b; position: relative; overflow: hidden; }
        .wood-img-container img { width: 100%; height: 100%; object-fit: cover; }
        .no-img { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #8c7a6b; font-size: 12px; font-style: italic; }
        
        .wood-body { padding: 14px; display: flex; flex-direction: column; flex: 1; justify-content: space-between; }
        .wood-title { font-size: 15px; font-weight: 800; color: #fefae0; margin: 0 0 4px; line-height: 1.3; }
        .wood-desc { font-size: 11px; color: #b0a699; margin: 0 0 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4; }
        
        .wood-footer { display: flex; flex-direction: column; gap: 10px; margin-top: auto; border-top: 1px solid #2d241d; padding-top: 10px; }
        .wood-price { font-size: 16px; font-weight: 950; color: #dda15e; }
        
        .qty-box { display: flex; align-items: center; justify-content: space-between; background: #28211b; border-radius: 8px; border: 1px solid #4a3828; overflow: hidden; width: 100%; }
        .qty-btn { background: #dda15e; color: #1a120b; border: none; width: 36px; height: 34px; font-weight: 900; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .qty-btn:active { background: #bc6c25; }
        .qty-num { width: 35px; text-align: center; color: #fff; font-weight: bold; font-size: 14px; background: transparent; border: none; }

        .floating-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #1a140f; border-top: 2px solid #dda15e; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -6px 25px rgba(0,0,0,0.8); z-index: 1000; }
        .total-info { font-size: 15px; font-weight: bold; color: #fff; }
        .total-info span { color: #dda15e; font-size: 18px; font-weight: 900; }
        .btn-whatsapp { background: #25d366; color: white; border: none; padding: 12px 20px; border-radius: 10px; font-weight: 900; font-size: 14px; cursor: pointer; text-decoration: none; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 12px rgba(37,211,102,0.4); }
        .btn-whatsapp:hover { background: #20ba5a; }
    </style>
</head>
<body>
    <div class="header">
        <h1>INGENIO EN MADERA</h1>
        <p>Carpintería y Restauración de Muebles | Diseños a Medida</p>
    </div>
    
    <div class="container">
        {% if productos %}
            <div class="grid-menu">
                {% for p in productos %}
                    <div class="wood-card">
                        <div class="wood-img-container">
                            {% if p.imagen %}
                                <img src="{{ p.imagen }}" alt="{{ p.nombre_prod }}">
                            {% else %}
                                <div class="no-img">Pieza Artesanal</div>
                            {% endif %}
                        </div>
                        <div class="wood-body">
                            <div>
                                <div class="wood-title">{{ p.nombre_prod }}</div>
                                <div class="wood-desc">{{ p.descripcion or 'Trabajo artesanal en madera de alta calidad.' }}</div>
                            </div>
                            <div class="wood-footer">
                                <div class="wood-price">${{ "%.2f"|format(p.precio) }} MXN</div>
                                <div class="qty-box">
                                    <button type="button" class="qty-btn" onclick="cambiarQty({{ p.id }}, -1)">-</button>
                                    <input type="text" id="qty_{{ p.id }}" class="qty-num" value="0" readonly>
                                    <button type="button" class="qty-btn" onclick="cambiarQty({{ p.id }}, 1)">+</button>
                                </div>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div style="text-align: center; color: #8c7a6b; margin-top: 60px; font-size: 15px;">
                No hay piezas o muebles registrados en el catálogo por el momento.
            </div>
        {% endif %}
    </div>

    <div class="floating-bar">
        <div class="total-info">
            Inversión Total: $<span id="totalGeneral">0.00</span> MXN
        </div>
        <button type="button" class="btn-whatsapp" onclick="enviarPedido()">
            📲 Cotizar / Pedir por WhatsApp
        </button>
    </div>

    <script>
        const productosData = {
            {% for p in productos %}
            "{{ p.id }}": { nombre: "{{ p.nombre_prod }}", precio: {{ p.precio }} },
            {% endfor %}
        };

        function cambiarQty(id, cambio) {
            const input = document.getElementById('qty_' + id);
            let val = parseInt(input.value) + cambio;
            if (val < 0) val = 0;
            input.value = val;
            calcularTotal();
        }

        function calcularTotal() {
            let total = 0;
            for (let id in productosData) {
                const input = document.getElementById('qty_' + id);
                if (input) {
                    let qty = parseInt(input.value) || 0;
                    total += qty * productosData[id].precio;
                }
            }
            document.getElementById('totalGeneral').innerText = total.toFixed(2);
        }

        function enviarPedido() {
            let mensaje = "Hola, me interesa cotizar / ordenar lo siguiente:%0A";
            let hayItems = false;
            let total = 0;

            for (let id in productosData) {
                const input = document.getElementById('qty_' + id);
                if (input) {
                    let qty = parseInt(input.value) || 0;
                    if (qty > 0) {
                        hayItems = true;
                        let subtotal = qty * productosData[id].precio;
                        total += subtotal;
                        mensaje += `- ${productosData[id].nombre} (x${qty}) - $%s%0A`.replace('%s', subtotal.toFixed(2));
                    }
                }
            }

            if (!hayItems) {
                alert("Por favor selecciona al menos una pieza o mueble antes de enviar tu cotización.");
                return;
            }

            mensaje += `%0A*Inversión Total: $${total.toFixed(2)} MXN*`;
            const telefono = "6143665161";
            window.open(`https://wa.me/${telefono}?text=${mensaje}`, '_blank');
        }
    </script>
</body>
</html>
"""

@app.route('/menu')
def menu_publico():
    productos = Producto.query.all()
    return render_template_string(HTML_MENU_TEMPLATE, productos=productos)

if __name__ == '__main__':
    app.run(debug=True)
