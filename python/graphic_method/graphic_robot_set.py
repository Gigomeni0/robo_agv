from collections import deque
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RoboGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Manual do Robô")

        # Criando a matriz do ambiente
        self.matriz = [
            [0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0],
            [1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0]
        ]

        # Dimensões da matriz
        self.linhas = len(self.matriz)
        self.colunas = len(self.matriz[0])

        # Inicializando o estado do robô
        self.estado_robo = (0, 0, "E", 0)  # (linha, coluna, orientação, passos)
        self.comandos = []  # Lista para armazenar os comandos

        # Configurar interface gráfica
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=1, fill='both')

        self.frame_controles = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_controles, text='Controles')

        self.frame_pontos = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_pontos, text='Pontos Salvos')

        self.frame_controles_lateral = ttk.Frame(self.frame_controles)
        self.frame_controles_lateral.pack(side=tk.LEFT, padx=10, pady=10)

        self.btn_frente = ttk.Button(self.frame_controles_lateral, text="Frente", command=lambda: self.mover_robo("F"))
        self.btn_frente.grid(row=0, column=1)

        self.btn_esquerda = ttk.Button(self.frame_controles_lateral, text="Esquerda", command=lambda: self.mover_robo("E"))
        self.btn_esquerda.grid(row=1, column=0)

        self.btn_direita = ttk.Button(self.frame_controles_lateral, text="Direita", command=lambda: self.mover_robo("D"))
        self.btn_direita.grid(row=1, column=2)

        self.btn_salvar = ttk.Button(self.frame_controles_lateral, text="Salvar Caminho", command=self.salvar_caminho)
        self.btn_salvar.grid(row=2, column=1)

        # Configurar gráfico
        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_controles)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Lista de pontos salvos
        self.lista_pontos = tk.Listbox(self.frame_pontos)
        self.lista_pontos.pack(fill=tk.BOTH, expand=True)

        self.btn_mover_para_ponto = ttk.Button(self.frame_pontos, text="Mover para Ponto", command=self.mover_para_ponto)
        self.btn_mover_para_ponto.pack()

        # Inicializar o ambiente
        self.desenhar_ambiente(self.estado_robo[:2])

    def verificar_sensores(self, linha, coluna, orientacao):
        sensores = [1, 1, 1]  # Inicialmente assume que todos os lados têm obstáculos

        # Verificar posição à frente
        if orientacao == "N" and linha > 0:
            sensores[0] = self.matriz[linha - 1][coluna]  # Frontal
        elif orientacao == "E" and coluna < self.colunas - 1:
            sensores[0] = self.matriz[linha][coluna + 1]
        elif orientacao == "S" and linha < self.linhas - 1:
            sensores[0] = self.matriz[linha + 1][coluna]
        elif orientacao == "W" and coluna > 0:
            sensores[0] = self.matriz[linha][coluna - 1]

        # Verificar posição à esquerda
        if orientacao == "N" and coluna > 0:
            sensores[1] = self.matriz[linha][coluna - 1]  # Esquerda
        elif orientacao == "E" and linha > 0:
            sensores[1] = self.matriz[linha - 1][coluna]
        elif orientacao == "S" and coluna < self.colunas - 1:
            sensores[1] = self.matriz[linha][coluna + 1]
        elif orientacao == "W" and linha < self.linhas - 1:
            sensores[1] = self.matriz[linha + 1][coluna]

        # Verificar posição à direita
        if orientacao == "N" and coluna < self.colunas - 1:
            sensores[2] = self.matriz[linha][coluna + 1]  # Direita
        elif orientacao == "E" and linha < self.linhas - 1:
            sensores[2] = self.matriz[linha + 1][coluna]
        elif orientacao == "S" and coluna > 0:
            sensores[2] = self.matriz[linha][coluna - 1]
        elif orientacao == "W" and linha > 0:
            sensores[2] = self.matriz[linha - 1][coluna]

        return [1 - s for s in sensores]  # Inverter valores (1 = parede, 0 = livre)

    def desenhar_ambiente(self, posicao_robo):
        self.ax.clear()
        self.ax.imshow(self.matriz, cmap="Greys", origin="upper")
        self.ax.scatter(posicao_robo[1], posicao_robo[0], color="red", label="Robô")
        self.ax.set_title("Ambiente e Movimentação do Robô")
        self.ax.legend()
        self.ax.grid(True, which='both', color='lightgray', linewidth=0.5)
        self.ax.set_xticks(range(self.colunas))
        self.ax.set_yticks(range(self.linhas))
        self.canvas.draw()

    def mover_robo(self, comando):
        linha, coluna, orientacao, passos = self.estado_robo

        # Verificar sensores
        sensores = self.verificar_sensores(linha, coluna, orientacao)

        # Decisão de movimento
        if comando == "F" and sensores[0] == 1:  # Caminho livre à frente
            if orientacao == "N":
                linha -= 1
            elif orientacao == "E":
                coluna += 1
            elif orientacao == "S":
                linha += 1
            elif orientacao == "W":
                coluna -= 1
        elif comando == "E":  # Virar à esquerda
            orientacao = {"N": "W", "W": "S", "S": "E", "E": "N"}[orientacao]
        elif comando == "D":  # Virar à direita
            orientacao = {"N": "E", "E": "S", "S": "W", "W": "N"}[orientacao]

        # Atualizar o estado do robô
        self.estado_robo = (linha, coluna, orientacao, passos + 1)

        # Adicionar comando à lista de comandos
        self.comandos.append(comando)

        # Desenhar o ambiente e o robô
        self.desenhar_ambiente((linha, coluna))

    def salvar_caminho(self):
        linha, coluna, orientacao, passos = self.estado_robo
        with open("caminho.txt", "r") as f:
            f.write(f"Posição final: ({linha}, {coluna}), Orientação: {orientacao}, Passos: {passos}\n")
            f.write("Comandos:\n")
            for comando in self.comandos:
                f.write(f"{comando}\n")
        print("Caminho salvo em caminho.txt")

        # Adicionar ponto salvo à lista de pontos
        self.lista_pontos.insert(tk.END, f"({linha}, {coluna}) - {orientacao}")

    def mover_para_ponto(self):
        selecionado = self.lista_pontos.curselection()
        if selecionado:
            ponto = self.lista_pontos.get(selecionado)
            linha, coluna = map(int, ponto.split(')')[0][1:].split(','))
            orientacao = ponto.split('-')[1].strip()
            self.estado_robo = (linha, coluna, orientacao, 0)
            self.desenhar_ambiente((linha, coluna))

if __name__ == "__main__":
    root = tk.Tk()
    app = RoboGUI(root)
    root.mainloop()