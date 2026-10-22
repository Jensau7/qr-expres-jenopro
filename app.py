import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'

# Configuración de base de datos y carpeta de imágenes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)

db = SQLAlchemy(app)

# MODELOS
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(30), nullable=True)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    productos = db.relationship('Producto', backref='usuario', lazy=True, cascade='all, delete-orphan')

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_prod = db.Column(db.String(150), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True) # <-- Campo de descripción
    imagen = db.Column(db.String(200), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

with app.app_context():
    db.create_all()

# RUTAS
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        password = request.form.get('password')

        user = Usuario.query.filter_by(correo=correo).first()
        if not user:
            user = Usuario(nombre=nombre, telefono=telefono, correo=correo, password=password)
            db.session.add(user)
            db.session.commit()

        session['user_id'] = user.id
        session['nombre_negocio'] = user.nombre
        session['mostrar_aviso'] = True
        return redirect(url_for('panel'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        
        user = Usuario.query.filter_by(correo=correo, password=password).first()
        if user:
            session['user_id'] = user.id
            session['nombre_negocio'] = user.nombre
            session['mostrar_aviso'] = True
            return redirect(url_for('panel'))
        else:
            return "Datos incorrectos, intenta de nuevo."
            
    return render_template('login.html')

@app.route('/quitar_aviso')
def quitar_aviso():
    session.pop('mostrar_aviso', None)
    return '', 204

@app.route('/panel')
def panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['user_id'])
    productos = Producto.query.filter_by(usuario_id=usuario.id).all()
    return render_template('panel.html', usuario=usuario, productos=productos)

# RUTA PARA AGREGAR PRODUCTO CON FOTO Y DESCRIPCIÓN
@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    nombre_prod = request.form.get('nombre_prod')
    precio = request.form.get('precio')
    descripcion = request.form.get('descripcion')
    
    imagen_filename = None
    if 'imagen' in request.files:
        file = request.files['imagen']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))
            imagen_filename = filename

    nuevo_prod = Producto(
        nombre_prod=nombre_prod,
        precio=float(precio),
        descripcion=descripcion,
        imagen=imagen_filename,
        usuario_id=session['user_id']
    )
    db.session.add(nuevo_prod)
    db.session.commit()
    return redirect(url_for('panel'))

# RUTA PARA ELIMINAR PRODUCTO
@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    producto = Producto.query.get_or_404(id)
    if producto.usuario_id == session['user_id']:
        db.session.delete(producto)
        db.session.commit()
    return redirect(url_for('panel'))

@app.route('/menu/<int:user_id>')
def menu_publico(user_id):
    usuario = Usuario.query.get_or_404(user_id)
    productos = Producto.query.filter_by(usuario_id=user_id).all()
    return render_template('menu.html', usuario=usuario, productos=productos)

@app.route('/qr/<int:user_id>')
def qr_mesas(user_id):
    usuario = Usuario.query.get_or_404(user_id)
    return render_template('preview.html', usuario=usuario)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
