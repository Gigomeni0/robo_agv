import tkinter as tk
from  tkinter import ttk
import ttkbootstrap as ttk
import matplotlib.pyplot as plt

window = ttk.Window()
window.title("Controle do Robô")
window.geometry("1000x800")

tab1 = ttk.Frame(window).pack()
ttk.Frame(tab1).pack( padx=10, pady=10, )


window.mainloop()

# Criando a função de desenho do grafico matplotlib da movimentação do robô
def draw_environment(canvas, figure, environment):
    plt.clf()
    plt.imshow(environment, cmap="Greys", origin="upper")
    plt.title("Ambiente e Movimentação do Robô")
    plt.grid(True, which='both', color='lightgray', linewidth=0.5)
    plt.xticks(range(20))
    plt.yticks(range(20))
    canvas.draw()