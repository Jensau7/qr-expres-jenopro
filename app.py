import os
import qrcode
from io import BytesIO
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='plantillas')
app.secret_key = os.environ.get('SECRET_KEY', 'jenopro_secret_key_2026')

# Configuración de Base de Datos (SQLite local / PostgreSQL en producción)
db_uri = os.environ.get('DATABASE_URL', 'sqlite:///jenopro.db')
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelos de la Base de Datos
class Negocio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    activo = db.Column(db.Boolean, default=False)
    productos = db.relationship('Producto', backref='negocio', lazy=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.String(20), nullable=False)
    foto = db.Column(db.String(300), nullable=True)
    negocio_id = db.Column(db.Integer, db.ForeignKey('negocio.id'), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre_negocio')
        telefono = request.form.get('telefono_wa')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existente = Negocio.query.filter_by(email=email).first()
        if existente:
            flash('El correo ya está registrado.', 'error')
            return redirect(url_for('registro'))
            
        nuevo_negocio = Negocio(
            nombre=nombre,
            telefono=telefono,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(nuevo_negocio)
        db.session.commit()
        
        session['negocio_id'] = nuevo_negocio.id
        return redirect(url_for('panel'))
    return render_template('registro.html')

@app.route('/panel')
def panel():
    if 'negocio_id' not in session:
        return redirect(url_for('registro'))
    negocio = Negocio.query.get(session['negocio_id'])
    return render_template('panel.html', negocio=negocio, productos=negocio.productos)

@app.route('/card/<int:negocio_id>')
def tarjeta(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    
    # Generar QR dinámico
    url_menu = request.host_url + f"card/{negocio.id}"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(url_menu)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    qr_url = f"data:image/png;base64,{qr_b64}"
    
    telefono_clean = ''.join(filter(str.isdigit, negocio.telefono))
    link_wa_cliente = f"https://wa.me/{telefono_clean}?text=Hola,%20quiero%20hacer%20un%20pedido"
    link_wa_activacion = f"https://wa.me/526141366516?text=Hola%20Noe,%20quiero%20activar%20mi%20negocio:%20{negocio.nombre}"

    return render_template('card.html',
                           nombre_negocio=negocio.nombre,
                           productos=negocio.productos,
                           qr_url=qr_url,
                           telefono_clean=telefono_clean,
                           link_wa_cliente=link_wa_cliente,
                           link_wa_activacion=link_wa_activacion)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
