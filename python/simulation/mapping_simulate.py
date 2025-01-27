import matplotlib.pyplot as plt
import numpy as np
import random
from collections import deque

# Configurações do ambiente
MAP_SIZE = 20  # Tamanho do mapa (20x20 células)
environment = np.full((MAP_SIZE, MAP_SIZE), -1)  # -1: desconhecido, 0: livre, 1: ocupado
robot_position = (0, 0)  # Posição inicial do robô

# Gerar obstáculos aleatórios
for _ in range(50):  # 50 obstáculos aleatórios
    x, y = random.randint(0, MAP_SIZE - 1), random.randint(0, MAP_SIZE - 1)
    environment[x, y] = 1  # 1: ocupado

# Função para mover o robô
def move_robot_bfs(robot_position, environment):
    queue = deque([robot_position])
    visited = set()
    visited.add(robot_position)

    while queue:
        x, y = queue.popleft() # Desenfileirar a posição atual do robô (x, y) da fila de visitados (visited) e da fila (queue) 

        # Detectar arredores (simulando sensores)
        surroundings = [
            (x + 1, y), (x - 1, y),  # Movimento vertical
            (x, y + 1), (x, y - 1)   # Movimento horizontal
        ]

        for nx, ny in surroundings:
            if 0 <= nx < MAP_SIZE and 0 <= ny < MAP_SIZE:
                if environment[nx, ny] == -1:  # Se desconhecido
                    environment[nx, ny] = 0  # Marcar como livre (simulação)
                if (nx, ny) not in visited and environment[nx, ny] == 0:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        # Mostrar o mapa
        plt.imshow(environment, cmap="gray", origin="upper")
        plt.title("Mapeamento Dinâmico")
        plt.pause(0.1)

    print("Exploração concluída!")
    plt.show()

# Iniciar a simulação
move_robot_bfs(robot_position, environment)