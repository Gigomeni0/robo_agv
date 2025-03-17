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

// Variáveis do encoder 1
volatile long pulseCount1 = 0;
int pulsesPerRevolution1 = 11;
float rpm1 = 0;
unsigned long lastTime1 = 0;

// Variáveis do encoder 2
volatile long pulseCount2 = 0;
int pulsesPerRevolution2 = 11;
float rpm2 = 0;
unsigned long lastTime2 = 0;

// Parâmetros da roda
float wheelDiameter = 12;                                          // Diâmetro da roda em cm
float wheelCircumference = PI * wheelDiameter;                     // Circunferência
float distancePerPulse = wheelCircumference / pulsesPerRevolution1; // Distância por pulso
float totalDistance1 = 0;
float totalDistance2 = 0;

// Funções de interrupção do encoder
void encoderISR1() {
  pulseCount1++;
}

void encoderISR2() {
  pulseCount2++;
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

  if (message == "F") {
    Serial.println("Ligando motores...");
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } 
  else if (message == "B") {
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
  pinMode(ENCODER_A2, INPUT);
  pinMode(ENCODER_B2, INPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  attachInterrupt(digitalPinToInterrupt(ENCODER_A), encoderISR1, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A2), encoderISR2, RISING);

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

  // Cálculos para o encoder 1
  if (currentTime - lastTime1 >= 1000) {
    rpm1 = (float)(pulseCount1 * 60) / (float)pulsesPerRevolution1;
    totalDistance1 += pulseCount1 * distancePerPulse;
    pulseCount1 = 0;
    lastTime1 = currentTime;

    Serial.print("Encoder 1 - RPM: ");
    Serial.print(rpm1);
    Serial.print(" | Distância total: ");
    Serial.print(totalDistance1);
    Serial.println(" cm");
  }

  // Cálculos para o encoder 2
  if (currentTime - lastTime2 >= 1000) {
    rpm2 = (float)(pulseCount2 * 60) / (float)pulsesPerRevolution2;
    totalDistance2 += pulseCount2 * distancePerPulse;
    pulseCount2 = 0;
    lastTime2 = currentTime;

    Serial.print("Encoder 2 - RPM: ");
    Serial.print(rpm2);
    Serial.print(" | Distância total: ");
    Serial.print(totalDistance2);
    Serial.println(" cm");
  }
}