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

# Menú público con diseño moderno de tarjetas estilo DiDi Food (Grid visual con fotos grandes arriba)
HTML_MENU_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ usuario.nombre }} - Menú Digital</title>
    <style>
        body { background: #121212; color: #f4f1ea; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; padding-bottom: 100px; }
        .header { background: linear-gradient(135deg, #1e1e1e, #2d2d2d); border-bottom: 2px solid #ff7043; text-align: center; padding: 25px 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        .header h1 { margin: 0; font-size: 22px; color: #ff7043; text-transform: uppercase; letter-spacing: 1px; font-weight: 800; }
        .header p { margin: 6px 0 0; color: #bbb; font-size: 13px; }
        
        .container { max-width: 900px; margin: 20px auto; padding: 0 12px; }
        
        .grid-menu { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
        
        .food-card { background: #1e1e1e; border-radius: 14px; overflow: hidden; box-shadow: 0 6px 15px rgba(0,0,0,0.4); display: flex; flex-direction: column; border: 1px solid #333; position: relative; }
        .food-img-container { width: 100%; height: 170px; background: #2a2a2a; position: relative; overflow: hidden; }
        .food-img-container img { width: 100%; height: 100%; object-fit: cover; }
        .no-img { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #777; font-size: 12px; background: #252525; }
        
        .food-body { padding: 14px; display: flex; flex-direction: column; flex: 1; justify-content: space-between; }
        .food-title { font-size: 16px; font-weight: 700; color: #fff; margin: 0 0 4px; }
        .food-desc { font-size: 12px; color: #aaa; margin: 0 0 12px; line-height: 1.4; }
        
        .food-footer { display: flex; justify-content: space-between; align-items: center; margin-top: auto; }
        .food-price { font-size: 17px; font-weight: 800; color: #ff7043; }
        
        .qty-box { display: flex; align-items: center; background: #2a2a2a; border-radius: 8px; border: 1px solid #444; overflow: hidden; }
        .qty-btn { background: #333; color: #fff; border: none; width: 32px; height: 32px; font-weight: bold; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .qty-btn:active { background: #ff7043; }
        .qty-num { width: 32px; text-align: center; color: #fff; font-weight: bold; font-size: 14px; background: transparent; border: none; }

        .floating-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #1a1a1a; border-top: 2px solid #333; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -6px 20px rgba(0,0,0,0.7); z-index: 1000; }
        .total-info { font-size: 16px; font-weight: bold; color: #fff; }
        .total-info span { color: #ff7043; font-size: 18px; }
        .btn-whatsapp { background: #25d366; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; text-decoration: none; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 10px rgba(37,211,102,0.3); }
        .btn-whatsapp:hover { background: #20ba5a; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ usuario.nombre }}</h1>
        <p>Selecciona tus productos y haz tu pedido al instante</p>
    </div>
    
    <div class="container">
        {% if productos %}
            <div class="grid-menu">
                {% for p in productos %}
                    <div class="food-card">
                        <div class="food-img-container">
                            {% if p.imagen %}
                                <img src="{{ p.imagen }}" alt="{{ p.nombre_prod }}">
                            {% else %}
                                <div class="no-img">Sin Imagen</div>
                            {% endif %}
                        </div>
                        <div class="food-body">
                            <div>
                                <div class="food-title">{{ p.nombre_prod }}</div>
                                <div class="food-desc">{{ p.descripcion or 'Producto de alta calidad' }}</div>
                            </div>
                            <div class="food-footer">
                                <div class="food-price">${{ "%.2f"|format(p.precio) }}</div>
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
            <div style="text-align: center; color: #888; margin-top: 50px; font-size: 15px;">
                Aún no hay productos en este catálogo. ¡Agrega algunos desde tu panel!
            </div>
        {% endif %}
    </div>

    <div class="floating-bar">
        <div class="total-info">
            Total: $<span id="totalGeneral">0.00</span> MXN
        </div>
        <button type="button" class="btn-whatsapp" onclick="enviarPedido()">
            📲 Enviar Pedido por WhatsApp
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
