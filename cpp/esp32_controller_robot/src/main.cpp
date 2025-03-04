#include <Arduino.h>
#include <BluetoothSerial.h>
#include <PubSubClient.h>
#include <WiFi.h>

// Pinos do enco
#define ENCODER_A 4
#define ENCODER_B 5
#define ENCODER_A2 6
#define ENCODER_B2 7

// Pinos da ponte H
#define IN1 15
#define IN2 16
#define IN3 17
#define IN4 18


// Variáveis para o encoder
volatile long pulseCount = 0;
int pulsesPerRevolution = 11; // 11 pulsos por revolução
float rpm = 0;
unsigned long lastTime = 0;

// Parâmetros da roda
float wheelDiameter = 12;                                          // Diâmetro da roda em cm
float wheelCircumference = PI * wheelDiameter;                     // Circunferência em cm
float distancePerPulse = wheelCircumference / pulsesPerRevolution; // Distância por pulso em cm
float totalDistance = 0;                                           // Distância total percorrida em cm

//============================== Funções do programa ==========================================
// Função de interrupção para o encoder
void encoderISR()
{
  pulseCount++;
}

// Função para conectar-se a uma rede Wi-Fi
void connect(String SSID, String password)
{
  WiFi.begin(SSID.c_str(), password.c_str());
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(1000);
    Serial.println("Conectando à rede Wi-Fi...");
  }
  Serial.println("Conectado à rede Wi-Fi!");
}

void setup()
{
  connect("Gigo2.4G", "18253122Ro");
  // Configura os pinos do encoder como entrada
  pinMode(ENCODER_A, INPUT);
  pinMode(ENCODER_B, INPUT);

  // Configura os pinos da ponte H como saída
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  // Configura a interrupção para o encoder
  attachInterrupt(digitalPinToInterrupt(ENCODER_A), encoderISR, RISING);

  // Inicia a comunicação serial
  Serial.begin(9600);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
}

void loop()
{
  // Calcula a RPM
  unsigned long currentTime = millis();
  unsigned long timeElapsed = currentTime - lastTime;

  if (timeElapsed >= 1000)
  { // Atualiza a cada segundo
    rpm = (float)(pulseCount * 60) / (float)pulsesPerRevolution;
    totalDistance += pulseCount * distancePerPulse; // Atualiza a distância total
    pulseCount = 0;
    lastTime = currentTime;

    // Exibe a RPM e a distância no monitor serial
    Serial.print("RPM: ");
    Serial.print(rpm);
    Serial.print(" | Distância total: ");
    Serial.print(totalDistance);
    Serial.println(" cm");
  }

  // Exemplo de controle do motor
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

