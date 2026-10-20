from flask import Flask, render_template, request, send_file
import qrcode
import io
import urllib.parse

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        negocio = request.form.get('negocio', 'Tu Negocio Aquí')
        telefono = request.form.get('telefono', '5210000000000')
        mensaje = request.form.get('mensaje', '¡Hola! Vi tu tarjeta digital y quiero más información.')
        
        # Limpiar teléfono de espacios y caracteres extra
        telefono_clean = ''.join(filter(str.isdigit, telefono))
        
        # Generar URL de WhatsApp
        msg_encoded = urllib.parse.quote(mensaje)
        wa_url = f"https://wa.me/{telefono_clean}?text={msg_encoded}"
        
        return render_template('preview.html', negocio=negocio, telefono=telefono_clean, wa_url=wa_url)
    
    return render_template('index.html')

@app.route('/qr')
def generate_qr():
    url = request.args.get('url', 'https://qr-expres-jenopro.onrender.com')
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
