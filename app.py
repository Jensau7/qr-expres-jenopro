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

# Plantilla HTML incrustada directamente para evitar errores de archivos faltantes
HTML_MENU_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo | {{ usuario.nombre }}</title>
    <style>
        body { background: {% if usuario.plantilla == 'restaurante' %}#fff3ec{% elif usuario.plantilla == 'minimalista' %}#f8f9fa{% else %}#1a120b{% endif %}; 
               color: {% if usuario.plantilla == 'carpinteria' %}#f4f1ea{% else %}#333{% endif %}; 
               font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .header { background: {% if usuario.plantilla == 'restaurante' %}#e76f51{% elif usuario.plantilla == 'minimalista' %}#212529{% else %}linear-gradient(135deg, #2c1d11, #4a2e18){% endif %}; 
                  color: white; text-align: center; padding: 30px 20px; }
        .container { max-width: 800px; margin: 20px auto; padding: 0 15px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; }
        .card { background: {% if usuario.plantilla == 'carpinteria' %}#281d13{% else %}white{% endif %}; 
                border: 1px solid {% if usuario.plantilla == 'carpinteria' %}#5c3d24{% else %}#ddd{% endif %}; 
                border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.2); display: flex; flex-direction: column; }
        .card img { width: 100%; height: 180px; object-fit: cover; }
        .card-body { padding: 15px; display: flex; flex-direction: column; justify-content: space-between; flex: 1; }
        .price { font-size: 18px; font-weight: bold; color: {% if usuario.plantilla == 'carpinteria' %}#dda15e{% elif usuario.plantilla == 'restaurante' %}#e76f51{% else %}#0d6efd{% endif %}; }
        .btn { background: #25d366; color: white; padding: 8px 12px; border-radius: 5px; text-decoration: none; font-size: 13px; font-weight: bold; display: inline-block; text-align: center; }
        .volver { text-align: center; margin: 30px 0; }
        .volver a { background: #6c757d; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ usuario.nombre }}</h1>
        <p>WhatsApp: {{ usuario.telefono }} | Estilo: {{ usuario.plantilla | capitalize }}</p>
    </div>
    <div class="container">
        <h2 style="text-align: center; margin-bottom: 25px;">Catálogo de Productos y Servicios</h2>
        {% if productos %}
            <div class="grid">
                {% for p in productos %}
                    <div class="card">
                        {% if p.imagen %}
                            <img src="{{ p.imagen }}" alt="{{ p.nombre_prod }}">
                        {% else %}
                            <div style="width: 100%; height: 180px; background: #444; display: flex; align-items: center; justify-content: center; color: #aaa;">Sin Imagen</div>
                        {% endif %}
                        <div class="card-body">
                            <div>
                                <h3 style="margin: 0 0 5px;">{{ p.nombre_prod }}</h3>
                                <p style="font-size: 13px; color: {% if usuario.plantilla == 'carpinteria' %}#c8b6a6{% else %}#666{% endif %};">{{ p.descripcion or 'Sin descripción' }}</p>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px; border-top: 1px solid rgba(128,128,128,0.2); padding-top: 10px;">
                                <span class="price">${{ "%.2f"|format(p.precio) }} MXN</span>
                                <a href="https://wa.me/{{ usuario.telefono }}?text=Me%20interesa%20el%20producto:%20{{ p.nombre_prod }}" target="_blank" class="btn">Pedir por WhatsApp</a>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <p style="text-align: center; color: #888;">No hay productos registrados en este catálogo.</p>
        {% endif %}
        <div class="volver">
            <a href="/panel">⬅️ Volver al Panel de Administración</a>
        </div>
    </div>
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
