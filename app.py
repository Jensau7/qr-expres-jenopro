cd ~/qr-expres-jenopro

cat << 'EOF' > app.py
from flask import Flask, render_template, request, send_file
import qrcode
import io
from urllib.parse import quote

app = Flask(__name__)

MI_WHATSAPP = "526143665161"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST', 'GET'])
def preview():
    negocio = request.form.get('negocio', 'INGENIO EN MADERA').strip()
    telefono = MI_WHATSAPP
    mensaje = f"¡Hola! Vi tu tarjeta digital de {negocio} y me interesa información."
    
    mensaje_encoded = quote(mensaje)
    wa_url = f"https://wa.me/{telefono}?text={mensaje_encoded}"
    
    mensaje_compra = quote(f"¡Hola! Quiero activar la tarjeta digital permanente para mi negocio '{negocio}'.")
    buy_url = f"https://wa.me/{MI_WHATSAPP}?text={mensaje_compra}"
    
    return render_template('preview.html', negocio=negocio, wa_url=wa_url, buy_url=buy_url)

@app.route('/qr')
def qr_code():
    url = request.args.get('url', '')
    if not url:
        return "URL requerida", 400
    
    # Generación explícita del código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png', as_attachment=False)

if __name__ == '__main__':
    app.run()
EOF
