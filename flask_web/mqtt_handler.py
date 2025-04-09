import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
obstacle_info = {}

def on_connect(client, userdata, flags, rc):
    print("Conectado ao MQTT Broker.")
    client.subscribe("robo_gaveteiro/status")

def on_message(client, userdata, msg):
    if msg.topic == "robo_gaveteiro/status":
        payload = json.loads(msg.payload.decode())
        x, y = payload.get("x"), payload.get("y")
        obstaculos = payload.get("obstaculos", {})

        global obstacle_info
        obstacle_info = obstaculos

        socketio = userdata["socketio"]
        socketio.emit("robot_status", {"x": x, "y": y, "obstaculos": obstaculos})

def get_obstacle_info():
    return obstacle_info

def start_mqtt_loop(socketio):
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set({"socketio": socketio})
    client.connect("localhost", 1883, 60)
    client.loop_start()
