from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'  # Mantén tu secret key actual

# Configuración de tu base de datos (ajusta si usas otra ruta o URI)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' # O tu configuración actual
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==========================================
# TUS MODELOS ORIGINALES (Asegúrate de conservar tus tablas)
# ==========================================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# ==========================================
# RUTAS DE LA APLICACIÓN
# ==========================================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        
        # Consulta original a tu base de datos
        user = Usuario.query.filter_by(correo=correo, password=password).first()
        
        if user:
            session['user_id'] = user.id
            session['nombre_negocio'] = user.nombre
            session['mostrar_aviso'] = True  # <-- Activa la alerta de los $50 pesos al iniciar sesión
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
