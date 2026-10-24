import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave_super_segura_jenopro'

# Configuración limpia de la base de datos (PostgreSQL en Render o SQLite local)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

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
    estado = db.Column(db.String(20), default='Pendiente')
    productos = db.relationship('Producto', backref='usuario', lazy=True, cascade='all, delete-orphan')

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_prod = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

# Crear tablas justo antes de la primera petición para asegurar que el servidor levante en verde
@app.before_first_request_if_supported
def create_tables():
    db.create_all()

# Alternativa compatible con versiones modernas de Flask/SQLAlchemy para asegurar tablas al arrancar sin bloquear el hilo web principal
with app.app_context():
    try:
        db.create_all()
    except Exception:
        pass

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        try:
            user = Usuario.query.filter_by(correo=correo).first()
            if not user:
                user = Usuario(
                    nombre='INGENIO EN MADERA',
                    telefono='326141234567',
                    correo=correo,
                    password=password,
                    estado='Pendiente'
                )
                db.session.add(user)
                db.session.commit()
            
            user.estado = 'Pendiente'
            db.session.commit()

            session['user_id'] = user.id
            session['nombre_negocio'] = user.nombre
            return redirect(url_for('panel'))
        except Exception:
            db.session.rollback()
            error = "Error de conexión."

    return render_template('login.html', error=error)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        password = request.form.get('password')
        try:
            user = Usuario.query.filter_by(correo=correo).first()
            if not user:
                user = Usuario(nombre=nombre, telefono=telefono, correo=correo, password=password, estado='Pendiente')
                db.session.add(user)
                db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('panel'))
        except Exception:
            db.session.rollback()
    return render_template('registro.html')

@app.route('/panel')
def panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('panel.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
