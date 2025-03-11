import numpy as np
import matplotlib.pyplot as plt
import time

def verificar_sensores(matriz, linha, coluna, orientacao):
    deslocamentos = {
        "N": [(-1, 0), (0, -1), (0, 1)],  # Frente, Esquerda, Direita
        "E": [(0, 1), (-1, 0), (1, 0)],
        "S": [(1, 0), (0, 1), (0, -1)],
        "W": [(0, -1), (1, 0), (-1, 0)]
    }

    sensores = []
    for dx, dy in deslocamentos[orientacao]:
        nova_linha, nova_coluna = linha + dx, coluna + dy
        if 0 <= nova_linha < len(matriz) and 0 <= nova_coluna < len(matriz[0]):
            sensores.append(1 - matriz[nova_linha][nova_coluna])  # 1 = livre, 0 = obstáculo
        else:
            sensores.append(0)  # Fora dos limites é sempre obstáculo

    return sensores

def desenhar_ambiente(ax, canvas, matriz, posicao_robo):
    ax.clear()
    ax.imshow(matriz, cmap="Greys", origin="upper")

    # Exibir o robô com um ícone vermelho
    ax.scatter(posicao_robo[1], posicao_robo[0], color="red", marker="o", s=100, label="Robô")

    # Configuração do gráfico
    ax.set_title("Ambiente e Movimentação do Robô")
    ax.legend()
    ax.grid(True, which='both', color='lightgray', linewidth=0.5)
    ax.set_xticks(range(len(matriz[0])))
    ax.set_yticks(range(len(matriz)))
    
    canvas.draw()


def inverter_comandos(comandos, orientacao_atual):
    orientacoes = ["N", "E", "S", "W"]
    comandos_invertidos = []
    for comando in reversed(comandos):
        if comando == "F":
            comandos_invertidos.append("F")
        elif comando == "E":
            orientacao_atual = nova_orientacao(orientacao_atual, "D")
            comandos_invertidos.append("D")
        elif comando == "D":
            orientacao_atual = nova_orientacao(orientacao_atual, "E")
            comandos_invertidos.append("E")
    # Adicionar duas rotações para inverter a direção
    comandos_invertidos.insert(0, "D")
    comandos_invertidos.insert(0, "D")
    return comandos_invertidos

def nova_orientacao(orientacao_atual, comando):
    orientacoes = ["N", "E", "S", "W"]
    idx = orientacoes.index(orientacao_atual)
    if comando == "E":
        return orientacoes[(idx - 1) % 4]
    elif comando == "D":
        return orientacoes[(idx + 1) % 4]

def esperar_tempo(segundos):
    time.sleep(segundos)