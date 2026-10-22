import os
import re
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class Negocio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    estado = db.Column(db.String(20), default='Draft')
    tema = db.Column(db.String(30), default='carpinteria')
    logo = db.Column(db.String(255))
    banner = db.Column(db.String(255))
    productos = db.relationship('Producto', backref='negocio', lazy=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255))
    categoria = db.Column(db.String(50), default='General')
    imagen = db.Column(db.String(255))
    negocio_id = db.Column(db.Integer, db.ForeignKey('negocio.id'), nullable=False)

with app.app_context():
    inspector = inspect(db.engine)
    if 'negocio' in inspector.get_table_names():
        columnas = [col['name'] for col in inspector.get_columns('negocio')]
        if 'tema' not in columnas:
            db.drop_all()
    db.create_all()

def generar_slug(texto):
    texto = texto.lower().strip()
    texto = re.sub(r'[^\w\s-]', '', texto)
    return re.sub(r'[\s_-]+', '-', texto)

@app.route('/')
def home():
    return redirect(url_for('registro'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        password = request.form.get('password')

        slug_base = generar_slug(nombre)
        slug = slug_base
        contador = 1
        while Negocio.query.filter_by(slug=slug).first():
            slug = f"{slug_base}-{contador}"
            contador += 1

        nuevo_negocio = Negocio(
            nombre=nombre,
            telefono=telefono,
            correo=correo,
            password=password,
            slug=slug,
            estado='Draft',
            tema='carpinteria'
        )
        db.session.add(nuevo_negocio)
        db.session.commit()

        return redirect(url_for('panel', negocio_id=nuevo_negocio.id))

    return render_template('registro.html')

@app.route('/panel/<int:negocio_id>')
def panel(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    return render_template('panel.html', negocio=negocio)

@app.route('/cambiar_tema/<int:negocio_id>', methods=['POST'])
def cambiar_tema(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    nuevo_tema = request.form.get('tema')
    if nuevo_tema:
        negocio.tema = nuevo_tema
        db.session.commit()
    return redirect(url_for('panel', negocio_id=negocio.id))

@app.route('/actualizar_branding/<int:negocio_id>', methods=['POST'])
def actualizar_branding(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    
    logo_file = request.files.get('logo')
    if logo_file and logo_file.filename != '':
        filename = f"logo_{negocio_id}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logo_file.save(filepath)
        negocio.logo = filename

    banner_file = request.files.get('banner')
    if banner_file and banner_file.filename != '':
        filename = f"banner_{negocio_id}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        banner_file.save(filepath)
        negocio.banner = filename

    db.session.commit()
    return redirect(url_for('panel', negocio_id=negocio.id))

@app.route('/pagar/<int:negocio_id>', methods=['POST'])
def pagar(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    negocio.estado = 'Active'
    db.session.commit()
    return redirect(url_for('panel', negocio_id=negocio.id))

@app.route('/activar_directo/<int:negocio_id>')
def activar_directo(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    negocio.estado = 'Active'
    db.session.commit()
    return redirect(url_for('panel', negocio_id=negocio.id))

@app.route('/agregar_producto/<int:negocio_id>', methods=['POST'])
def agregar_producto(negocio_id):
    negocio = Negocio.query.get_or_404(negocio_id)
    nombre = request.form.get('nombre')
    precio = float(request.form.get('precio'))
    descripcion = request.form.get('descripcion')
    categoria = request.form.get('categoria') or 'General'
    
    imagen_file = request.files.get('imagen')
    filename = None

    if imagen_file and imagen_file.filename != '':
        filename = f"{negocio_id}_{generar_slug(nombre)}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imagen_file.save(filepath)

    nuevo_prod = Producto(
        nombre=nombre,
        precio=precio,
        descripcion=descripcion,
        categoria=categoria,
        imagen=filename,
        negocio_id=negocio.id
    )
    db.session.add(nuevo_prod)
    db.session.commit()

    return redirect(url_for('panel', negocio_id=negocio.id))

@app.route('/menu/<slug>')
def menu_publico(slug):
    negocio = Negocio.query.filter_by(slug=slug).first_or_404()
    categorias_dict = {}
    for prod in negocio.productos:
        cat = prod.categoria if prod.categoria else 'General'
        if cat not in categorias_dict:
            categorias_dict[cat] = []
        categorias_dict[cat].append(prod)

    return render_template('menu.html', negocio=negocio, categorias=categorias_dict)

if __name__ == '__main__':
    app.run(debug=True)
