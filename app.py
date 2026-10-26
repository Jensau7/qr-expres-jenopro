import os
import traceback
from flask import Flask, render_template, request, redirect, url_for, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave_super_segura_jenopro'

# Configuración de base de datos con SSL
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url and "postgresql://" in database_url and "sslmode" not in database_url:
    separator = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{separator}sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='Activo')
    plantilla = db.Column(db.String(50), default='carpinteria')
    productos = db.relationship('Producto', backref='usuario', lazy=True, cascade='all, delete-orphan')

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_prod = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

with app.app_context():
    try:
        db.create_all()
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS plantilla VARCHAR(50) DEFAULT 'carpinteria';"))
            conn.commit()
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('panel'))

@app.errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()
    return f"<h2>Error Interno Detectado:</h2><pre>{tb}</pre>", 500

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        correo = request.form.get('correo') or request.form.get('email')
        password = request.form.get('password') or request.form.get('contrasena')
        
        if not correo or not password:
            return render_template('login.html', error="Por favor ingresa tu correo y contraseña.")
        
        try:
            user = Usuario.query.filter_by(correo=correo).first()
            if not user:
                user = Usuario(
                    nombre='INGENIO EN MADERA',
                    telefono='326141234567',
                    correo=correo,
                    password=password,
                    estado='Activo',
                    plantilla='carpinteria'
                )
                db.session.add(user)
                db.session.commit()
            else:
                user.estado = 'Activo'
                db.session.commit()
            
            session['user_id'] = user.id
            session['nombre_negocio'] = user.nombre
            return redirect(url_for('panel'))
        except Exception as e:
            db.session.rollback()
            return f"<h2>Error en Login:</h2><pre>{traceback.format_exc()}</pre>", 500

    return render_template('login.html', error=error)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo') or request.form.get('email')
        password = request.form.get('password') or request.form.get('contrasena')
        
        if not correo or not password:
            return render_template('registro.html', error="Todos los campos son obligatorios.")
            
        try:
            user = Usuario.query.filter_by(correo=correo).first()
            if not user:
                user = Usuario(nombre=nombre, telefono=telefono, correo=correo, password=password, estado='Activo', plantilla='carpinteria')
                db.session.add(user)
                db.session.commit()
            else:
                user.estado = 'Activo'
                db.session.commit()

            session['user_id'] = user.id
            session['nombre_negocio'] = user.nombre
            return redirect(url_for('panel'))
        except Exception as e:
            db.session.rollback()
            return f"<h2>Error en Registro:</h2><pre>{traceback.format_exc()}</pre>", 500
    return render_template('registro.html')

@app.route('/panel', methods=['GET', 'POST'])
def panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = Usuario.query.get(session['user_id'])
    if user:
        user.estado = 'Activo'
        db.session.commit()
    
    if request.method == 'POST':
        nombre_prod = request.form.get('nombre_prod')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        
        imagen_url = None
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagen_url = url_for('static', filename=f'uploads/{filename}')

        try:
            nuevo_prod = Producto(
                nombre_prod=nombre_prod,
                precio=float(precio or 0),
                descripcion=descripcion,
                imagen=imagen_url,
                usuario_id=user.id
            )
            db.session.add(nuevo_prod)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            
        return redirect(url_for('panel'))

    productos = Producto.query.filter_by(usuario_id=user.id).all() if user else []
    return render_template('panel.html', usuario=user, productos=productos)

@app.route('/cambiar_plantilla', methods=['POST'])
def cambiar_plantilla():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = Usuario.query.get(session['user_id'])
    if user:
        user.plantilla = request.form.get('plantilla', 'carpinteria')
        db.session.commit()
    return redirect(url_for('panel'))

# Menú público interativo con selector de cantidades y total en tiempo real
HTML_MENU_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ usuario.nombre }} - Catálogo Digital</title>
    <style>
        body { background: #121212; color: #f4f1ea; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; padding-bottom: 95px; }
        .header { background: linear-gradient(135deg, #2c1d11, #4a2e18); border-bottom: 3px solid #b07d62; text-align: center; padding: 25px 15px; }
        .header h1 { margin: 0; font-size: 24px; color: #d4a373; text-transform: uppercase; letter-spacing: 1px; }
        .header p { margin: 5px 0 0; color: #dda15e; font-size: 13px; }
        .container { max-width: 600px; margin: 15px auto; padding: 0 10px; }
        .card { background: #1e1e1e; border: 1px solid #333; border-radius: 10px; overflow: hidden; margin-bottom: 15px; display: flex; align-items: center; padding: 12px; gap: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.4); }
        .card img { width: 85px; height: 85px; object-fit: cover; border-radius: 8px; background: #2a2a2a; }
        .card-info { flex: 1; }
        .card-title { font-size: 16px; font-weight: bold; color: #fff; margin: 0 0 4px; }
        .card-desc { font-size: 12px; color: #aaa; margin: 0 0 8px; }
        .card-price { font-size: 15px; font-weight: bold; color: #dda15e; }
        .qty-control { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
        .qty-btn { background: #333; color: #fff; border: none; width: 28px; height: 28px; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 14px; }
        .qty-btn:active { background: #555; }
        .qty-input { width: 38px; text-align: center; background: #2a2a2a; color: #fff; border: 1px solid #444; border-radius: 4px; font-size: 14px; padding: 3px; }
        .floating-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #1a1a1a; border-top: 2px solid #333; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -4px 10px rgba(0,0,0,0.5); z-index: 1000; }
        .total-text { font-size: 15px; font-weight: bold; color: #fff; }
        .btn-enviar { background: #25d366; color: white; border: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; font-size: 14px; cursor: pointer; text-decoration: none; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ usuario.nombre }}</h1>
        <p>Selecciona las cantidades y haz tu pedido por WhatsApp</p>
    </div>
    
    <div class="container">
        {% if productos %}
            {% for p in productos %}
                <div class="card">
                    {% if p.imagen %}
                        <img src="{{ p.imagen }}" alt="{{ p.nombre_prod }}">
                    {% else %}
                        <div style="width: 85px; height: 85px; background: #2a2a2a; display: flex; align-items: center; justify-content: center; color: #666; border-radius: 8px; font-size: 11px;">Sin Foto</div>
                    {% endif %}
                    <div class="card-info">
                        <div class="card-title">{{ p.nombre_prod }}</div>
                        <div class="card-desc">{{ p.descripcion or '' }}</div>
                        <div class="card-price">${{ "%.2f"|format(p.precio) }} MXN</div>
                        <div class="qty-control">
                            <button type="button" class="qty-btn" onclick="cambiarQty({{ p.id }}, -1)">-</button>
                            <input type="text" id="qty_{{ p.id }}" class="qty-input" value="0" readonly>
                            <button type="button" class="qty-btn" onclick="cambiarQty({{ p.id }}, 1)">+</button>
                        </div>
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <p style="text-align: center; color: #888; margin-top: 40px;">No hay productos disponibles en este catálogo.</p>
        {% endif %}
    </div>

    <div class="floating-bar">
        <div>
            <div class="total-text">Total: $<span id="totalGeneral">0.00</span> MXN</div>
        </div>
        <button type="button" class="btn-enviar" onclick="enviarPedido()">📲 Enviar Pedido</button>
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
            let mensaje = "Hola, me interesa realizar el siguiente pedido:%0A";
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
                alert("Por favor selecciona al menos un producto antes de enviar tu pedido.");
                return;
            }

            mensaje += `%0A*Total a Pagar: $${total.toFixed(2)} MXN*`;
            const telefono = "{{ usuario.telefono }}";
            window.open(`https://wa.me/${telefono}?text=${mensaje}`, '_blank');
        }
    </script>
</body>
</html>
"""

@app.route('/menu')
def menu_publico():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = Usuario.query.get(session['user_id'])
    productos = Producto.query.filter_by(usuario_id=user.id).all() if user else []
    return render_template_string(HTML_MENU_TEMPLATE, usuario=user, productos=productos)

@app.route('/eliminar/<int:id>')
@app.route('/borrar/<int:id>')
@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    producto = Producto.query.get(id)
    if producto and producto.usuario_id == session['user_id']:
        db.session.delete(producto)
        db.session.commit()
        
    return redirect(url_for('panel'))

@app.route('/pago')
@app.route('/simular-pago')
@app.route('/simular_pago')
def pago():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = Usuario.query.get(session['user_id'])
    if user:
        user.estado = 'Activo'
        db.session.commit()
    return redirect(url_for('panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
