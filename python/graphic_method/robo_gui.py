import os
import json
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mqtt_manager import MQTTManager
from robo_controller import RoboController
from utils import desenhar_ambiente, inverter_comandos

class RoboGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Manual do Robô")

        # Criando a matriz do ambiente (10x10)
        self.matriz = [[0] * 30 for _ in range(30)]
        self.estado_robo = self.carregar_ultima_posicao()  # Posição inicial

        # Criar controlador do robô
        self.robo_controller = RoboController(self.matriz, self.estado_robo)

        # Criar cliente MQTT
        self.mqtt_client = MQTTManager(
            broker="test.mosquitto.org",
            port=1883,
            topics=["robo_gaveteiro/comandos", "robo_gaveteiro/status"],
            on_message_callback=self.on_mqtt_message
        )
        self.mqtt_client.connect()

        # Criando interface gráfica
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=1, fill='both')
        
        self.frame_controles = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_controles, text='Controles')
        
        self.frame_rotas = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_rotas, text='Rotas Salvas')
        
        self.frame_sequencia = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_sequencia, text='Sequência de Rotas')

        self.frame_controles_lateral = ttk.Frame(self.frame_controles)
        self.frame_controles_lateral.pack(side=tk.LEFT, padx=10, pady=10)

        # Botões de controle do robô
        self.btn_frente = ttk.Button(self.frame_controles_lateral, text="Frente", command=lambda: self.enviar_comando("F"))
        self.btn_frente.grid(row=0, column=1)

        self.btn_esquerda = ttk.Button(self.frame_controles_lateral, text="Esquerda", command=lambda: self.enviar_comando("E"))
        self.btn_esquerda.grid(row=1, column=0)

        self.btn_direita = ttk.Button(self.frame_controles_lateral, text="Direita", command=lambda: self.enviar_comando("D"))
        self.btn_direita.grid(row=1, column=2)
        
        self.btn_retornar_inicio = ttk.Button(self.frame_controles_lateral, text="Retornar ao Início", command=self.retornar_inicio)
        self.btn_retornar_inicio.grid(row=3, column=1)
        
        self.btn_pausa = ttk.Button(self.frame_controles_lateral, text="Inserir Pausa", command=self.inserir_pausa)
        self.btn_pausa.grid(row=3, column=0, pady=5)
        
        self.btn_iniciar_gravacao = ttk.Button(self.frame_controles_lateral, text="Iniciar Gravação", command=self.iniciar_gravacao)
        self.btn_iniciar_gravacao.grid(row=4, column=0, pady=5)

        self.btn_salvar_rota = ttk.Button(self.frame_controles_lateral, text="Salvar Rota", command=self.salvar_rota)
        self.btn_salvar_rota.grid(row=4, column=2, pady=5)

        # Configuração de tempo de espera
        self.label_wait = ttk.Label(self.frame_controles_lateral, text="Tempo de Espera (s):")
        self.label_wait.grid(row=6, column=0, pady=5)

        self.spin_wait = ttk.Spinbox(self.frame_controles_lateral, from_=1, to=30, width=5)
        self.spin_wait.grid(row=6, column=1, pady=5)
        self.spin_wait.set(1)
        
        # Lista de comandos
        self.lista_comandos = tk.Listbox(self.frame_controles_lateral, height=10)
        self.lista_comandos.grid(row=8, column=0, columnspan=3, pady=5)
        
        # Lista de rotas salvas
        self.lista_rotas = tk.Listbox(self.frame_rotas)
        self.lista_rotas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.btn_executar_rota = ttk.Button(self.frame_rotas, text="Executar Rota", command=self.executar_rota)
        self.btn_executar_rota.pack(pady=10)
        
        # Configurar gráfico
        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_controles)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Inicializar o ambiente
        desenhar_ambiente(self.ax, self.canvas, self.matriz, self.estado_robo[:2])

        # Capturar evento de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Carregar rotas salvas
        self.carregar_rotas_salvas()

    def carregar_ultima_posicao(self):
        """Carrega a última posição do robô a partir do arquivo JSON."""
        caminho_arquivo = os.path.join(os.path.dirname(__file__), "position.json")
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                    return (dados["linha"], dados["coluna"], dados["orientacao"], dados["passos"])
                except json.JSONDecodeError:
                    pass
        # Se o arquivo não existir ou houver um erro, inicializar no centro, virado para o norte
        return (self.linhas // 2, self.colunas // 2, "N", 0)

    def salvar_posicao_atual(self):
        """Salva a posição atual do robô no arquivo JSON."""
        caminho_arquivo = os.path.join(os.path.dirname(__file__), "position.json")
        dados = {
            "linha": self.estado_robo[0],
            "coluna": self.estado_robo[1],
            "orientacao": self.estado_robo[2],
            "passos": self.estado_robo[3]
        }
        with open(caminho_arquivo, "w") as f:
            json.dump(dados, f, indent=4)


    def enviar_comando(self, comando):
        self.mqtt_client.publish("robo_gaveteiro/comandos", comando)
        self.lista_comandos.insert(tk.END, f"[{comando}]")
        self.estado_robo = self.robo_controller.mover_robo(comando)

        # Salvar a posição atual do robô
        self.salvar_posicao_atual()
        self.atualizar_interface()
    
    def atualizar_interface(self):
        self.label_wait.config(text=f"Posição Atual: {self.estado_robo[:2]}")
        desenhar_ambiente(self.ax, self.canvas, self.matriz, self.estado_robo[:2])
    
    def inserir_pausa(self):
        segundos = int(self.spin_wait.get())
        comando = f"W{segundos}"
        self.lista_comandos.insert(tk.END, f"[{comando}]")
        self.robo_controller.comandos.append(comando)
        print(f"Pausa de {segundos} segundos adicionada.")
    
    def retornar_inicio(self):
        if not self.robo_controller.comandos:
            print("⚠️ Nenhum comando registrado para inverter.")
            return
        
        comandos_retorno = inverter_comandos(self.robo_controller.comandos, self.estado_robo[2])

        for comando in comandos_retorno:
            self.enviar_comando(comando)  # Envia cada comando para o robô

        print("🔄 Retornando ao início...")

    def iniciar_gravacao(self):
        """Inicia a gravação de comandos para uma nova rota."""
        self.robo_controller.comandos = []  # Limpa comandos anteriores
        self.lista_comandos.delete(0, tk.END)  # Limpa a lista da interface
        print("🔴 Gravação iniciada. Execute os comandos para salvar a rota.")


    def salvar_rota(self):
        """Salva os comandos gravados, incluindo a orientação inicial e final."""
        if not self.robo_controller.comandos:
            print("⚠️ Nenhum comando gravado para salvar.")
            return

        caminho_arquivo = os.path.join(os.path.dirname(__file__), "rotas_salvas.json")

        # Carregar as rotas já existentes no arquivo JSON
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                except json.JSONDecodeError:
                    dados = []
        else:
            dados = []

        # Contar quantas rotas já existem no arquivo JSON
        total_rotas_salvas = len(dados)

        # Criar o nome da nova rota
        rota_nome = f"Rota {total_rotas_salvas + 1}"

        rota = {
            "nome": rota_nome,
            "comandos": self.robo_controller.comandos,
            "orientacao_inicial": self.estado_robo[2],  # Orientação no começo
            "orientacao_final": self.robo_controller.get_orientacao_final()  # Orientação no final
        }

        # Adiciona a nova rota à lista de rotas salvas
        dados.append(rota)

        # Salva o arquivo atualizado
        with open(caminho_arquivo, "w") as f:
            json.dump(dados, f, indent=4)

        # Atualiza a lista na interface
        self.lista_rotas.insert(tk.END, rota_nome)
        print(f"💾 Rota salva: {rota_nome} (Orientação inicial: {rota['orientacao_inicial']}, final: {rota['orientacao_final']})")

    def carregar_rotas_salvas(self):
        """Carrega as rotas do arquivo JSON para a interface gráfica."""
        caminho_arquivo = os.path.join(os.path.dirname(__file__), "rotas_salvas.json")
        print(f"Carregando rotas salvas do arquivo: {caminho_arquivo}")

        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                except json.JSONDecodeError:
                    dados = []
                    print("Erro ao decodificar o arquivo JSON.")
        else:
            dados = []
            print("Arquivo de rotas salvas não encontrado.")

        # Adiciona cada rota à interface gráfica
        for rota in dados:
            self.lista_rotas.insert(tk.END, rota["nome"])

    def executar_rota(self):
        selecionado = self.lista_rotas.curselection()
        if selecionado:
            rota_nome = self.lista_rotas.get(selecionado)
            print(f"🔄 Executando rota: {rota_nome}")
            comandos = self.robo_controller.carregar_rotas(rota_nome)
            print(f"📜 Comandos carregados: {comandos}")
            for comando in comandos:
                print(f"🚀 Enviando comando: {comando}")
                self.enviar_comando(comando)
        else:
            print("⚠️ Nenhuma rota selecionada.")
    
    def on_mqtt_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print(f"📡 Mensagem recebida: {msg.topic} {payload}")

        if msg.topic == "robo_gaveteiro/status":
            if payload == "obstaculo":
                print("⚠️ Obstáculo detectado! Robô parado.")
            else:
                print(f"📍 Novo status do robô: {payload}")
                self.estado_robo = json.loads(payload)  # Atualiza posição se for JSON válido
                self.atualizar_interface()
        elif msg.topic == "robo_gaveteiro/comandos":
            print(f"🔄 Comando recebido: {payload}")

    
    def on_closing(self):
        self.mqtt_client.disconnect()
        self.root.destroy()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = RoboGUI(root)
    root.mainloop()
