import os
import urllib.parse
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST', 'GET'])
def generar():
    # Si recargan la página por GET, mandamos valores por defecto para que no truene
    if request.method == 'GET':
        negocio = "INGENIO EN MADERA"
        telefono = "526143665161"
    else:
        negocio = request.form.get('negocio', 'INGENIO EN MADERA')
        telefono = request.form.get('telefono', '526143665161')
    
    mensaje = f"Hola, me interesa más información sobre los servicios de {negocio}."
    
    wa_encoded_msg = urllib.parse.quote(mensaje)
    wa_url = f"https://wa.me/{telefono}?text={wa_encoded_msg}"
    
    encoded_wa_url = urllib.parse.quote(wa_url, safe='')
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_wa_url}"
    
    buy_url = "https://www.paypal.com"

    return render_template('preview.html', negocio=negocio, qr_url=qr_url, wa_url=wa_url, buy_url=buy_url)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
