import os
import base64
from io import BytesIO
import urllib.parse
from flask import Flask, render_template, request
import qrcode

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    negocio = request.form.get('negocio', 'Mi Negocio')
    telefono = request.form.get('telefono', '526143665161')
    mensaje = f"Hola, me interesa más información sobre los servicios de {negocio}."
    
    # Enlace directo de WhatsApp con codificación segura
    wa_encoded_msg = urllib.parse.quote(mensaje)
    wa_url = f"https://wa.me/{telefono}?text={wa_encoded_msg}"
    
    # Generar la imagen del QR de forma local y 100% independiente en memoria
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(wa_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a Base64 para inyectarlo directo en el HTML sin depender de archivos temporales
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    qr_url = f"data:image/png;base64,{qr_base64}"
    
    buy_url = "https://www.paypal.com"

    return render_template('preview.html', negocio=negocio, qr_url=qr_url, wa_url=wa_url, buy_url=buy_url)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
