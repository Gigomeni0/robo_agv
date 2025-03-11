import json
import paho.mqtt.client as mqtt

class MQTTManager:
    def __init__(self, broker, port, topics, on_message_callback):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = on_message_callback
        self.broker = broker
        self.port = port
        self.topics = topics if isinstance(topics, list) else [topics]

    def connect(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"Erro ao conectar ao broker MQTT: {e}")

    def on_connect(self, client, userdata, flags, rc):
        print(f"📡 Conectado ao broker MQTT com código {rc}")
        for topic in self.topics:
            client.subscribe(topic)
            print(f"📡 Inscrito no tópico: {topic}")

    def publish(self, topic, message):
        payload = json.dumps(message) if isinstance(message, dict) else message
        self.client.publish(topic, payload)
        print(f"📤 Mensagem enviada para {topic}: {payload}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
