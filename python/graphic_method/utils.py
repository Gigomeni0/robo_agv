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


def desenhar_ambiente(ax, canvas, matriz, posicao_robo, base=None):
    print(f"🔍 Desenhando ambiente: Base={base}, Posição do robô={posicao_robo}")
    ax.clear()
    linhas, colunas = len(matriz), len(matriz[0])

    # Desenhar o grid e obstáculos
    for i in range(linhas):
        for j in range(colunas):
            if matriz[i][j] == 1:
                # Obstáculo
                ax.add_patch(plt.Rectangle((j, linhas - i - 1), 1, 1, color='black', alpha=0.8))
            else:
                # Grid normal
                ax.add_patch(plt.Rectangle((j, linhas - i - 1), 1, 1, edgecolor='gray', facecolor='none', linewidth=0.5))

    # Desenhar a base, se definida
    if base:
        base_x, base_y = base["coluna"], linhas - base["linha"] - 1
        ax.add_patch(plt.Rectangle((base_x, base_y), 1, 1, color='green', alpha=0.8))
        ax.text(base_x + 0.5, base_y + 0.5, "B", color="white", ha="center", va="center", fontsize=10)

    # Desenhar o robô
    x, y = posicao_robo[:2]
    ax.add_patch(plt.Rectangle((y, linhas - x - 1), 1, 1, color='blue', alpha=0.8))

    # Configurar os limites dos eixos
    ax.set_xlim(-1, colunas)
    ax.set_ylim(-1, linhas)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(True, linewidth=0.3, color='gray', linestyle='--')
    #ax.invert_yaxis()

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