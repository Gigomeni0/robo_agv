#include <Arduino.h>
#include <BluetoothSerial.h>
#include <PubSubClient.h>
#include <WiFi.h>

// Cliente Wi-Fi
WiFiClient espClient;
// Cliente MQTT
PubSubClient client(espClient);

const char* topico = "robo_gaveteiro/comandos";

// Pinos do encoder
#define ENCODER_A 4
#define ENCODER_B 5
#define ENCODER_A2 6
#define ENCODER_B2 7

// Pinos da Ponte H
#define IN1 15
#define IN2 16
#define IN3 17
#define IN4 18

// Variáveis do encoder
volatile long pulseCount = 0;
int pulsesPerRevolution = 11;
float rpm = 0;
unsigned long lastTime = 0;

// Parâmetros da roda
float wheelDiameter = 12;                                          // Diâmetro da roda em cm
float wheelCircumference = PI * wheelDiameter;                     // Circunferência
float distancePerPulse = wheelCircumference / pulsesPerRevolution; // Distância por pulso
float totalDistance = 0;

// Função de interrupção do encoder
void encoderISR() {
  pulseCount++;
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Mensagem recebida no tópico: ");
  Serial.println(topic);

  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Mensagem: ");
  Serial.println(message);

  if (message == "ligar") {
    Serial.println("Ligando motores...");
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } 
  else if (message == "desligar") {
    Serial.println("Desligando motores...");
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
  }
}

void connectToWifi(const char* SSID, const char* password) {
  Serial.println("Conectando ao Wi-Fi...");
  WiFi.begin(SSID, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi conectado!");
}

void connectToMQTT(const char* clientID, const char* mqttServer, int mqttPort, const char* user, const char* password) {
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback);

  while (!client.connected()) {
    Serial.print("Conectando ao Broker MQTT...");
    if (client.connect(clientID, user, password)) {
      Serial.println(" Conectado!");
      client.subscribe(topico);
      Serial.print("Inscrito no tópico: ");
      Serial.println(topico);
    } 
    else {
      Serial.print(" Falha, rc=");
      Serial.print(client.state());
      Serial.println(" Tentando novamente em 5 segundos...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  connectToWifi("Gigo2.4G", "18253122Ro");
  connectToMQTT("ESP32Client", "test.mosquitto.org", 1883, "espClient", "");

  // Configuração dos pinos
  pinMode(ENCODER_A, INPUT);
  pinMode(ENCODER_B, INPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  attachInterrupt(digitalPinToInterrupt(ENCODER_A), encoderISR, RISING);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void loop() {
  if (!client.connected()) {
    connectToMQTT("ESP32Client", "test.mosquitto.org", 1883, "espClient", "");
  }

  client.loop();  // Mantém a conexão ativa e escuta mensagens

  unsigned long currentTime = millis();
  unsigned long timeElapsed = currentTime - lastTime;

  if (timeElapsed >= 1000) {
    rpm = (float)(pulseCount * 60) / (float)pulsesPerRevolution;
    totalDistance += pulseCount * distancePerPulse;
    pulseCount = 0;
    lastTime = currentTime;

    Serial.print("RPM: ");
    Serial.print(rpm);
    Serial.print(" | Distância total: ");
    Serial.print(totalDistance);
    Serial.println(" cm");
  }
}
