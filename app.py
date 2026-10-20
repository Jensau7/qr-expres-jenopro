import os
import io
import urllib.parse
from flask import Flask, render_template_string, request, send_file
import qrcode

app = Flask(__name__)

PAYPAL_EMAIL = "snoe7217@gmail.com"
PRECIO_ACTIVACION = "50.00"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ QR Exprés JeNoPro - Tarjeta y QR Digital</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .card-profile { max-width: 480px; margin: 30px auto; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border: none; }
        .header-banner { background: linear-gradient(135deg, #0d6efd, #0dcaf0); color: white; border-radius: 20px 20px 0 0; padding: 30px 20px; text-align: center; }
        .qr-box { background: white; padding: 15px; border-radius: 15px; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
        .btn-ws { background-color: #25D366; color: white; font-weight: bold; font-size: 1.1rem; border-radius: 50px; padding: 12px; }
        .btn-ws:hover { background-color: #1eb857; color: white; }
        .badge-demo { background-color: #ffc107; color: #000; font-weight: bold; padding: 8px 15px; border-radius: 20px; }
    </style>
</head>
<body>

<div class="container">
    <div class="card card-profile">
        <div class="header-banner">
            <h5 class="text-uppercase tracking-wide opacity-75">⚡ QR Exprés JeNoPro</h5>
            <h2 class="fw-bold mt-2 mb-0">{{ negocio }}</h2>
            {% if rubro %}
            <p class="mb-0 text-capitalize opacity-90">Servicio de {{ rubro }}</p>
            {% endif %}
        </div>

        <div class="card-body text-center p-4">

            {% if es_demo %}
            <div class="mb-3">
                <span class="badge-demo">⚠️ MUESTRA DE VISTA PREVIA</span>
            </div>
            {% endif %}

            <div class="qr-box my-3">
                <img src="/qr?tel={{ tel }}&negocio={{ negocio_encoded }}" alt="Código QR" class="img-fluid" style="max-width: 200px;">
            </div>

            <p class="text-muted small">Escanea el código para abrir el chat de WhatsApp directo o toca el botón de abajo</p>

            <div class="d-grid gap-2 my-4">
                <a href="https://wa.me/521{{ tel }}?text=Hola%20{{ negocio_encoded }},%20vi%20su%20tarjeta%20digital%20y%20me%20interesa%20información" 
                   target="_blank" class="btn btn-ws">
                   💬 Contactar por WhatsApp
                </a>
            </div>

            <hr class="my-4">

            {% if es_demo %}
            <div class="card bg-light border-warning p-3 text-start">
                <h6 class="fw-bold text-dark mb-1">¿Quieres activar la versión permanente?</h6>
                <p class="small text-muted mb-3">Por solo <strong>$50 MXN</strong> obtienes:</p>
                <ul class="small text-muted ps-3 mb-3">
                    <li>Descarga de tu Código QR en Alta Definición para imprimir.</li>
                    <li>Enlace dinámico permanente sin marcas de agua.</li>
                    <li>Botón directo a tu WhatsApp funcionando 24/7.</li>
                </ul>
                <a href="https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={{ paypal_email }}&item_name=Activacion%20Tarjeta%20QR%20-%20{{ negocio_encoded }}&amount={{ precio }}&currency_code=MXN&return={{ request_url }}" 
                   class="btn btn-warning fw-bold w-100">
                   💳 Activar mi Tarjeta por ${{ precio }} MXN
                </a>
            </div>
            {% else %}
            <div class="alert alert-success fw-bold">
                ¡Tarjeta Activa y Confirmada! 🚀
            </div>
            {% endif %}

        </div>
        <div class="card-footer text-center text-muted small py-3">
            © QR Exprés JeNoPro - Tarjetas Digitales Rápidas
        </div>
    </div>
</div>

</body>
</html>
"""

@app.route('/')
@app.route('/demo')
def demo():
    negocio = request.args.get('negocio', 'Tu Negocio Aquí')
    tel = request.args.get('tel', '6140000000')
    rubro = request.args.get('rubro', '')
    es_demo = request.args.get('activo', 'false') != 'true'

    negocio_encoded = urllib.parse.quote(negocio)
    request_url = request.url

    return render_template_string(
        HTML_TEMPLATE,
        negocio=negocio,
        tel=tel,
        rubro=rubro,
        es_demo=es_demo,
        negocio_encoded=negocio_encoded,
        paypal_email=PAYPAL_EMAIL,
        precio=PRECIO_ACTIVACION,
        request_url=request_url
    )

@app.route('/qr')
def generar_qr():
    tel = request.args.get('tel', '6140000000')
    negocio = request.args.get('negocio', '')
    
    url_whatsapp = f"https://wa.me/521{tel}?text=Hola%20{urllib.parse.quote(negocio)},%20vi%20su%20tarjeta%20digital"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url_whatsapp)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0d6efd", back_color="white")
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
