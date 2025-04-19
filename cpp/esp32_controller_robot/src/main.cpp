#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <queue> // Biblioteca para usar filas (queues)

// Configurações de Wi-Fi
const char *WIFI_SSID = "Red";          // Substitua pelo seu SSID
const char *WIFI_PASSWORD = "12345678"; // Substitua pela sua senha

// Configurações de MQTT
const char *MQTT_SERVER = "192.168.146.103";        // Broker MQTT Local
const int MQTT_PORT = 1883;                         // Porta padrão do MQTT
const char *MQTT_CLIENT_ID = "admin";               // ID do cliente MQTT
const char *MQTT_TOPIC = "robo_gaveteiro/comandos"; // Tópico para receber comandos

// Pinos da Ponte H
#define IN1 6
#define IN2 7
#define IN3 15
#define IN4 16

// Pinos dos Encoders
#define ENCODER_A 4   // Pino do encoder do motor 1
#define ENCODER_B 5   // Pino do encoder do motor 1
#define ENCODER_A2 2  // Pino do encoder do motor 2
#define ENCODER_B2 42 // Pino do encoder do motor 2

// Variáveis dos Encoders
volatile long pulseCount1 = 0;                                     // Contador de pulsos do motor 1
volatile long pulseCount2 = 0;                                     // Contador de pulsos do motor 2
int pulsesPerRevolution = 2470;                                     // Pulsos por volta do encoder
float wheelDiameter = 12.0;                                        // Diâmetro da roda em cm
float wheelCircumference = PI * wheelDiameter;                     // Circunferência da roda
float distancePerPulse = wheelCircumference / pulsesPerRevolution; // Distância por pulso

// Variáveis de tempo
unsigned long lastTime1 = 0; // Último tempo de leitura do motor 1
unsigned long lastTime2 = 0; // Último tempo de leitura do motor 2

// Variáveis de distância
float totalDistance1 = 0; // Distância total percorrida pelo motor 1
float totalDistance2 = 0; // Distância total percorrida pelo motor 2

// Cliente Wi-Fi e MQTT
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Fila de mensagens
std::queue<String> filaMensagens;

// Funções de interrupção dos encoders
void encoderISR1()
{
    pulseCount1++; // Incrementa o contador de pulsos do motor 
}

// Função para conectar ao Wi-Fi
void connectToWiFi()
{
    Serial.println("Conectando ao Wi-Fi...");
    int n = WiFi.scanNetworks();
    Serial.println("Redes Wi-Fi disponíveis:");
    for (int i = 0; i < n; ++i)
    {
        Serial.print(i + 1);
        Serial.print(": ");
        Serial.print(WiFi.SSID(i));
        Serial.print(" (");
        Serial.print(WiFi.RSSI(i));
        Serial.println(" dBm)");
    }
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(1000);
        Serial.print(".");
    }

    Serial.println("\nConectado ao Wi-Fi!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
}

// Função para conectar ao servidor MQTT
void connectToMQTT()
{
    Serial.println("Conectando ao servidor MQTT...");
    while (!mqttClient.connected())
    {
        if (mqttClient.connect(MQTT_CLIENT_ID))
        {
            Serial.println("Conectado ao servidor MQTT!");
            mqttClient.subscribe(MQTT_TOPIC); // Inscreve-se no tópico
            Serial.print("Inscrito no tópico: ");
            Serial.println(MQTT_TOPIC);
        }
        else
        {
            Serial.print("Falha na conexão MQTT, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" Tentando novamente em 5 segundos...");
            delay(5000);
        }
    }
}
// Função para processar comandos dos motores
void controlarMotores(char comando)
{
    switch (comando)
    {
    case 'F': // Frente
        Serial.println("Movendo para frente...");
        digitalWrite(IN1, HIGH);
        digitalWrite(IN2, LOW);
        digitalWrite(IN3, HIGH);
        digitalWrite(IN4, LOW);
        break;
    case 'E': // Esquerda
        Serial.println("Girando para esquerda...");
        digitalWrite(IN1, LOW);
        digitalWrite(IN2, HIGH);
        digitalWrite(IN3, HIGH);
        digitalWrite(IN4, LOW);
        break;
    case 'D': // Direita
        Serial.println("Girando para direita...");
        digitalWrite(IN1, HIGH);
        digitalWrite(IN2, LOW);
        digitalWrite(IN3, LOW);
        digitalWrite(IN4, HIGH);
        break;
    case 'W': // Esperar
        Serial.println("Parando...");
        digitalWrite(IN1, LOW);
        digitalWrite(IN2, LOW);
        digitalWrite(IN3, LOW);
        digitalWrite(IN4, LOW);
        break;
    default:
        Serial.println("Comando desconhecido.");
        break;
    }
}

// Função de callback para mensagens MQTT
void mqttCallback(char *topic, byte *payload, unsigned int length)
{
    Serial.print("Mensagem recebida no tópico: ");
    Serial.println(topic);

    // Converte o payload para uma string
    char mensagem[length + 1];
    memcpy(mensagem, payload, length);
    mensagem[length] = '\0'; // Adiciona o terminador nulo
    Serial.print("Mensagem: ");
    Serial.println(mensagem);
  
    // Adiciona a mensagem à fila
    filaMensagens.push(String(mensagem));
    Serial.println("Mensagem adicionada à fila.");
}

// Função para processar a fila de mensagens
void processarFila()
{
    if (!filaMensagens.empty())
    {
        String mensagem = filaMensagens.front(); // Pega a primeira mensagem da fila
        filaMensagens.pop();                     // Remove a mensagem da fila
        Serial.print("Processando mensagem: ");
        Serial.println(mensagem);

        // Processa cada caractere da mensagem
        for (int i = 0; i < mensagem.length(); i++)
        {
            controlarMotores(mensagem[i]); // Executa o comando
            delay(500);                    // Pequeno delay entre comandos (ajuste conforme necessário)
        }
    }
}

// Função para calcular RPM e distância percorrida
void calcularRPM_Distancia()
{
    unsigned long currentTime = millis();

    // Cálculos para o motor 1
    if (currentTime - lastTime1 >= 1000)
    { // Atualiza a cada 1 segundo
        float rpm1 = (float)(pulseCount1 * 60) / (float)pulsesPerRevolution;
        totalDistance1 += pulseCount1 * distancePerPulse;
        pulseCount1 = 0; // Zera o contador de pulsos
        lastTime1 = currentTime;

        Serial.print("Motor 1 - RPM: ");
        Serial.print(rpm1);
        Serial.print(" | Distância total: ");
        Serial.print(totalDistance1);
        Serial.println(" cm");
    }

    // Cálculos para o motor 2
    if (currentTime - lastTime2 >= 1000)
    { // Atualiza a cada 1 segundo
        float rpm2 = (float)(pulseCount2 * 60) / (float)pulsesPerRevolution;
        totalDistance2 += pulseCount2 * distancePerPulse;
        pulseCount2 = 0; // Zera o contador de pulsos
        lastTime2 = currentTime;

        Serial.print("Motor 2 - RPM: ");
        Serial.print(rpm2);
        Serial.print(" | Distância total: ");
        Serial.print(totalDistance2);
        Serial.println(" cm");
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
}

void loop()
{
    // Verifica se o Wi-Fi está conectado
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("Wi-Fi desconectado. Tentando reconectar...");
        connectToWiFi();
    }

    // Mantém a conexão MQTT ativa
    mqttClient.loop();

    // Processa a fila de mensagens
    processarFila();

    // Calcula RPM e distância percorrida
    calcularRPM_Distancia();
}