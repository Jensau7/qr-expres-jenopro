from flask import Flask, render_template, request, send_file
import qrcode
import io

app = Flask(__name__)

# Tu número oficial (sin ceros ni números de prueba)
MI_WHATSAPP = "526143665161"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview():
    negocio = request.form.get('negocio', 'INGENIO EN MADERA')
    telefono_input = request.form.get('telefono', '').strip()
    
    # Si viene vacío o trae el número de prueba viejo, usamos tu número real
    if not telefono_input or "0000000" in telefono_input:
        telefono = MI_WHATSAPP
    else:
        telefono = telefono_input.replace('+', '').replace(' ', '').replace('-', '')
    
    mensaje = request.form.get('mensaje', f'¡Hola! Vi tu tarjeta digital de {negocio} y quiero más información.')
    
    from urllib.parse import quote
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
    
    img = qrcode.make(url)
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
