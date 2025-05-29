// File: src/main.cpp
//===============================================================================================================
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <queue>

// Configurações (mantidas as mesmas)
const char *WIFI_SSID = "SSID";
const char *WIFI_PASSWORD = "SUA_SENHA";
const char *MQTT_SERVER = "192.168.121.103";
const int MQTT_PORT = 1883;
const char *MQTT_CLIENT_ID = "admin";
const char *MQTT_TOPIC = "robo_gaveteiro/comandos";

// Pinos (mantidos os mesmos)
#define IN1 6
#define IN2 7
#define IN3 15
#define IN4 16
#define ENCODER_A 1
#define ENCODER_B 2
#define ENCODER_A2 47
#define ENCODER_B2 21

// Variáveis dos Encoders (mantidas)
volatile long pulseCount1 = 0;
volatile long pulseCount2 = 0;
int pulsesPerRevolution = 2740;
float wheelDiameter = 12.0;
float wheelCircumference = PI * wheelDiameter;
float distancePerPulse = wheelCircumference / pulsesPerRevolution;

// --- NOVAS VARIÁVEIS PARA CONTROLE POR PULSOS ---
const long PULSOS_FRENTE_TRAS = 27000; // Pulsos para movimento linear
const long PULSOS_CURVA = 1000;         // Pulsos para curvas
bool emMovimento = false;
String comandoAtual = "";
unsigned long inicioMovimento = 0;
const unsigned long TIMEOUT_MOVIMENTO = 10000; // 10 segundos

// Variáveis existentes (mantidas)
unsigned long lastTime1 = 0, lastTime2 = 0;
float totalDistance1 = 0, totalDistance2 = 0;
WiFiClient espClient;
PubSubClient mqttClient(espClient);
std::queue<String> filaMensagens;

// Interrupções dos encoders (mantidas)
void encoderISR1()
{
  if (emMovimento)
    pulseCount1++;
}
void encoderISR2()
{
  if (emMovimento)
    pulseCount2++;
}

// --- FUNÇÕES ADICIONADAS/MODIFICADAS ---
void iniciarMovimento(String comando)
{
  comando.toUpperCase();
  comandoAtual = comando;
  emMovimento = true;
  pulseCount1 = 0;
  pulseCount2 = 0;
  inicioMovimento = millis();

  if (comando == "F")
  {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    Serial.println("INICIANDO: Frente (27000 pulsos)");
  }
  else if (comando == "T")
  {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    Serial.println("INICIANDO: Trás (27000 pulsos)");
  }
  else if (comando == "D")
  {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    Serial.println("INICIANDO: Direita (685 pulsos)");
  }
  else if (comando == "E")
  {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    Serial.println("INICIANDO: Esquerda (685 pulsos)");
  }
}

void pararMotores()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  emMovimento = false;

  Serial.print("FINALIZADO: ");
  Serial.print(comandoAtual);
  Serial.print(" | Pulsos: ");
  Serial.print(pulseCount1);
  Serial.print(", ");
  Serial.println(pulseCount2);

  // Publica status via MQTT
  String status = "Concluido:" + comandoAtual + ",Pulsos:" + String(pulseCount1) + "," + String(pulseCount2);
  mqttClient.publish("robo/status", status.c_str());
}

void verificarMovimento()
{
  if (!emMovimento)
    return;

  // Verifica timeout
  if (millis() - inicioMovimento > TIMEOUT_MOVIMENTO)
  {
    Serial.println("ERRO: Timeout de movimento");
    pararMotores();
    return;
  }

  // Verifica pulsos conforme o comando
  long pulsosAlvo = (comandoAtual == "F" || comandoAtual == "T") ? PULSOS_FRENTE_TRAS : PULSOS_CURVA;

  if ((comandoAtual == "F" || comandoAtual == "D") &&
      (pulseCount1 >= pulsosAlvo && pulseCount2 >= pulsosAlvo))
  {
    pararMotores();
  }
  else if ((comandoAtual == "T" || comandoAtual == "E") &&
           (pulseCount1 >= pulsosAlvo && pulseCount2 >= pulsosAlvo))
  {
    pararMotores();
  }
}

// Funções existentes MODIFICADAS
void controlarMotores(String comando)
{
  comando.toUpperCase();

  if (comando == "P")
  {
    pararMotores();
    return;
  }

  if (emMovimento)
  {
    Serial.println("Aguardando movimento atual terminar");
    return;
  }

  if (comando == "F" || comando == "T" || comando == "D" || comando == "E")
  {
    iniciarMovimento(comando);
  }
  else
  {
    Serial.println("Comando inválido: " + comando);
  }
}

void processarFila()
{
  if (emMovimento || filaMensagens.empty())
    return;

  String mensagem = filaMensagens.front();
  filaMensagens.pop();
  controlarMotores(mensagem);
}

// Funções existentes MANTIDAS SEM ALTERAÇÃO

// Conecta ao Wi-Fi
void connectToWiFi()
{
  Serial.print("Conectando ao Wi-Fi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConectado ao Wi-Fi");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

// Conecta ao MQTT
void connectToMQTT()
{
  while (!mqttClient.connected())
  {
    Serial.print("Conectando ao MQTT...");

    if (mqttClient.connect(MQTT_CLIENT_ID))
    {
      Serial.println("Conectado");
      mqttClient.subscribe(MQTT_TOPIC);
    }
    else
    {
      Serial.print("Falha, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Tentando novamente em 5 segundos");
      delay(5000);
    }
  }
}

// Função de callback para mensagens MQTT
void mqttCallback(char *topic, byte *payload, unsigned int length)
{
  Serial.print("Mensagem recebida no tópico: ");
  Serial.println(topic);

  char mensagem[length + 1];
  memcpy(mensagem, payload, length);
  mensagem[length] = '\0';
  Serial.print("Mensagem: ");
  Serial.println(mensagem);

  // Adiciona mensagem à fila
  filaMensagens.push(String(mensagem));
}

// Calcula RPM e distância percorrida
void calcularRPM_Distancia()
{
  unsigned long currentTime = millis();
  unsigned long elapsedTime1 = currentTime - lastTime1;
  unsigned long elapsedTime2 = currentTime - lastTime2;

  if (elapsedTime1 >= 1000)
  { // A cada segundo
    // Calcula RPM para o motor 1
    float rpm1 = (pulseCount1 * 60.0) / pulsesPerRevolution;

    // Calcula distância percorrida pelo motor 1
    float distance1 = pulseCount1 * distancePerPulse;
    totalDistance1 += distance1;

    Serial.print("Motor 1 - RPM: ");
    Serial.print(rpm1);
    Serial.print(", Distância: ");
    Serial.print(totalDistance1);
    Serial.println(" cm");

    // Reseta contadores e tempo
    pulseCount1 = 0;
    lastTime1 = currentTime;
  }

  if (elapsedTime2 >= 1000)
  { // A cada segundo
    // Calcula RPM para o motor 2
    float rpm2 = (pulseCount2 * 60.0) / pulsesPerRevolution;

    // Calcula distância percorrida pelo motor 2
    float distance2 = pulseCount2 * distancePerPulse;
    totalDistance2 += distance2;

    Serial.print("Motor 2 - RPM: ");
    Serial.print(rpm2);
    Serial.print(", Distância: ");
    Serial.print(totalDistance2);
    Serial.println(" cm");

    // Reseta contadores e tempo
    pulseCount2 = 0;
    lastTime2 = currentTime;
  }
}

void setup()
{
  Serial.begin(115200);

  // Configura os pinos da Ponte H
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Configura os pinos dos encoders
  pinMode(ENCODER_A, INPUT);
  pinMode(ENCODER_B, INPUT);
  pinMode(ENCODER_A2, INPUT);
  pinMode(ENCODER_B2, INPUT);

  // Configura as interrupções dos encoders
  attachInterrupt(digitalPinToInterrupt(ENCODER_A), encoderISR1, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A2), encoderISR2, RISING);

  // Conecta ao Wi-Fi
  connectToWiFi();

  // Configura o servidor MQTT e a função de callback
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  // Conecta ao servidor MQTT
  connectToMQTT();

  // Inscreve no tópico
  mqttClient.subscribe(MQTT_TOPIC);
}

// Loop principal atualizado
void loop()
{
  // Conexões (mantidas)
  if (WiFi.status() != WL_CONNECTED)
    connectToWiFi();
  if (!mqttClient.connected())
    connectToMQTT();
  mqttClient.loop();

  // Processamento (atualizado)
  verificarMovimento();
  processarFila();
  calcularRPM_Distancia();

  // Debug durante movimento
  static unsigned long lastDebug = 0;
  if (emMovimento && millis() - lastDebug > 500)
  {
    lastDebug = millis();
    Serial.print("Progresso: ");
    Serial.print(pulseCount1);
    Serial.print("/");
    Serial.print((comandoAtual == "F" || comandoAtual == "T") ? PULSOS_FRENTE_TRAS : PULSOS_CURVA);
    Serial.print(" | ");
    Serial.println(pulseCount2);
  }
}