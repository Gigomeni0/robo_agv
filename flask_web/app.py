
# Criando um app.py básico que importa mqtt_manager
from flask import Flask, render_template, request, redirect
import mqtt_manager

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mover', methods=['POST'])
def mover():
    direcao = request.form.get('direcao')
    if direcao:
        mqtt_manager.publicar_comando(direcao)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
