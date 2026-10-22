from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de Usuario
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(30), nullable=True)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Crear tablas al iniciar
with app.app_context():
    db.create_all()

# ==========================================
# RUTAS DE LA APLICACIÓN
# ==========================================

@app.route('/')
def index():
    return redirect(url_for('registro'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        password = request.form.get('password')

        # Buscar si ya existe el usuario
        usuario_existente = Usuario.query.filter_by(correo=correo).first()
        if usuario_existente:
            user = usuario_existente
        else:
            nuevo_usuario = Usuario(nombre=nombre, telefono=telefono, correo=correo, password=password)
            db.session.add(nuevo_usuario)
            db.session.commit()
            user = nuevo_usuario

        # Iniciar sesión automáticamente
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
    return render_template('panel.html', usuario=usuario)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
