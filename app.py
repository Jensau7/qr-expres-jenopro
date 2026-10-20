cat << 'EOF' > app.py
from flask import Flask, render_template, request, send_file
import qrcode
import io

app = Flask(__name__)

MI_WHATSAPP = "526143665161"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview():
    negocio = request.form.get('negocio', 'INGENIO EN MADERA')
    telefono = request.form.get('telefono', MI_WHATSAPP).strip()
    mensaje = request.form.get('mensaje', '¡Hola! Vi tu tarjeta digital y quiero más información.')
    
    # Si por alguna razón el usuario no envía teléfono, usaremos tu número por defecto
    if not telefono:
        telefono = MI_WHATSAPP
        
    # Limpiamos el número de espacios o signos +
    telefono = telefono.replace('+', '').replace(' ', '').replace('-', '')
    
    # Construir enlace directo a WhatsApp
    from urllib.parse import quote
    mensaje_encoded = quote(mensaje)
    wa_url = f"https://wa.me/{telefono}?text={mensaje_encoded}"
    
    # Enlace para activación/compra
    mensaje_compra = quote(f"¡Hola! Quiero activar la tarjeta digital permanente para mi negocio '{negocio}'.")
    buy_url = f"https://wa.me/{MI_WHATSAPP}?text={mensaje_compra}"
    
    return render_template('preview.html', negocio=negocio, wa_url=wa_url, buy_url=buy_url)

@app.route('/qr')
def qr_code():
    url = request.args.get('url', '')
    if not url:
        return "URL requerida", 400
    
    img = qrcode.make(url)
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
EOF
