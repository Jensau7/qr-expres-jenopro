from flask import Flask, render_template, request
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
    
    # Genera la URL directa del código QR usando la API externa de qrserver
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={quote(wa_url)}"
    
    mensaje_compra = quote(f"¡Hola! Quiero activar la tarjeta digital permanente para mi negocio '{negocio}'.")
    buy_url = f"https://wa.me/{MI_WHATSAPP}?text={mensaje_compra}"
    
    return render_template('preview.html', negocio=negocio, wa_url=wa_url, buy_url=buy_url, qr_url=qr_url)

if __name__ == '__main__':
    app.run()
