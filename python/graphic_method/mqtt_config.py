import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker, port, topic, on_message_callback):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = on_message_callback

    def connect(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"Erro ao conectar ao broker MQTT: {e}")

    def on_connect(self, client, userdata, flags, rc):
        print(f"Conectado ao broker MQTT com código {rc}")
        client.subscribe(self.topic)

    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Comando enviado: {message}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()