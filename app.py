import os
import qrcode
from flask import Flask, render_template, request, send_file, url_for
from io import BytesIO
import urllib.parse

app = Flask(__name__)

# Tu número de WhatsApp para recibir cobros/activaciones (10 dígitos con código de país)
TU_NUMERO_WHATSAPP = "526141366516" 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nombre_negocio = request.form.get('nombre_negocio', '').strip()
        telefono_wa = request.form.get('telefono_wa', '').strip()
        
        if nombre_negocio and telefono_wa:
            # Limpiar número de teléfono
            telefono_clean = ''.join(filter(str.isdigit, telefono_wa))
            if not telefono_clean.startswith('52') and len(telefono_clean) == 10:
                telefono_clean = '52' + telefono_clean
                
            # Mensaje automático para el cliente del negocio
            msg_cliente = f"Hola, vi tu tarjeta digital de {nombre_negocio} y me interesa saber más sobre tus productos/servicios."
            link_wa_cliente = f"https://wa.me/{telefono_clean}?text={urllib.parse.quote(msg_cliente)}"
            
            # Mensaje de activación para ti ($50 MXN)
            msg_activacion = f"Hola Noé, quiero activar la tarjeta permanente para mi negocio: {nombre_negocio} (Tel: {telefono_clean})."
            link_wa_activacion = f"https://wa.me/{TU_NUMERO_WHATSAPP}?text={urllib.parse.quote(msg_activacion)}"
            
            return render_template(
                'card.html',
                nombre_negocio=nombre_negocio,
                link_wa_cliente=link_wa_cliente,
                link_wa_activacion=link_wa_activacion,
                qr_url=url_for('generate_qr', data=link_wa_cliente)
            )
            
    return render_template('index.html')

@app.route('/qr')
def generate_qr():
    data = request.args.get('data', '')
    if not data:
        return "No data provided", 400
        
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return send_file(buffer, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
