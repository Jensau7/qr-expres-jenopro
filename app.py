import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
import mercadopago

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_qr_jenopro'
# Cambiamos el nombre a jenopro_v2.db para recrear la tabla limpia con email y password
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///jenopro_v2.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
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
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    negocio_id = db.Column(db.Integer, db.ForeignKey('negocio.id'), nullable=False)

with app.app_context():
    db.create_all()

MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'APP_USR-6064762100649336-102105-c9c4e7819f238771f3a72af8897b15c2-2903412042')
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
DOMAIN_URL = "https://qr-expres-jenopro.onrender.com"

# --- RUTAS ---
@app.route('/')
def index():
    return render_template('registro.html')

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
            
        slug = nombre.lower().replace(" ", "-")
        
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
    return render_template('registro.html')

@app.route('/panel/<int:negocio_id>')
def panel(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    return render_template('panel.html', negocio=negocio)

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
