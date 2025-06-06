#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <queue>
#include <Adafruit_NeoPixel.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

// Configurações de rede
const char *WIFI_SSID = "SSID";
const char *WIFI_PASSWORD = "SUA_SENHA";
const char *MQTT_SERVER = "192.168.24.103";
const int MQTT_PORT = 1883;
const char *MQTT_CLIENT_ID = "admin";
const char *MQTT_TOPIC = "robo_gaveteiro/comandos";
const char *MQTT_TOPIC_PLOTTER = "robo_gaveteiro/plotter";
const char *MQTT_TOPIC_STATUS = "robo_gaveteiro/status";

// Configuração do NeoPixel
#define LED_PIN 48
#define NUM_LEDS 1
Adafruit_NeoPixel pixel(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Pinos dos motores e encoders
#define IN1 6
#define IN2 7
#define IN3 15
#define IN4 16
#define ENCODER_A 1
#define ENCODER_B 2
#define ENCODER_A2 47
#define ENCODER_B2 21

// Pinos dos sensores ultrassônicos
#define TRIG_PRIORITARIO 38
#define ECHO_PRIORITARIO 37
#define TRIG_SECUNDARIO_1 40
#define ECHO_SECUNDARIO_1 39
#define TRIG_SECUNDARIO_2 42
#define ECHO_SECUNDARIO_2 41

// Parâmetros dos sensores
const float DISTANCIA_SEGURANCA = 20.0;
const float DISTANCIA_EMERGENCIA = 10.0;
const unsigned long INTERVALO_LEITURA_SENSORES = 200;
const unsigned long TEMPO_ESPERA_APOS_EMERGENCIA = 5000;

// Variáveis compartilhadas entre núcleos
volatile long pulseCount1 = 0;
volatile long pulseCount2 = 0;
float distanciaPrioritaria = 0;
float distanciaSecundaria1 = 0;
float distanciaSecundaria2 = 0;
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

// Variáveis dos encoders
const int pulsesPerRevolution = 2740 * 2;
float wheelDiameter = 12.0;
float wheelCircumference = PI * wheelDiameter;
float distancePerPulse = wheelCircumference / pulsesPerRevolution;

// Variáveis de controle
const long PULSOS_FRENTE_TRAS = 1000;
float trackWidthCm = 26.0;
long PULSOS_CURVA = 800; // valor fixo de pulsos para curva (90°)
bool emMovimento = false;
bool emergencia = false;
String comandoAtual = "";
unsigned long inicioMovimento = 0;
const unsigned long TIMEOUT_MOVIMENTO = 10000;
long pulsosRestantes1 = 0;
long pulsosRestantes2 = 0;
bool esperandoPausa = false;
unsigned long fimPausa = 0;
unsigned long tempoObstaculoSaiu = 0;

// Variáveis do sistema
unsigned long lastTime1 = 0, lastTime2 = 0;
float totalDistance1 = 0, totalDistance2 = 0;
WiFiClient espClient;
PubSubClient mqttClient(espClient);
std::queue<String> filaMensagens;

// Protótipos de funções
void connectToWiFi();
void connectToMQTT();
void mqttCallback(char *topic, byte *payload, unsigned int length);
float lerSensorUltrassonico(int trigPin, int echoPin);
void verificarSensores();
void tratarEmergencia();
void retomarMovimento();
void iniciarMovimento(String comando);
void pararMotores();
void controlarMotores(String comando);
void verificarMovimento();
void processarFila();
void calcularRPM_Distancia();
void setLedColor(uint8_t r, uint8_t g, uint8_t b);
void taskSensoresEncoders(void *pvParameters);
void IRAM_ATTR encoderISR1();
void IRAM_ATTR encoderISR2();
void publicarDadosPlotter();
void verificarObstaculosGUI();

void setLedColor(uint8_t r, uint8_t g, uint8_t b)
{
  pixel.setPixelColor(0, pixel.Color(r, g, b));
  pixel.show();
}

float lerSensorUltrassonico(int trigPin, int echoPin)
{
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);
  return duration * 0.034 / 2;
}

void tratarEmergencia()
{
  if (emMovimento)
  {
    long pulsosAlvo = (comandoAtual == "F" || comandoAtual == "T") ? PULSOS_FRENTE_TRAS : PULSOS_CURVA;
    portENTER_CRITICAL(&mux);
    pulsosRestantes1 = pulsosAlvo - pulseCount1;
    pulsosRestantes2 = pulsosAlvo - pulseCount2;
    portEXIT_CRITICAL(&mux);

    pararMotores();
    mqttClient.publish(MQTT_TOPIC_STATUS, "EMERGENCIA: Obstaculo prioritario detectado!");
    setLedColor(255, 0, 0);
  }
  emergencia = true;
}

void retomarMovimento()
{
  portENTER_CRITICAL(&mux);
  long pr1 = pulsosRestantes1;
  long pr2 = pulsosRestantes2;
  portEXIT_CRITICAL(&mux);

  if (pr1 <= 0 || pr2 <= 0)
    return;

  Serial.println("Retomando movimento interrompido");
  emMovimento = true;
  portENTER_CRITICAL(&mux);
  pulseCount1 = 0;
  pulseCount2 = 0;
  portEXIT_CRITICAL(&mux);
  inicioMovimento = millis();

  if (comandoAtual == "F")
  {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  }
  else if (comandoAtual == "D")
  {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }
  else if (comandoAtual == "E")
  {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  }

  setLedColor(0, 255, 0);
}

void iniciarMovimento(String comando)
{
  if (emergencia)
  {
    Serial.println("Movimento bloqueado - Emergencia ativa");
    return;
  }

  comando.toUpperCase();
  comandoAtual = comando;
  emMovimento = true;
  portENTER_CRITICAL(&mux);
  pulseCount1 = 0;
  pulseCount2 = 0;
  portEXIT_CRITICAL(&mux);
  inicioMovimento = millis();
  pulsosRestantes1 = 0;
  pulsosRestantes2 = 0;

  if (comando == "F")
  {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    Serial.println("INICIANDO: Frente");
  }
  else if (comando == "T")
  {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    Serial.println("INICIANDO: Trás");
  }
  else if (comando == "D")
  {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    Serial.println("INICIANDO: Direita");
  }
  else if (comando == "E")
  {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    Serial.println("INICIANDO: Esquerda");
  }

  setLedColor(0, 255, 0);
}

void pararMotores()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  emMovimento = false;

  portENTER_CRITICAL(&mux);
  long pc1 = pulseCount1;
  long pc2 = pulseCount2;
  portEXIT_CRITICAL(&mux);

  Serial.print("FINALIZADO: ");
  Serial.print(comandoAtual);
  Serial.print(" | Pulsos: ");
  Serial.print(pc1);
  Serial.print(", ");
  Serial.println(pc2);

  String status = "Concluido:" + comandoAtual + ",Pulsos:" + String(pc1) + "," + String(pc2);
  mqttClient.publish(MQTT_TOPIC_STATUS, status.c_str());
  publicarDadosPlotter();
}

void publicarDadosPlotter()
{
  portENTER_CRITICAL(&mux);
  long pc1 = pulseCount1;
  long pc2 = pulseCount2;
  portEXIT_CRITICAL(&mux);

  char plotBuf[32];
  snprintf(plotBuf, sizeof(plotBuf), "%ld,%ld", pc1, pc2);
  mqttClient.publish(MQTT_TOPIC_PLOTTER, plotBuf);
}

void verificarObstaculosGUI()
{
  portENTER_CRITICAL(&mux);
  float dp = distanciaPrioritaria;
  float ds1 = distanciaSecundaria1;
  float ds2 = distanciaSecundaria2;
  portEXIT_CRITICAL(&mux);

  if (dp <= DISTANCIA_EMERGENCIA && dp > 0)
  {
    mqttClient.publish(MQTT_TOPIC_STATUS, "obstaculoFrente");
  }
  if (ds1 <= DISTANCIA_SEGURANCA && ds1 > 0)
  {
    mqttClient.publish(MQTT_TOPIC_STATUS, "obstaculoDireita");
  }
  if (ds2 <= DISTANCIA_SEGURANCA && ds2 > 0)
  {
    mqttClient.publish(MQTT_TOPIC_STATUS, "obstaculoEsquerda");
  }
}

void controlarMotores(String comando)
{
  comando.toUpperCase();

  if (comando == "P")
  {
    pararMotores();
    return;
  }

  if (emMovimento || emergencia)
    return;

  if (comando == "F" || comando == "T" || comando == "D" || comando == "E")
  {
    iniciarMovimento(comando);
  }
}

void verificarMovimento()
{
  if (!emMovimento)
    return;

  if (millis() - inicioMovimento > TIMEOUT_MOVIMENTO)
  {
    Serial.println("ERRO: Timeout de movimento");
    pararMotores();
    pulsosRestantes1 = 0;
    pulsosRestantes2 = 0;
    for (int i = 0; i < 3; i++)
    {
      setLedColor(128, 0, 128);
      vTaskDelay(pdMS_TO_TICKS(200));
      setLedColor(0, 0, 0);
      vTaskDelay(pdMS_TO_TICKS(200));
    }
    return;
  }

  long pulsosAlvo = (comandoAtual == "F" || comandoAtual == "T") ? PULSOS_FRENTE_TRAS : PULSOS_CURVA;

  portENTER_CRITICAL(&mux);
  long pc1 = pulseCount1;
  long pc2 = pulseCount2;
  portEXIT_CRITICAL(&mux);

  if ((pc1 >= pulsosAlvo) && (pc2 >= pulsosAlvo))
  {
    pararMotores();
    pulsosRestantes1 = 0;
    pulsosRestantes2 = 0;
  }
}

void processarFila()
{
  if (emMovimento || filaMensagens.empty())
    return;

  String mensagem = filaMensagens.front();
  filaMensagens.pop();

  if (mensagem.startsWith("W"))
  {
    int secs = mensagem.substring(1).toInt();
    fimPausa = millis() + (unsigned long)secs * 1000UL;
    esperandoPausa = true;
    Serial.printf("Iniciando pausa de %d s\n", secs);
    return;
  }

  if (mensagem == "F" || mensagem == "T" || mensagem == "D" || mensagem == "E" || mensagem == "P")
  {
    controlarMotores(mensagem);
  }
}

void calcularRPM_Distancia()
{
  unsigned long currentTime = millis();
  static unsigned long lastTime1 = 0, lastTime2 = 0;

  portENTER_CRITICAL(&mux);
  long pc1 = pulseCount1;
  long pc2 = pulseCount2;
  portEXIT_CRITICAL(&mux);

  if (currentTime - lastTime1 >= 1000)
  {
    float rpm1 = (pc1 * 60.0) / pulsesPerRevolution;
    float distance1 = pc1 * distancePerPulse;
    totalDistance1 += distance1;
    lastTime1 = currentTime;
    portENTER_CRITICAL(&mux);
    pulseCount1 = 0;
    portEXIT_CRITICAL(&mux);

    Serial.print("Motor 1 - RPM: ");
    Serial.print(rpm1);
    Serial.print(", Distância: ");
    Serial.print(totalDistance1);
    Serial.println(" cm");
  }

  if (currentTime - lastTime2 >= 1000)
  {
    float rpm2 = (pc2 * 60.0) / pulsesPerRevolution;
    float distance2 = pc2 * distancePerPulse;
    totalDistance2 += distance2;
    lastTime2 = currentTime;
    portENTER_CRITICAL(&mux);
    pulseCount2 = 0;
    portEXIT_CRITICAL(&mux);

    Serial.print("Motor 2 - RPM: ");
    Serial.print(rpm2);
    Serial.print(", Distância: ");
    Serial.print(totalDistance2);
    Serial.println(" cm");
  }
}

void connectToWiFi()
{
  Serial.print("Conectando ao Wi-Fi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  setLedColor(255, 165, 0);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConectado ao Wi-Fi");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
  setLedColor(0, 0, 255);
}

void connectToMQTT()
{
  while (!mqttClient.connected())
  {
    Serial.print("Conectando ao MQTT...");
    setLedColor(255, 165, 0);

    if (mqttClient.connect(MQTT_CLIENT_ID))
    {
      Serial.println("Conectado");
      mqttClient.subscribe(MQTT_TOPIC);
      setLedColor(0, 255, 0);
    }
    else
    {
      Serial.print("Falha, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Tentando novamente em 5 segundos");
      setLedColor(255, 0, 0);
      delay(5000);
    }
  }
}

void mqttCallback(char *topic, byte *payload, unsigned int length)
{
  char mensagem[length + 1];
  memcpy(mensagem, payload, length);
  mensagem[length] = '\0';
  filaMensagens.push(String(mensagem));
}

void IRAM_ATTR encoderISR1()
{
  if (emMovimento && !emergencia)
  {
    portENTER_CRITICAL_ISR(&mux);
    pulseCount1++;
    portEXIT_CRITICAL_ISR(&mux);
  }
}

void IRAM_ATTR encoderISR2()
{
  if (emMovimento && !emergencia)
  {
    portENTER_CRITICAL_ISR(&mux);
    pulseCount2++;
    portEXIT_CRITICAL_ISR(&mux);
  }
}

void taskSensoresEncoders(void *pvParameters)
{
  (void)pvParameters;
  const TickType_t xDelay = pdMS_TO_TICKS(10);
  unsigned long lastSensorRead = 0;

  for (;;)
  {
    unsigned long now = millis();

    // Leitura dos sensores
    if (now - lastSensorRead >= INTERVALO_LEITURA_SENSORES)
    {
      lastSensorRead = now;

      portENTER_CRITICAL(&mux);
      distanciaPrioritaria = lerSensorUltrassonico(TRIG_PRIORITARIO, ECHO_PRIORITARIO);
      distanciaSecundaria1 = lerSensorUltrassonico(TRIG_SECUNDARIO_1, ECHO_SECUNDARIO_1);
      distanciaSecundaria2 = lerSensorUltrassonico(TRIG_SECUNDARIO_2, ECHO_SECUNDARIO_2);
      portEXIT_CRITICAL(&mux);

      // Verificação de emergência
      if (distanciaPrioritaria <= DISTANCIA_EMERGENCIA && distanciaPrioritaria > 0)
      {
        tratarEmergencia();
      }

      // Atualização GUI
      verificarObstaculosGUI();

      // Publicar distância do sensor para plotagem na GUI
      {
        char distBuf[16];
        snprintf(distBuf, sizeof(distBuf), "%.2f", distanciaPrioritaria);
        mqttClient.publish(MQTT_TOPIC_PLOTTER, distBuf);
        // também enviar via status com prefixo
        char statusBuf[24];
        snprintf(statusBuf, sizeof(statusBuf), "dist:%.2f", distanciaPrioritaria);
        mqttClient.publish(MQTT_TOPIC_STATUS, statusBuf);
      }
    }

    // Cálculos dos encoders
    calcularRPM_Distancia();

    vTaskDelay(xDelay);
  }
}

void setup()
{
  Serial.begin(115200);

  // Configura pinos
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  pinMode(TRIG_PRIORITARIO, OUTPUT);
  pinMode(ECHO_PRIORITARIO, INPUT);
  pinMode(TRIG_SECUNDARIO_1, OUTPUT);
  pinMode(ECHO_SECUNDARIO_1, INPUT);
  pinMode(TRIG_SECUNDARIO_2, OUTPUT);
  pinMode(ECHO_SECUNDARIO_2, INPUT);

  // Configura interrupções
  attachInterrupt(digitalPinToInterrupt(ENCODER_A), encoderISR1, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_B), encoderISR1, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A2), encoderISR2, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_B2), encoderISR2, RISING);

  // Inicializa NeoPixel
  pixel.begin();
  pixel.setBrightness(50);
  setLedColor(255, 0, 255);

  // Cria tarefa no Core 1
  xTaskCreatePinnedToCore(
      taskSensoresEncoders,
      "SensoresEncoders",
      4096,
      NULL,
      1,
      NULL,
      1);

  // Conecta à rede
  connectToWiFi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  connectToMQTT();

  Serial.println("Sistema inicializado com todas as funcionalidades");
  setLedColor(0, 255, 0);
}

void loop()
{
  // Mantém conexões
  if (WiFi.status() != WL_CONNECTED)
  {
    connectToWiFi();
  }

  if (!mqttClient.connected())
  {
    connectToMQTT();
  }

  mqttClient.loop();

  // Processa comandos
  if (!emergencia && !esperandoPausa)
  {
    processarFila();
    verificarMovimento();
  }

  // Trata pausa
  if (esperandoPausa && millis() >= fimPausa)
  {
    esperandoPausa = false;
    Serial.println("Pausa concluída");
  }
}