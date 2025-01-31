import numpy as np
import matplotlib.pyplot as plt

# Função para desenhar o ambiente e o robô no Tkinter
def draw_environment(canvas, figure, environment, robot_position):
    plt.clf()
    plt.imshow(environment, cmap="Greys", origin="upper")
    plt.scatter(robot_position[1], robot_position[0], color="red", label="Robô")
    plt.title("Ambiente e Movimentação do Robô")
    plt.legend()
    plt.grid(True, which='both', color='lightgray', linewidth=0.5)
    plt.xticks(range(20))
    plt.yticks(range(20))
    canvas.draw()
