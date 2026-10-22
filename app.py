import os
import unicodedata
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import mercadopago

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_qr_jenopro'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///jenopro_v2.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de carpeta para subir imágenes
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear la carpeta de imágenes si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def crear_slug(texto):
    # Remueve acentos, diéresis y caracteres especiales
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8")
    return texto.lower().replace(" ", "-")

# --- MODELOS DE LA BASE DE DATOS ---
class Negocio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(20), default='Draft')
    productos = db.relationship('Producto', backref='negocio', lazy=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_primary=True) if False else db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    imagen = db.Column(db.String(300), nullable=True)
    negocio_id = db.Column(db.Integer, db.ForeignKey('negocio.id'), nullable=False)

with app.app_context():
    db.create_all()

# --- CONFIGURACIÓN MERCADO PAGO ---
MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'APP_USR-650264623324783-102109-c9aab1f86523917492f1ea4d6966ff1e-3782800866')
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
DOMAIN_URL = "https://qr-expres-jenopro.onrender.com"

# --- RUTAS DE AUTENTICACIÓN ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not nombre or not telefono or not email or not password:
            flash('Por favor completa todos los campos requeridos.', 'danger')
            return render_template('registro.html')
            
        slug = crear_slug(nombre)
        
        existente = Negocio.query.filter_by(slug=slug).first()
        if existente:
            flash('Ese negocio ya existe. Inicia sesión para acceder.', 'danger')
            return render_template('registro.html')
        
        try:
            nuevo_negocio = Negocio(
                nombre=nombre, 
                telefono=telefono, 
                email=email, 
                password=password, 
                slug=slug, 
                estado='Draft'
            )
            db.session.add(nuevo_negocio)
            db.session.commit()
            return redirect(url_for('panel', negocio_id=nuevo_negocio.id))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el registro.', 'danger')
            return render_template('registro.html')
            
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        negocio = Negocio.query.filter_by(email=email, password=password).first()
        
        if negocio:
            return redirect(url_for('panel', negocio_id=negocio.id))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
            return render_template('login.html')
            
    return render_template('login.html')

# --- PANEL DE CONTROL Y PRODUCTOS ---
@app.route('/panel/<int:negocio_id>')
def panel(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    return render_template('panel.html', negocio=negocio)

@app.route('/agregar_producto/<int:negocio_id>', methods=['POST'])
def agregar_producto(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    if negocio.estado != 'Active':
        flash('Debes activar tu cuenta para agregar productos.', 'danger')
        return redirect(url_for('panel', negocio_id=negocio.id))

    nombre = request.form.get('nombre')
    precio = request.form.get('precio')
    descripcion = request.form.get('descripcion')
    
    filename = None
    if 'imagen' in request.files:
        file = request.files['imagen']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"negocio_{negocio.id}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

    if nombre and precio:
        nuevo_prod = Producto(
            nombre=nombre,
            precio=float(precio),
            descripcion=descripcion,
            imagen=filename,
            negocio_id=negocio.id
        )
        db.session.add(nuevo_prod)
        db.session.commit()
        flash('Producto agregado con éxito.', 'success')

    return redirect(url_for('panel', negocio_id=negocio.id))

# --- MENÚ PÚBLICO (VISTA QR CLIENTE) ---
@app.route('/menu/<slug>')
def ver_menu(slug):
    negocio = Negocio.query.filter_by(slug=slug).first_or_404()
    return render_template('menu.html', negocio=negocio)

# --- ACTIVACIÓN Y PAGO ---
@app.route('/activar_directo/<int:negocio_id>')
def activar_directo(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    negocio.estado = 'Active'
    db.session.commit()
    flash('¡Cuenta activada manualmente para pruebas!', 'success')
    return redirect(url_for('panel', negocio_id=negocio.id))

@app.route('/pagar/<int:negocio_id>', methods=['POST'])
def pagar_activacion(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    preference_data = {
        "items": [
            {
                "title": f"Activación Licencia QR JeNoPro - {negocio.nombre}",
                "quantity": 1,
                "unit_price": 50.00,
                "currency_id": "MXN"
            }
        ],
        "external_reference": str(negocio.id),
        "back_urls": {
            "success": f"{DOMAIN_URL}/pago/exitoso/{negocio.id}",
            "failure": f"{DOMAIN_URL}/pago/fallido/{negocio.id}",
            "pending": f"{DOMAIN_URL}/pago/pendiente/{negocio.id}"
        },
        "auto_return": "approved",
    }
    preference_response = sdk.preference().create(preference_data)
    return redirect(preference_response["response"]["init_point"])

@app.route('/pago/exitoso/<int:negocio_id>')
def pago_exitoso(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    negocio.estado = 'Active'
    db.session.commit()
    flash('¡Pago acreditado con éxito! Tu cuenta ya está activa.', 'success')
    return redirect(url_for('panel', negocio_id=negocio.id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
