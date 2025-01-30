from collections import deque
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import json

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

        self.btn_salvar_ponto = ttk.Button(self.frame_controles_lateral, text="Salvar Ponto", command=self.salvar_ponto)
        self.btn_salvar_ponto.grid(row=2, column=0)

        self.btn_salvar_rota = ttk.Button(self.frame_controles_lateral, text="Salvar Rota", command=self.salvar_rota)
        self.btn_salvar_rota.grid(row=2, column=2)

        self.btn_retornar_inicio = ttk.Button(self.frame_controles_lateral, text="Retornar ao Início", command=self.retornar_inicio)
        self.btn_retornar_inicio.grid(row=3, column=1)

        # Lista de rotas salvas
        self.lista_rotas = tk.Listbox(self.frame_controles_lateral)
        self.lista_rotas.grid(row=4, column=0, columnspan=3, pady=10)

        self.btn_executar_rota = ttk.Button(self.frame_controles_lateral, text="Executar Rota", command=self.executar_rota)
        self.btn_executar_rota.grid(row=5, column=1)

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

        # Capturar evento de fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Carregar pontos e rotas salvas
        self.carregar_pontos()
        self.carregar_rotas()

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

    def salvar_ponto(self):
        linha, coluna, orientacao, passos = self.estado_robo
        caminho_arquivo = "python/graphic_method/pontos_salvos.json"
        ponto_nome = f"Ponto {len(self.lista_pontos.get(0, tk.END)) + 1}"
        ponto = {
            "nome": ponto_nome,
            "posicao_final": {"linha": linha, "coluna": coluna},
            "orientacao": orientacao,
            "passos": passos,
            "comandos": self.comandos
        }
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                except json.JSONDecodeError:
                    dados = []
        else:
            dados = []

        dados.append(ponto)

        with open(caminho_arquivo, "w") as f:
            json.dump(dados, f, indent=4)
        print(f"Ponto salvo em {caminho_arquivo}")

        # Adicionar ponto salvo à lista de pontos
        self.lista_pontos.insert(tk.END, ponto_nome)

    def salvar_rota(self):
        caminho_arquivo = "python/graphic_method/rotas_salvas.json"
        rota_nome = f"Rota {len(self.lista_rotas.get(0, tk.END)) + 1}"
        rota = {
            "nome": rota_nome,
            "comandos": self.comandos
        }
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                except json.JSONDecodeError:
                    dados = []
        else:
            dados = []

        dados.append(rota)

        with open(caminho_arquivo, "w") as f:
            json.dump(dados, f, indent=4)
        print(f"Rota salva em {caminho_arquivo}")

        # Adicionar rota salva à lista de rotas
        self.lista_rotas.insert(tk.END, rota_nome)

    def carregar_pontos(self):
        caminho_arquivo = "python/graphic_method/pontos_salvos.json"
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                except json.JSONDecodeError:
                    dados = []
            for ponto in dados:
                if "nome" in ponto:
                    self.lista_pontos.insert(tk.END, ponto["nome"])

    def carregar_rotas(self):
        caminho_arquivo = "python/graphic_method/rotas_salvas.json"
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                except json.JSONDecodeError:
                    dados = []
            for rota in dados:
                if "nome" in rota:
                    self.lista_rotas.insert(tk.END, rota["nome"])

    def mover_para_ponto(self):
        selecionado = self.lista_pontos.curselection()
        if selecionado:
            ponto_nome = self.lista_pontos.get(selecionado)
            caminho_arquivo = "python/graphic_method/pontos_salvos.json"
            with open(caminho_arquivo, "r") as f:
                dados = json.load(f)
            for p in dados:
                if p["nome"] == ponto_nome:
                    self.estado_robo = (p["posicao_final"]["linha"], p["posicao_final"]["coluna"], p["orientacao"], 0)
                    self.comandos = p["comandos"]
                    break
            self.desenhar_ambiente((self.estado_robo[0], self.estado_robo[1]))

    def executar_rota(self):
        selecionado = self.lista_rotas.curselection()
        if selecionado:
            rota_nome = self.lista_rotas.get(selecionado)
            caminho_arquivo = "python/graphic_method/rotas_salvas.json"
            with open(caminho_arquivo, "r") as f:
                dados = json.load(f)
            for r in dados:
                if r["nome"] == rota_nome:
                    comandos = r["comandos"]
                    break
            # Reiniciar o robô na posição inicial
            self.estado_robo = (0, 0, "E", 0)
            self.comandos = []
            self.desenhar_ambiente((0, 0))
            self.executar_comandos(comandos)

    def executar_comandos(self, comandos):
        if comandos:
            comando = comandos.pop(0)
            self.mover_robo(comando)
            self.root.after(500, lambda: self.executar_comandos(comandos))  # Atraso de 500ms entre os comandos

    def retornar_inicio(self):
        comandos_retorno = self.inverter_comandos(self.comandos)
        self.executar_comandos(comandos_retorno)

    def inverter_comandos(self, comandos):
        orientacao_atual = self.estado_robo[2]
        comandos_invertidos = []
        for comando in reversed(comandos):
            if comando == "F":
                comandos_invertidos.append("F")
            elif comando == "E":
                orientacao_atual = self.nova_orientacao(orientacao_atual, "D")
                comandos_invertidos.append("D")
            elif comando == "D":
                orientacao_atual = self.nova_orientacao(orientacao_atual, "E")
                comandos_invertidos.append("E")
        # Adicionar duas rotações para inverter a direção
        comandos_invertidos.insert(0, "D")
        comandos_invertidos.insert(0, "D")
        return comandos_invertidos

    def nova_orientacao(self, orientacao_atual, comando):
        orientacoes = ["N", "E", "S", "W"]
        idx = orientacoes.index(orientacao_atual)
        if comando == "E":
            return orientacoes[(idx - 1) % 4]
        elif comando == "D":
            return orientacoes[(idx + 1) % 4]

    def on_closing(self):
        self.root.destroy()
        print("Janela fechada e programa finalizado.")

if __name__ == "__main__":
    root = tk.Tk()
    app = RoboGUI(root)
    root.mainloop()