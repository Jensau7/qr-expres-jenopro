import unicodedata

def crear_slug(texto):
    # Quita acentos, diéresis y caracteres especiales
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8")
    return texto.lower().replace(" ", "-")

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
