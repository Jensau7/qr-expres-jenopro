import os
import traceback
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
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
                    estado='Activo'
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
                user = Usuario(nombre=nombre, telefono=telefono, correo=correo, password=password, estado='Activo')
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
