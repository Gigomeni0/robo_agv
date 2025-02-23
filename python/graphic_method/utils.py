import numpy as np
import matplotlib.pyplot as plt
import time

def verificar_sensores(matriz, linha, coluna, orientacao):
    sensores = [1, 1, 1]  # Inicialmente assume que todos os lados têm obstáculos

    # Verificar posição à frente
    if orientacao == "N" and linha > 0:
        sensores[0] = matriz[linha - 1][coluna]  # Frontal
    elif orientacao == "E" and coluna < len(matriz[0]) - 1:
        sensores[0] = matriz[linha][coluna + 1]
    elif orientacao == "S" and linha < len(matriz) - 1:
        sensores[0] = matriz[linha + 1][coluna]
    elif orientacao == "W" and coluna > 0:
        sensores[0] = matriz[linha][coluna - 1]

    # Verificar posição à esquerda
    if orientacao == "N" and coluna > 0:
        sensores[1] = matriz[linha][coluna - 1]  # Esquerda
    elif orientacao == "E" and linha > 0:
        sensores[1] = matriz[linha - 1][coluna]
    elif orientacao == "S" and coluna < len(matriz[0]) - 1:
        sensores[1] = matriz[linha][coluna + 1]
    elif orientacao == "W" and linha < len(matriz) - 1:
        sensores[1] = matriz[linha + 1][coluna]

    # Verificar posição à direita
    if orientacao == "N" and coluna < len(matriz[0]) - 1:
        sensores[2] = matriz[linha][coluna + 1]  # Direita
    elif orientacao == "E" and linha < len(matriz) - 1:
        sensores[2] = matriz[linha + 1][coluna]
    elif orientacao == "S" and coluna > 0:
        sensores[2] = matriz[linha][coluna - 1]
    elif orientacao == "W" and linha > 0:
        sensores[2] = matriz[linha - 1][coluna]

    return [1 - s for s in sensores]  # Inverter valores (1 = parede, 0 = livre)

def desenhar_ambiente(ax, canvas, matriz, posicao_robo):
    ax.clear()
    ax.imshow(matriz, cmap="Greys", origin="upper")
    ax.scatter(posicao_robo[1], posicao_robo[0], color="red", label="Robô")
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