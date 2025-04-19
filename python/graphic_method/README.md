# Projeto Robo Gaveteiro

Este projeto é um sistema de controle para um robô gaveteiro. Ele inclui componentes para controle do robô, interface gráfica e comunicação MQTT.

## Estrutura do Projeto

- `python/graphic_method/`: Contém o código Python para a interface gráfica e controle do robô.
- `cpp/esp32_controller_robot/`: Contém o código C++ para o controle do robô usando um ESP32.

## Classes e Métodos

### Python

#### `utils.py`

- **verificar_sensores(matriz, linha, coluna, orientacao)**
  - Verifica os sensores do robô para detectar obstáculos.
  - **Parâmetros:**
    - `matriz`: Matriz representando o ambiente.
    - `linha`: Linha atual do robô.
    - `coluna`: Coluna atual do robô.
    - `orientacao`: Orientação atual do robô (`"N"`, `"E"`, `"S"`, `"W"`).
  - **Retorna:** Lista de sensores indicando se há obstáculos (1 = livre, 0 = obstáculo).

- **desenhar_ambiente(ax, canvas, matriz, posicao_robo)**
  - Desenha o ambiente e a posição do robô em um gráfico.
  - **Parâmetros:**
    - `ax`: Objeto Axes do Matplotlib.
    - `canvas`: Objeto Canvas do Matplotlib.
    - `matriz`: Matriz representando o ambiente.
    - `posicao_robo`: Posição atual do robô (linha, coluna).

- **inverter_comandos(comandos, orientacao_atual)**
  - Inverte a sequência de comandos para retornar ao ponto inicial.
  - **Parâmetros:**
    - `comandos`: Lista de comandos.
    - `orientacao_atual`: Orientação atual do robô.
  - **Retorna:** Lista de comandos invertidos.

- **nova_orientacao(orientacao_atual, comando)**
  - Calcula a nova orientação do robô após um comando de rotação.
  - **Parâmetros:**
    - `orientacao_atual`: Orientação atual do robô.
    - `comando`: Comando de rotação (`"E"` ou `"D"`).
  - **Retorna:** Nova orientação do robô.

- **esperar_tempo(segundos)**
  - Faz o robô esperar por um determinado tempo.
  - **Parâmetros:**
    - `segundos`: Tempo de espera em segundos.

#### `robo_controller.py`

- **RoboController**
  - Classe para controlar o robô.
  - **Métodos:**
    - `__init__(self, matriz, estado_robo)`: Inicializa o controlador com a matriz do ambiente e o estado inicial do robô.
    - `mover_robo(self, comando)`: Move o robô de acordo com o comando.
    - `simular_movimento(self, comandos)`: Simula a execução dos comandos e retorna a posição final do robô.
    - `iniciar_gravacao(self)`: Inicia a gravação de comandos.
    - `salvar_rota(self, caminho_arquivo)`: Salva a rota gravada em um arquivo.
    - `carregar_rotas(self, caminho_arquivo)`: Carrega rotas de um arquivo.
    - `executar_comandos(self, comandos)`: Executa uma lista de comandos.
    - `inverter_rota(self)`: Inverte a rota gravada.
    - `get_orientacao_final(self)`: Retorna a orientação final após a execução da rota.

#### `robo_gui.py`

- **RoboGUI**
  - Classe para a interface gráfica do robô.
  - **Métodos:**
    - `__init__(self, root)`: Inicializa a interface gráfica.
    - `enviar_comando(self, comando)`: Envia um comando para o robô via MQTT.
    - `atualizar_interface(self)`: Atualiza a interface gráfica com a posição atual do robô.
    - `inserir_pausa(self)`: Insere um comando de pausa na lista de comandos.
    - `retornar_inicio(self)`: Retorna o robô ao ponto inicial invertendo os comandos.
    - `iniciar_gravacao(self)`: Inicia a gravação de comandos para uma nova rota.
    - `salvar_rota(self)`: Salva os comandos gravados em um arquivo.
    - `executar_rota(self)`: Executa uma rota salva.
    - `on_mqtt_message(self, client, userdata, msg)`: Callback para mensagens MQTT recebidas.
    - `on_closing(self)`: Desconecta o cliente MQTT e fecha a interface gráfica.

### C++

#### `main.cpp`

- **Configuração Inicial**
  - Configura os pinos dos motores e encoders.
  - Inicializa a comunicação serial para debug.

- **Loop Principal**
  - Move os motores para frente.
  - Calcula a distância percorrida com base nos pulsos dos encoders.
  - Exibe os valores no monitor serial.

## Como Executar

### Python

1. Navegue até o diretório do projeto:
   ```sh
   cd /c:/Users/joaoa/OneDrive/Área de Trabalho/Projetos/robo_gaveteiro
   ```

2. Execute o script principal:
   ```sh
   python -m python.graphic_method.graphic_robot_set
   ```

### C++

1. Compile e carregue o código no ESP32 usando a IDE Arduino ou outra ferramenta de sua escolha.
2. Conecte o ESP32 ao seu computador e abra o monitor serial para visualizar a saída.

## Contribuição

Sinta-se à vontade para contribuir com melhorias para este projeto. Envie pull requests ou abra issues para discutir mudanças.

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.