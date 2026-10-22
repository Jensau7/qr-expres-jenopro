from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'  # Reemplaza o mantén tu secret_key actual

# ==========================================
# MODELO DE EJEMPLO (Ajusta según tu base de datos)
# ==========================================
class Usuario:
    def __init__(self, id, correo, password, nombre):
        self.id = id
        self.correo = correo
        self.password = password
        self.nombre = nombre

# Simulación o conexión a tu base de datos existente
# Asegúrate de mantener la consulta real que ya usas en tu proyecto
def buscar_usuario(correo, password):
    # Aquí va tu consulta: Usuario.query.filter_by(correo=correo, password=password).first()
    pass

# ==========================================
# RUTAS PRINCIPALES
# ==========================================

@app.route('/')
index = lambda: redirect(url_for('login'))
app.add_url_rule('/', 'index', index)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        
        # Validación de usuario con tu lógica actual
        user = Usuario.query.filter_by(correo=correo, password=password).first() if 'Usuario' in globals() else None
        
        if user:
            session['user_id'] = user.id
            session['nombre_negocio'] = user.nombre
            session['mostrar_aviso'] = True  # Activa la alerta de los $50 pesos al iniciar sesión
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
    
    # Objeto de usuario para la plantilla
    usuario = type('obj', (object,), {
        'id': session.get('user_id'),
        'nombre': session.get('nombre_negocio', 'Mi Negocio')
    })
    
    return render_template('panel.html', usuario=usuario)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
