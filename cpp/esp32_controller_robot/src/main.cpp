#include <Arduino.h>

// Pinos do enco
#define ENCODER_A 2
#define ENCODER_B 3

// Pinos da ponte H
#define IN1 4
#define IN2 5

// Variáveis para o encoder
volatile long pulseCount = 0;
int pulsesPerRevolution = 11; // 11 pulsos por revolução
float rpm = 0;
unsigned long lastTime = 0;

// Parâmetros da roda
float wheelDiameter = 6.0; // Diâmetro da roda em cm
float wheelCircumference = PI * wheelDiameter; // Circunferência em cm
float distancePerPulse = wheelCircumference / pulsesPerRevolution; // Distância por pulso em cm
float totalDistance = 0; // Distância total percorrida em cm

void setup() {
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
}

void loop() {
  // Calcula a RPM
  unsigned long currentTime = millis();
  unsigned long timeElapsed = currentTime - lastTime;

  if (timeElapsed >= 1000) { // Atualiza a cada segundo
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
}

// Função de interrupção para o encoder
void encoderISR() {
  pulseCount++;
}