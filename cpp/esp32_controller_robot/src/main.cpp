#include <Arduino.h>

// ---- Definições de Pinos ----
// Motores (H-Bridge L298N)
#define IN1 6
#define IN2 7
#define ENA 14  // PWM Motor 1
#define IN3 41
#define IN4 40
#define ENB 19  // PWM Motor 2

// Encoders (Motores com encoder A/B)
#define ENCODER_A 4
#define ENCODER_B 5
#define ENCODER_A2 2
#define ENCODER_B2 42

// ---- Variáveis dos Encoders ----
volatile long pulseCount1 = 0; // Contador de pulsos do encoder 1
volatile long pulseCount2 = 0; // Contador de pulsos do encoder 2
float pulsesPerRevolution = 11; // Pulsos por revolução do encoder
float wheelDiameter = 12; // Diâmetro da roda em cm
float wheelCircumference = PI * wheelDiameter; // Circunferência da roda
float distancePerPulse = wheelCircumference / pulsesPerRevolution; // Distância por pulso

// ---- Funções de Interrupção para os Encoders ----
void encoder1_ISR() {
  pulseCount1++; // Incrementa o contador de pulsos do encoder 1
}

void encoder2_ISR() {
  pulseCount2++; // Incrementa o contador de pulsos do encoder 2
}

// ---- Configuração Inicial ----
void setup() {
  // Configuração dos pinos dos motores
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENB, OUTPUT);

  // Configuração dos pinos dos encoders
  pinMode(ENCODER_A, INPUT_PULLUP);
  pinMode(ENCODER_B, INPUT_PULLUP);
  pinMode(ENCODER_A2, INPUT_PULLUP);
  pinMode(ENCODER_B2, INPUT_PULLUP);

  // Configuração das interrupções para os encoders
  attachInterrupt(digitalPinToInterrupt(ENCODER_A), encoder1_ISR, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A2), encoder2_ISR, RISING);

  // Inicializa a comunicação serial (para debug)
  Serial.begin(9600);
}

// ---- Loop Principal ----
void loop() {
  // Movimenta ambos os motores para frente
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 200); // Velocidade do motor 1 (0-255)

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, 200); // Velocidade do motor 2 (0-255)

  // Calcula a distância percorrida
  float distance1 = pulseCount1 * distancePerPulse; // Distância do motor 1
  float distance2 = pulseCount2 * distancePerPulse; // Distância do motor 2

  // Exibe os valores no monitor serial
  Serial.print("Encoder 1 - Pulsos: ");
  Serial.print(pulseCount1);
  Serial.print(" | Distância: ");
  Serial.print(distance1);
  Serial.println(" cm");

  Serial.print("Encoder 2 - Pulsos: ");
  Serial.print(pulseCount2);
  Serial.print(" | Distância: ");
  Serial.print(distance2);
  Serial.println(" cm");

  delay(100); // Aguarda 100 ms antes de atualizar novamente
}