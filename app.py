cd ~/qr-expres-jenopro
cat << 'EOF' > app.py
from flask import Flask, render_template, request, send_file
import qrcode
import io
import urllib.parse

app = Flask(__name__)

MI_WHATSAPP = "526143665161"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview():
    negocio = request.form.get('negocio', 'Tu Negocio Aquí')
    telefono = request.form.get('telefono', MI_WHATSAPP)
    mensaje = request.form.get('mensaje', '¡Hola! Vi tu tarjeta digital y quiero más información.')
    
    telefono_clean = ''.join(filter(str.isdigit, telefono))
    msg_encoded = urllib.parse.quote(mensaje)
    wa_url = f"https://wa.me/{telefono_clean}?text={msg_encoded}"
    
    buy_msg = urllib.parse.quote(f"Hola, quiero activar mi tarjeta digital para mi negocio: {negocio}")
    buy_url = f"https://wa.me/{MI_WHATSAPP}?text={buy_msg}"
    
    return render_template('preview.html', negocio=negocio, telefono=telefono_clean, wa_url=wa_url, buy_url=buy_url)

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
EOF
