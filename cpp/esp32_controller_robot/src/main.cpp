#include <WiFi.h>

// Configurações Wi-Fi
const char *ssid = "Gigo 2.4G";
const char *password = "18253122Ro";

// Configurações do servidor
const char *serverIP = "192.168.15.12"; // Substitua pelo IP do servidor
const int serverPort = 65432;

WiFiClient client;

void pinSetup();

void setup()
{
  Serial.begin(115200);
  pinSetup();
  // Conecta ao Wi-Fi
  Serial.print("Conectando ao Wi-Fi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConectado ao Wi-Fi!");
  Serial.println(WiFi.localIP());

  // Conecta ao servidor
  Serial.print("Conectando ao servidor...");
  while (!client.connect(serverIP, serverPort))
  {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConectado ao servidor!");
}

void loop()
{
  static unsigned long lastMillis = 0;

  // Envia mensagem ao servidor a cada 5 segundos
  if (millis() - lastMillis >= 1000)
  {
    lastMillis = millis();
    client.println("Esperando comando...");
  }

  // Verifica se há dados disponíveis do servidor
  if (client.available())
  {
    digitalWrite(14, HIGH); // Conectado
    String resposta = client.readStringUntil('\n');
    Serial.println("Comando recebido: " + resposta);

    // Processa o comando recebido (exemplo)
    if (resposta == "F")
    {
      Serial.println("Comando: Avançar!");
      // Lógica para avançar o robô
      digitalWrite(32, HIGH);
      digitalWrite(33, HIGH);
      digitalWrite(34, LOW);
      digitalWrite(35, LOW);
    }
    else if (resposta == "T")
    {
      Serial.println("Comando: Parar!");
      // Lógica para parar o robô
      digitalWrite(33, LOW);
      digitalWrite(32, LOW);
      digitalWrite(34, LOW);
      digitalWrite(35, LOW);
    }
    else if (resposta == "D")
    {
      Serial.println("Comando: Horário");
      // Lógica para ré do robô
      digitalWrite(32, HIGH);
      digitalWrite(33, LOW);
      digitalWrite(34, HIGH);
      digitalWrite(35, LOW);
    }
    else if (resposta == "E")
    {
      Serial.println("Comando: Anti-horario");
      // Lógica para direita do robô
      digitalWrite(32, LOW);
      digitalWrite(33, HIGH);
      digitalWrite(34, LOW);
      digitalWrite(35, HIGH);
    }
    else
    {
      Serial.println("Comando inválido!");
    }
  }
}

void pinSetup()
{
  pinMode(32, OUTPUT);
  pinMode(33, OUTPUT);
  pinMode(34, OUTPUT);
  pinMode(35, OUTPUT);
  pinMode(14, OUTPUT);
}