import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
import mercadopago

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_qr_jenopro'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///jenopro.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

# Credencial de Producción Mercado Pago
MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'APP_USR-6064762100649336-102105-c9c4e7819f238771f3a72af8897b15c2-2903412042')
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

DOMAIN_URL = "https://qr-expres-jenopro.onrender.com"

# --- MODELOS ---
class Negocio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(20), default='Draft')  # Draft o Active
    productos = db.relationship('Producto', backref='negocio', lazy=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    negocio_id = db.Column(db.Integer, db.ForeignKey('negocio.id'), nullable=False)

# --- RUTAS PRINCIPALES ---
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

# --- MERCADO PAGO: COBRO DE ACTIVACIÓN DE $50 MXN ---
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
    preference = preference_response["response"]
    
    return redirect(preference["init_point"])

# --- NOTIFICACIÓN Y ACTIVACIÓN AUTOMÁTICA (WEBHOOK) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True) or request.args
    
    if data.get("type") == "payment" or data.get("topic") == "payment":
        payment_id = data.get("data", {}).get("id") or data.get("id")
        if payment_id:
            payment_info = sdk.payment().get(payment_id)
            payment = payment_info.get("response", {})
            
            if payment.get("status") == "approved":
                negocio_id = payment.get("external_reference")
                if negocio_id:
                    negocio = Negocio.query.get(int(negocio_id))
                    if negocio:
                        negocio.estado = 'Active'
                        db.session.commit()
    
    return jsonify({"status": "ok"}), 200

# --- RETORNOS DEL CHECKOUT ---
@app.route('/pago/exitoso/<int:negocio_id>')
def pago_exitoso(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    negocio.estado = 'Active'
    db.session.commit()
    flash('¡Pago acreditado con éxito! Tu cuenta ya está activa.', 'success')
    return redirect(url_for('panel', negocio_id=negocio.id))

@app.route('/pago/fallido/<int:negocio_id>')
def pago_fallido(negocio_id):
    flash('El pago no pudo completarse. Por favor reintenta.', 'danger')
    return redirect(url_for('panel', negocio_id=negocio_id))

@app.route('/pago/pendiente/<int:negocio_id>')
def pago_pendiente(negocio_id):
    flash('Tu pago está en proceso (ej. OXXO/SPEI). Se activará al confirmarse.', 'info')
    return redirect(url_for('panel', negocio_id=negocio_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
