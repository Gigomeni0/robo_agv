#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <queue>
#include <Adafruit_NeoPixel.h> // Biblioteca para controle do LED endereçável

// Configurações de rede
const char *WIFI_SSID = "SSID";
const char *WIFI_PASSWORD = "SUA_SENHA";
const char *MQTT_SERVER = "192.168.137.103";
const int MQTT_PORT = 1883;
const char *MQTT_CLIENT_ID = "admin";
const char *MQTT_TOPIC = "robo_gaveteiro/comandos";

// Configuração do NeoPixel
#define LED_PIN 48 // Pino onde o NeoPixel está conectado
#define NUM_LEDS 1 // Número de LEDs na fita (usamos apenas 1)
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
const float DISTANCIA_SEGURANCA = 20.0;                  // cm
const float DISTANCIA_EMERGENCIA = 10.0;                 // cm
const unsigned long INTERVALO_LEITURA_SENSORES = 200;    // ms
const unsigned long TEMPO_ESPERA_APOS_EMERGENCIA = 5000; // 5 segundos

// Variáveis dos sensores
unsigned long ultimaLeituraSensores = 0;
float distanciaPrioritaria = 0;
float distanciaSecundaria1 = 0;
float distanciaSecundaria2 = 0;
unsigned long tempoObstaculoSaiu = 0;

// Variáveis dos encoders
volatile long pulseCount1 = 0;
volatile long pulseCount2 = 0;
const int pulsesPerRevolution = 2740 * 2; // dobrar para canais A+B
float wheelDiameter = 12.0;
float wheelCircumference = PI * wheelDiameter;
float distancePerPulse = wheelCircumference / pulsesPerRevolution;

// Variáveis de controle
const long PULSOS_FRENTE_TRAS = 27000;
float trackWidthCm = 40.0; // cm - distância entre rodas, ajuste conforme seu robô
long PULSOS_CURVA = 0;     // será calculado no setup
bool emMovimento = false;
bool emergencia = false;
String comandoAtual = "";
unsigned long inicioMovimento = 0;
const unsigned long TIMEOUT_MOVIMENTO = 10000;
long pulsosRestantes1 = 0;
long pulsosRestantes2 = 0;

// Suporte ao comando MQTT de espera W{x}
bool esperandoPausa = false;
unsigned long fimPausa = 0;

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
void setLedColor(uint8_t r, uint8_t g, uint8_t b); // Nova função para controle do LED

// Interrupções dos encoders
void encoderISR1()
{
  if (emMovimento && !emergencia)
    pulseCount1++;
}

void encoderISR2()
{
  if (emMovimento && !emergencia)
    pulseCount2++;
}

// Função para controlar o LED
void setLedColor(uint8_t r, uint8_t g, uint8_t b)
{
  pixel.setPixelColor(0, pixel.Color(r, g, b));
  pixel.show();
}

// Função para ler sensor ultrassônico
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

// Função para verificar sensores
void verificarSensores()
{
  if (millis() - ultimaLeituraSensores >= INTERVALO_LEITURA_SENSORES)
  {
    ultimaLeituraSensores = millis();

    distanciaPrioritaria = lerSensorUltrassonico(TRIG_PRIORITARIO, ECHO_PRIORITARIO);

    if (emergencia)
    {
      if (distanciaPrioritaria > DISTANCIA_EMERGENCIA || distanciaPrioritaria <= 0)
      {
        if (tempoObstaculoSaiu == 0)
        {
          tempoObstaculoSaiu = millis();
          mqttClient.publish("robo/status", "Obstaculo removido. Aguardando 5s...");
        }
        else if (millis() - tempoObstaculoSaiu >= TEMPO_ESPERA_APOS_EMERGENCIA)
        {
          emergencia = false;
          tempoObstaculoSaiu = 0;
          retomarMovimento();
        }
      }
      else
      {
        tempoObstaculoSaiu = 0;
      }
    }
    else
    {
      if (distanciaPrioritaria <= DISTANCIA_EMERGENCIA && distanciaPrioritaria > 0)
      {
        tratarEmergencia();
        return;
      }
    }

    distanciaSecundaria1 = lerSensorUltrassonico(TRIG_SECUNDARIO_1, ECHO_SECUNDARIO_1);
    distanciaSecundaria2 = lerSensorUltrassonico(TRIG_SECUNDARIO_2, ECHO_SECUNDARIO_2);

    // Publica flag de obstáculo simples para GUI
    if (distanciaPrioritaria <= DISTANCIA_EMERGENCIA && distanciaPrioritaria > 0)
    {
      if (emMovimento)
        pararMotores();
      mqttClient.publish("robo_gaveteiro/status", "obstaculoFrente");
      return;
    }
    if (distanciaSecundaria1 <= DISTANCIA_SEGURANCA && distanciaSecundaria1 > 0)
    {
      if (emMovimento)
        pararMotores();
      mqttClient.publish("robo_gaveteiro/status", "obstaculoDireita");
      return;
    }
    if (distanciaSecundaria2 <= DISTANCIA_SEGURANCA && distanciaSecundaria2 > 0)
    {
      if (emMovimento)
        pararMotores();
      mqttClient.publish("robo_gaveteiro/status", "obstaculoEsquerda");
      return;
    }
  }
}

// Tratar situação de emergência
void tratarEmergencia()
{
  if (emMovimento)
  {
    long pulsosAlvo = (comandoAtual == "F" || comandoAtual == "T") ? PULSOS_FRENTE_TRAS : PULSOS_CURVA;
    pulsosRestantes1 = pulsosAlvo - pulseCount1;
    pulsosRestantes2 = pulsosAlvo - pulseCount2;

    pararMotores();
    mqttClient.publish("robo/status", "EMERGENCIA: Obstaculo prioritario detectado!");
    setLedColor(255, 0, 0); // LED vermelho durante emergência
  }
  emergencia = true;
}

// Retomar movimento após emergência
void retomarMovimento()
{
  if (pulsosRestantes1 <= 0 || pulsosRestantes2 <= 0)
  {
    return;
  }

  Serial.println("Retomando movimento interrompido");
  emMovimento = true;
  pulseCount1 = 0;
  pulseCount2 = 0;
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

  setLedColor(0, 255, 0); // LED verde ao retomar movimento
}

// Iniciar movimento
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
  pulseCount1 = 0;
  pulseCount2 = 0;
  inicioMovimento = millis();
  pulsosRestantes1 = 0;
  pulsosRestantes2 = 0;

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

  setLedColor(0, 255, 0); // LED verde ao iniciar movimento
}

// Parar motores
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

  String status = "Concluido:" + comandoAtual + ",Pulsos:" + String(pulseCount1) + "," + String(pulseCount2);
  mqttClient.publish("robo/status", status.c_str());
  // Envia contagem de pulsos para calibragem na GUI
  char plotBuf[32];
  snprintf(plotBuf, sizeof(plotBuf), "%ld,%ld", pulseCount1, pulseCount2);
  mqttClient.publish("robo_gaveteiro/plotter", plotBuf);
}

// Controlar motores
void controlarMotores(String comando)
{
  comando.toUpperCase();

  if (comando == "P")
  {
    pararMotores();
    return;
  }

  if (emMovimento || emergencia)
  {
    Serial.println(emergencia ? "Emergencia ativa - Comando ignorado" : "Aguardando movimento atual terminar");
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

// Verificar movimento
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
    return;
  }

  long pulsosAlvo = (comandoAtual == "F" || comandoAtual == "T") ? PULSOS_FRENTE_TRAS : PULSOS_CURVA;

  if (pulsosRestantes1 > 0 && pulsosRestantes2 > 0)
  {
    pulsosAlvo = max(pulsosRestantes1, pulsosRestantes2);
  }

  if ((pulseCount1 >= pulsosAlvo) && (pulseCount2 >= pulsosAlvo))
  {
    pararMotores();
    pulsosRestantes1 = 0;
    pulsosRestantes2 = 0;
  }
}

// Processar fila de mensagens
void processarFila()
{
  if (emMovimento || filaMensagens.empty())
    return;

  String mensagem = filaMensagens.front();
  filaMensagens.pop();

  // comando de pausa via MQTT
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
  else
  {
    Serial.println("Comando inválido descartado: " + mensagem);
  }
}

// Calcular RPM e distância
void calcularRPM_Distancia()
{
  unsigned long currentTime = millis();
  unsigned long elapsedTime1 = currentTime - lastTime1;
  unsigned long elapsedTime2 = currentTime - lastTime2;

  if (elapsedTime1 >= 1000)
  {
    float rpm1 = (pulseCount1 * 60.0) / pulsesPerRevolution;
    float distance1 = pulseCount1 * distancePerPulse;
    totalDistance1 += distance1;

    Serial.print("Motor 1 - RPM: ");
    Serial.print(rpm1);
    Serial.print(", Distância: ");
    Serial.print(totalDistance1);
    Serial.println(" cm");

    pulseCount1 = 0;
    lastTime1 = currentTime;
  }

  if (elapsedTime2 >= 1000)
  {
    float rpm2 = (pulseCount2 * 60.0) / pulsesPerRevolution;
    float distance2 = pulseCount2 * distancePerPulse;
    totalDistance2 += distance2;

    Serial.print("Motor 2 - RPM: ");
    Serial.print(rpm2);
    Serial.print(", Distância: ");
    Serial.print(totalDistance2);
    Serial.println(" cm");

    pulseCount2 = 0;
    lastTime2 = currentTime;
  }
}

// Conectar ao Wi-Fi
void connectToWiFi()
{
  Serial.print("Conectando ao Wi-Fi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
    setLedColor(255, 165, 0); // LED laranja durante tentativa de conexão WiFi
  }

  Serial.println("\nConectado ao Wi-Fi");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
  setLedColor(0, 0, 255); // LED azul quando WiFi conectado (antes do MQTT)
}

// Conectar ao MQTT
void connectToMQTT()
{
  while (!mqttClient.connected())
  {
    Serial.print("Conectando ao MQTT...");
    setLedColor(255, 165, 0); // LED laranja durante tentativa de conexão MQTT

    if (mqttClient.connect(MQTT_CLIENT_ID))
    {
      Serial.println("Conectado");
      mqttClient.subscribe(MQTT_TOPIC);
      setLedColor(0, 255, 0); // LED verde quando MQTT conectado com sucesso
    }
    else
    {
      Serial.print("Falha, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Tentando novamente em 5 segundos");
      setLedColor(255, 0, 0); // LED vermelho quando falha na conexão MQTT
      delay(5000);
    }
  }
}

// Callback MQTT
void mqttCallback(char *topic, byte *payload, unsigned int length)
{
  Serial.print("Mensagem recebida no tópico: ");
  Serial.println(topic);

  char mensagem[length + 1];
  memcpy(mensagem, payload, length);
  mensagem[length] = '\0';
  Serial.print("Mensagem: ");
  Serial.println(mensagem);

  filaMensagens.push(String(mensagem));
}

// Setup
void setup()
{
  Serial.begin(115200);

  // Inicializa o NeoPixel
  pixel.begin();
  pixel.setBrightness(50);  // Ajuste o brilho conforme necessário (0-255)
  setLedColor(255, 0, 255); // LED roxo durante inicialização

  // Configura pinos dos motores
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Configura pinos dos encoders
  pinMode(ENCODER_A, INPUT);
  pinMode(ENCODER_B, INPUT);
  pinMode(ENCODER_A2, INPUT);
  pinMode(ENCODER_B2, INPUT);

  // Configura pinos dos sensores
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

  // Conecta ao Wi-Fi e MQTT
  connectToWiFi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  connectToMQTT();
  mqttClient.subscribe(MQTT_TOPIC);

  // Calcula quantidade de pulsos para curva de 90 graus
  {
    float anguloDeg = 90.0;
    float arcoCm = PI * trackWidthCm * (anguloDeg / 360.0);
    PULSOS_CURVA = (long)(arcoCm / distancePerPulse);
    Serial.print("PULSOS_CURVA calculado: ");
    Serial.println(PULSOS_CURVA);
  }

  Serial.println("Sistema inicializado com LED de status e retomada automatica");
  setLedColor(0, 255, 0); // LED verde quando tudo inicializado com sucesso
}

// Loop principal
void loop()
{
  // Mantém conexões
  if (WiFi.status() != WL_CONNECTED)
  {
    setLedColor(255, 0, 0); // LED vermelho se WiFi desconectado
    connectToWiFi();
  }

  if (!mqttClient.connected())
  {
    setLedColor(255, 0, 0); // LED vermelho se MQTT desconectado
    connectToMQTT();
  }

  mqttClient.loop();

  // --- trata pausa via comando W{x} ---
  if (esperandoPausa)
  {
    if (millis() >= fimPausa)
    {
      esperandoPausa = false;
      Serial.println("Pausa concluída");
    }
    else
    {
      // Durante pausa, só atualiza sensores e MQTT
      verificarSensores();
      return;
    }
  }

  // Verifica sensores
  verificarSensores();

  // Processamento normal
  if (!emergencia)
  {
    verificarMovimento();
    processarFila();
    calcularRPM_Distancia();
  }

  // Debug
  static unsigned long lastDebug = 0;
  if (millis() - lastDebug > 500)
  {
    lastDebug = millis();
    if (emMovimento)
    {
      Serial.print("Progresso: ");
      Serial.print(pulseCount1);
      Serial.print("/");
      Serial.print((comandoAtual == "F" || comandoAtual == "T") ? PULSOS_FRENTE_TRAS : PULSOS_CURVA);
      Serial.print(" | ");
      Serial.println(pulseCount2);
    }

    Serial.print("Distancias: Prior=");
    Serial.print(distanciaPrioritaria);
    Serial.print("cm, Sec1=");
    Serial.print(distanciaSecundaria1);
    Serial.print("cm, Sec2=");
    Serial.print(distanciaSecundaria2);
    Serial.println("cm");

    if (emergencia)
    {
      Serial.println("EMERGENCIA ATIVA - Aguardando obstaculo sair");
    }
  }
}