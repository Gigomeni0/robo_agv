import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import threading
import socket
import random
import time

app = Flask(__name__)
socketio = SocketIO(app)

# MQTT Settings
broker_address = "192.168.11.2"
COMMAND_TOPIC = "robo_gaveteiro/comandos"
STATUS_TOPIC = "robo_gaveteiro/status"

is_connected = False

# Estado dos sensores ao redor do robô
sensor_state = {
    "front": False,
    "back": False,
    "left": False,
    "right": False
}

# Inicializa MQTT
mqtt_client = mqtt.Client()


import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # conecta a um IP externo qualquer só pra descobrir qual interface será usada
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def on_connect(client, userdata, flags, rc):
    global is_connected
    if rc == 0:
        print("Conectado ao broker MQTT!")
        client.subscribe(STATUS_TOPIC)
        is_connected = True
    else:
        print(f"Falha na conexão. Código de retorno: {rc}")
        is_connected = False


def on_disconnect(client, userdata, rc):
    global is_connected
    print("Desconectado do broker MQTT.")
    is_connected = False


def on_message(client, userdata, msg):
    global sensor_state
    if msg.topic == STATUS_TOPIC:
        try:
            payload = msg.payload.decode()
            sensor_state.update(eval(payload))  # Ex: {'front': True, 'back': False, ...}
            socketio.emit('sensor_update', sensor_state)
        except Exception as e:
            print("Erro ao processar mensagem MQTT:", e)


mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message
mqtt_client.connect(broker_address, 1883, 60)

def mqtt_loop():
    mqtt_client.loop_forever()

threading.Thread(target=mqtt_loop).start()

# Posição simulada do robô
x, y = 5, 5
obstacles = set()

def simulate_robot_position():
    global x, y
    while True:
        socketio.emit('robot_position', {'x': x, 'y': y, 'obstacles': list(obstacles)})
        socketio.sleep(1)

@socketio.on('connect')
def handle_connect():
    print("Cliente conectado via WebSocket")

@socketio.on('send_command')
def handle_send_command(data):
    command = data.get('command')
    if command in ['F', 'D', 'E'] or (command.endswith('W') and command[:-1].isdigit()):
        mqtt_client.publish(COMMAND_TOPIC, command)
        print(f"Enviado comando: {command}")
    else:
        print(f"Comando inválido recebido: {command}")
        
@socketio.on('definir_base')
def handle_definir_base():
    print("Base definida.")
    mqtt_client.publish(COMMAND_TOPIC, "SET_BASE")

    
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send_command", methods=["POST"])
def send_command():
    data = request.json
    command = data.get("command")

    blocked = (
        (command == "F" and sensor_state.get("front")) or
        (command == "B" and sensor_state.get("back")) or
        (command == "L" and sensor_state.get("left")) or
        (command == "R" and sensor_state.get("right"))
    )

    if blocked:
        return jsonify({"status": "blocked"})

    mqtt_client.publish(COMMAND_TOPIC, command)
    return jsonify({"status": "sent"})

@app.route("/broker_status")
def broker_status():
    try:
        with socket.create_connection((broker_address, 1883), timeout=2):
            mosquitto_running = True
    except Exception:
        mosquitto_running = False

    return jsonify({
        "broker_ip": broker_address,
        "mosquitto_running": mosquitto_running,
        "mqtt_connected": is_connected
    })

if __name__ == "__main__":
    ip_address = get_local_ip()
    print(f"Servidor rodando em: http://{ip_address}:5000")
    socketio.start_background_task(simulate_robot_position)
    socketio.run(app, host="0.0.0.0", port=5055, debug=False, use_reloader=False)


