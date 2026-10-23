import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave_super_segura_jenopro'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(30), nullable=True)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='Pendiente') # 'Pendiente' o 'Activo'
    productos = db.relationship('Producto', backref='usuario', lazy=True, cascade='all, delete-orphan')

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_prod = db.Column(db.String(150), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('login'))

# LOGIN A PRUEBA DE FALLOS Y DE REINICIOS DE BASE DE DATOS
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        try:
            user = Usuario.query.filter_by(correo=correo).first()
            if not user:
                # Si se reinició la BD, crea al usuario al vuelo para que no se quede atorado
                user = Usuario(
                    nombre='INGENIO EN MADERA',
                    telefono='526141234567',
                    correo=correo,
                    password=password,
                    estado='Pendiente'
                )
                db.session.add(user)
                db.session.commit()
            
            if user.password == password:
                # REGLA CLAVE: Cada nueva sesión bloquea la edición hasta pagar la renovación de $50 MXN
                user.estado = 'Pendiente'
                db.session.commit()
                
                session['user_id'] = user.id
                session['nombre_negocio'] = user.nombre
                return redirect(url_for('panel'))
            else:
                error = "Contraseña incorrecta."
        except Exception:
            db.session.rollback()
            error = "Error al conectar. Intenta de nuevo."
            
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
            session['nombre_negocio'] = user.nombre
            return redirect(url_for('panel'))
        except Exception:
            db.session.rollback()
    return render_template('registro.html')

@app.route('/pagar_simulado')
def pagar_simulado():
    if 'user_id' in session:
        user = Usuario.query.get(session['user_id'])
        if user:
            user.estado = 'Activo'
            db.session.commit()
    return redirect(url_for('panel'))

@app.route('/panel')
def panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    usuario = Usuario.query.get(session['user_id'])
    if not usuario:
        session.clear()
        return redirect(url_for('login'))
    productos = Producto.query.filter_by(usuario_id=usuario.id).all()
    return render_template('panel.html', usuario=usuario, productos=productos)

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    usuario = Usuario.query.get(session['user_id'])
    
    if usuario.estado != 'Activo':
        return "Acceso denegado: Debes realizar el pago de $50 MXN para actualizar tu menú.", 403

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

@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    usuario = Usuario.query.get(session['user_id'])
    
    if usuario.estado != 'Activo':
        return "Acceso denegado: Debes realizar el pago para modificar productos.", 403

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
