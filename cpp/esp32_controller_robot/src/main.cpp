#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <PID_v1.h>

// ---- Configurações Wi-Fi e MQTT ----
const char* ssid = "Gigo2.4G";
const char* password = "18253122Ro";
const char* mqttServer = "test.mosquitto.org";
const char* topicoComandos = "robo_gaveteiro/comandos";
const char* topicoSensores = "robo_gaveteiro/sensores";

WiFiClient espClient;
PubSubClient client(espClient);

// ---- Definições de Pinos ----
// Motores (H-Bridge L298N)
#define IN1 15
#define IN2 16
#define ENA 14  // PWM Motor 1
#define IN3 17
#define IN4 18
#define ENB 19  // PWM Motor 2

// Encoders (Motores com encoder A/B)
#define ENCODER_A 4
#define ENCODER_B 5
#define ENCODER_A2 6
#define ENCODER_B2 7

// Sensores Ultrassônicos
#define TRIG_FRONT 22
#define ECHO_FRONT 23

// ---- Variáveis dos Encoders ----
volatile long pulseCount1 = 0;
volatile long pulseCount2 = 0;
float pulsesPerRevolution = 11;
float wheelDiameter = 12; // cm
float wheelCircumference = PI * wheelDiameter;
float distancePerPulse = wheelCircumference / pulsesPerRevolution;

// ---- PID ----
double input1, output1, setpoint1;
double input2, output2, setpoint2;

PID pid1(&input1, &output1, &setpoint1, 1.0, 0.5, 0.2, DIRECT);
PID pid2(&input2, &output2, &setpoint2, 1.0, 0.5, 0.2, DIRECT);

float targetDistance = 0;
bool executing = false;

// ---- Comandos ----
unsigned long commandStartTime = 0;  // Tempo inicial do comando
unsigned long maxCommandTime = 5000; // Tempo máximo para cada comando (em milissegundos)
String commandQueue = "";
int commandIndex = 0;
unsigned long waitTimer = 0;
bool waiting = false;

// ---- Funções dos Encoders ----
void IRAM_ATTR encoderISR1() {
  if (digitalRead(ENCODER_B) == HIGH) pulseCount1++;
  else pulseCount1--;
}

void IRAM_ATTR encoderISR2() {
  if (digitalRead(ENCODER_B2) == HIGH) pulseCount2++;
  else pulseCount2--;
}

// ---- Conexão Wi-Fi ----
void connectWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Conectado!");
}

// ---- Callback MQTT ----
void callback(char* topic, byte* payload, unsigned int length) {
  commandQueue = "";
  for (int i = 0; i < length; i++) {
    commandQueue += (char)payload[i];
  }
  Serial.print("Comandos Recebidos: ");
  Serial.println(commandQueue);
  commandIndex = 0;
  executing = false;
}

// ---- Conexão MQTT ----
void connectMQTT() {
  client.setServer(mqttServer, 1883);
  client.setCallback(callback);
  
  while (!client.connected()) {
    if (client.connect("ESP32Client")) {
      Serial.println("Conectado ao Broker MQTT");
      client.subscribe(topicoComandos);
    } else {
      Serial.print("Falha MQTT, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}


// ---- Função de Movimentação ----
void moveMotors(int pwm1, int pwm2) {
  digitalWrite(IN1, pwm1 > 0);
  digitalWrite(IN2, pwm1 <= 0);
  digitalWrite(IN3, pwm2 > 0);
  digitalWrite(IN4, pwm2 <= 0);

  analogWrite(ENA, abs(pwm1));
  analogWrite(ENB, abs(pwm2));
}

void stopMotors() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}

// ---- Leitura do Ultrassônico ----
float readUltrasonic() {
  static unsigned long startTime = 0;
  static int state = 0;
  static float distance = -1;

  if (state == 0) {
    digitalWrite(TRIG_FRONT, LOW);
    startTime = micros();
    state = 1;
  } else if (state == 1 && micros() - startTime > 2) {
    digitalWrite(TRIG_FRONT, HIGH);
    startTime = micros();
    state = 2;
  } else if (state == 2 && micros() - startTime > 10) {
    digitalWrite(TRIG_FRONT, LOW);
    startTime = micros();
    state = 3;
  } else if (state == 3) {
    unsigned long duration = pulseIn(ECHO_FRONT, HIGH, 30000); // Timeout de 30ms
    if (duration > 0) {
      distance = duration * 0.034 / 2;
    } else {
      distance = -1; // Sem resposta
    }
    state = 0;
  }

  return distance;
}

// ---- Execução de Comandos ----
void executeCommand(char command) {
  if (command == 'F') {  // Andar para frente
    targetDistance = 50;
    executing = true;
    pulseCount1 = 0;
    pulseCount2 = 0;
    commandStartTime = millis();  // Registrar o tempo inicial
  }
  else if (command == 'E') { // Virar para esquerda
    targetDistance = 50;
    executing = true;
    pulseCount1 = 0;
    pulseCount2 = 0;
    commandStartTime = millis();  // Registrar o tempo inicial
  }
  else if (command == 'D') { // Virar para direita
    targetDistance = 50;
    executing = true;
    pulseCount1 = 0;
    pulseCount2 = 0;
    commandStartTime = millis();  // Registrar o tempo inicial
  }
  else if (command == 'W') {  // Esperar
    waiting = true;
    waitTimer = millis();
  }
}

void processCommands() {
  if (commandIndex < commandQueue.length() && !waiting) {
    char command = commandQueue[commandIndex];

    if (command == 'W') {
      // Verificar se há um número após o 'W'
      if (commandIndex + 1 < commandQueue.length() && isdigit(commandQueue[commandIndex + 1])) {
        int waitTime = (commandQueue[commandIndex + 1] - '0') * 1000; // Converter para milissegundos
        waitTimer = millis() + waitTime;
        waiting = true;
        commandIndex += 2; // Avançar para o próximo comando após 'W' e o número
      } else {
        Serial.println("⚠️ Comando 'W' inválido! Número esperado após 'W'.");
        commandIndex++;
      }
    } else {
      executeCommand(command);
      commandIndex++;
    }
  }

  if (waiting && millis() >= waitTimer) {
    waiting = false;
  }

  if (executing) {
    float distance1 = pulseCount1 * distancePerPulse;
    float distance2 = pulseCount2 * distancePerPulse;

    input1 = distance1;
    setpoint1 = targetDistance;
    pid1.Compute();
    
    input2 = distance2;
    setpoint2 = targetDistance;
    pid2.Compute();
    
    moveMotors(output1, output2);

    // Verificar se a distância alvo foi atingida
    if (distance1 >= targetDistance && distance2 >= targetDistance) {
      stopMotors();
      executing = false;
    }

    // Verificar se o tempo limite foi atingido
    if (millis() - commandStartTime > maxCommandTime) {
      Serial.println("⏱️ Tempo limite atingido! Parando o robô.");
      stopMotors();
      executing = false;
    }

    // Verificar se há um obstáculo na frente
    float distFront = readUltrasonic();
    if (distFront < 15 && distFront > 0) {
      Serial.println("🚫 Obstáculo na frente!");
      stopMotors();
      client.publish(topicoSensores, "obstacle_front");
      executing = false;
    }
  }
}

void setup() {
  Serial.begin(115200);
  connectWiFi();
  connectMQTT();

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(TRIG_FRONT, OUTPUT);
  pinMode(ECHO_FRONT, INPUT);

  pid1.SetMode(AUTOMATIC);
  pid2.SetMode(AUTOMATIC);

  attachInterrupt(digitalPinToInterrupt(ENCODER_A), encoderISR1, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A2), encoderISR2, RISING);
}

void loop() {
  if (!client.connected()) {
    connectMQTT();
  }
  client.loop();
  processCommands();
}