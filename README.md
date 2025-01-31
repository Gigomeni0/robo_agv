# Projeto Robô Gaveteiro

Este projeto implementa uma interface gráfica para controlar um robô gaveteiro. O robô pode se mover em um ambiente simulado, salvar pontos de parada, criar rotas e retornar à posição inicial. A interface gráfica é construída usando Tkinter e Matplotlib.

## Funcionalidades

- **Movimentação Manual**: Controle manual do robô usando botões para mover para frente, virar à esquerda e virar à direita.
- **Salvar Pontos**: Salvar pontos de parada no ambiente.
- **Salvar Rotas**: Criar e salvar rotas baseadas nos comandos de movimentação.
- **Executar Rotas**: Executar rotas salvas, movendo o robô automaticamente.
- **Retornar ao Início**: Retornar o robô à posição inicial usando a lista de comandos invertida.
- **Atualização Gradual**: A interface gráfica atualiza gradualmente, mostrando cada movimentação do robô em tempo real.

## Estrutura do Código

### `RoboGUI`

A classe `RoboGUI` é responsável por criar a interface gráfica e gerenciar a lógica de controle do robô.

#### Métodos Principais

- **`__init__(self, root)`**: Inicializa a interface gráfica e configura os componentes.
- **`verificar_sensores(self, linha, coluna, orientacao)`**: Verifica os sensores do robô para detectar obstáculos.
- **`desenhar_ambiente(self, posicao_robo)`**: Desenha o ambiente e a posição do robô na interface gráfica.
- **`mover_robo(self, comando)`**: Move o robô de acordo com o comando fornecido.
- **`salvar_ponto(self)`**: Salva a posição atual do robô como um ponto de parada.
- **`salvar_rota(self)`**: Salva a sequência de comandos como uma rota.
- **`carregar_pontos(self)`**: Carrega os pontos salvos a partir de um arquivo JSON.
- **`carregar_rotas(self)`**: Carrega as rotas salvas a partir de um arquivo JSON.
- **`mover_para_ponto(self)`**: Move o robô para um ponto salvo.
- **`executar_rota(self)`**: Executa uma rota salva.
- **`executar_comandos(self, comandos)`**: Executa uma lista de comandos com atraso entre cada comando.
- **`retornar_inicio(self)`**: Retorna o robô à posição inicial usando a lista de comandos invertida.
- **`inverter_comandos(self, comandos)`**: Inverte a lista de comandos para retornar à posição inicial.
- **`nova_orientacao(self, orientacao_atual, comando)`**: Calcula a nova orientação do robô com base no comando de rotação.
- **`on_closing(self)`**: Fecha a janela e finaliza o programa.

## Como Executar

1. Certifique-se de ter o Python instalado em sua máquina.
2. Instale as bibliotecas necessárias:
   ```bash
   pip install matplotlib numpy