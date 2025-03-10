import os
import json
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils import verificar_sensores, desenhar_ambiente, inverter_comandos
from mqtt_config import MQTTClient

class RoboGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Manual do Robô")

        # Configurações MQTT
        self.mqtt_broker = "test.mosquitto.org"  # Usar o broker de teste do mosquitto.org
        self.mqtt_port = 1883
        self.mqtt_topic = "robo_gaveteiro/comandos"

        # Criar cliente MQTT
        self.mqtt_client = MQTTClient(self.mqtt_broker, self.mqtt_port, self.mqtt_topic, self.on_mqtt_message)
        self.mqtt_client.connect()

        # Criando a matriz do ambiente (10x10)
        self.matriz = [
            [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ]

        # Dimensões da matriz
        self.linhas = len(self.matriz)
        self.colunas = len(self.matriz[0])

        # Carregar a última posição do robô a partir do arquivo position.json
        self.estado_robo = self.carregar_ultima_posicao()

        self.comandos = []  # Lista para armazenar os comandos

        # Configurar interface gráfica
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

        self.btn_frente = ttk.Button(self.frame_controles_lateral, text="Frente", command=lambda: self.enviar_comando_mqtt("F"))
        self.btn_frente.grid(row=0, column=1)

        self.btn_esquerda = ttk.Button(self.frame_controles_lateral, text="Esquerda", command=lambda: self.enviar_comando_mqtt("E"))
        self.btn_esquerda.grid(row=1, column=0)

        self.btn_direita = ttk.Button(self.frame_controles_lateral, text="Direita", command=lambda: self.enviar_comando_mqtt("D"))
        self.btn_direita.grid(row=1, column=2)

        self.btn_iniciar_gravacao = ttk.Button(self.frame_controles_lateral, text="Iniciar Gravação", command=self.iniciar_gravacao)
        self.btn_iniciar_gravacao.grid(row=2, column=0)

        self.btn_salvar_rota = ttk.Button(self.frame_controles_lateral, text="Salvar Rota", command=self.salvar_rota)
        self.btn_salvar_rota.grid(row=2, column=2)

        self.btn_retornar_inicio = ttk.Button(self.frame_controles_lateral, text="Retornar ao Início", command=self.retornar_inicio)
        self.btn_retornar_inicio.grid(row=3, column=1)

        # Botão para limpar memória
        self.btn_limpar_memoria = ttk.Button(self.frame_controles_lateral, text="Limpar Memória", command=self.limpar_memoria)
        self.btn_limpar_memoria.grid(row=4, column=1)

        # Configuração de tempo de espera
        self.label_wait = ttk.Label(self.frame_controles_lateral, text="Tempo de Espera (s):")
        self.label_wait.grid(row=6, column=0, pady=5)

        self.spin_wait = ttk.Spinbox(self.frame_controles_lateral, from_=1, to=30, width=5)
        self.spin_wait.grid(row=6, column=1, pady=5)
        self.spin_wait.set(1)  # Valor padrão

        self.btn_pausa = ttk.Button(self.frame_controles_lateral, text="Inserir Pausa", command=self.inserir_pausa)
        self.btn_pausa.grid(row=3, column=0, pady=5)    

        # Exibir coordenada atual do robô
        self.label_coordenadas = ttk.Label(self.frame_controles_lateral, text=f"Coordenadas: ({self.estado_robo[0]}, {self.estado_robo[1]})")
        self.label_coordenadas.grid(row=5, column=0, columnspan=3, pady=10)

        # Comandos da rota
        self.label_comandos = ttk.Label(self.frame_controles_lateral, text="Comandos da Rota:")
        self.label_comandos.grid(row=7, column=0, columnspan=3, pady=5)

        self.lista_comandos = tk.Listbox(self.frame_controles_lateral, height=10)
        self.lista_comandos.grid(row=8, column=0, columnspan=3, pady=5)

        self.label_estado = ttk.Label(self.frame_controles_lateral, text="📡 Estado: Desconhecido")
        self.label_estado.grid(row=10, column=0, columnspan=3, pady=5)

        self.label_bateria = ttk.Label(self.frame_controles_lateral, text="🔋 Bateria: --%")
        self.label_bateria.grid(row=11, column=0, columnspan=3, pady=5)


        # Lista de rotas salvas
        self.lista_rotas = tk.Listbox(self.frame_rotas)
        self.lista_rotas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.btn_executar_rota = ttk.Button(self.frame_rotas, text="Executar Rota", command=self.executar_rota)
        self.btn_executar_rota.pack(pady=10)

        # Instruções para criar sequência
        self.label_instrucoes = ttk.Label(self.frame_sequencia, text="Selecione as rotas e clique em 'Adicionar à Sequência'")
        self.label_instrucoes.pack(pady=10)

        # Lista de rotas para criar sequência
        self.lista_rotas_sequencia = tk.Listbox(self.frame_sequencia, selectmode=tk.MULTIPLE)
        self.lista_rotas_sequencia.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.btn_adicionar_sequencia = ttk.Button(self.frame_sequencia, text="Adicionar à Sequência", command=self.adicionar_sequencia)
        self.btn_adicionar_sequencia.pack(pady=10)

        self.btn_remover_sequencia = ttk.Button(self.frame_sequencia, text="Remover da Sequência", command=self.remover_sequencia)
        self.btn_remover_sequencia.pack(pady=10)

        self.label_sequencia_atual = ttk.Label(self.frame_sequencia, text="Sequência Atual:")
        self.label_sequencia_atual.pack(pady=10)

        self.lista_sequencia_atual = tk.Listbox(self.frame_sequencia)
        self.lista_sequencia_atual.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.btn_executar_sequencia = ttk.Button(self.frame_sequencia, text="Executar Sequência", command=self.executar_sequencia)
        self.btn_executar_sequencia.pack(pady=10)

        self.loop_var = tk.IntVar()
        self.check_loop = ttk.Checkbutton(self.frame_sequencia, text="Loop", variable=self.loop_var)
        self.check_loop.pack(pady=10)

        # Configurar gráfico
        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_controles)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Inicializar o ambiente
        desenhar_ambiente(self.ax, self.canvas, self.matriz, self.estado_robo[:2])

        # Capturar evento de fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Carregar rotas salvas
        self.carregar_rotas()

    def on_mqtt_message(self, client, userdata, msg):
        mensagem = msg.payload.decode()
        print(f"📡 Mensagem recebida: {msg.topic} {mensagem}")

        try:
            data = json.loads(mensagem)

            # SE O STATUS VEIO DO ROBÔ
            if msg.topic == "robo_gaveteiro/status":
                # Atualizar status do robô na interface
                self.atualizar_status_robo(data)

            # SE O ROBÔ DETECTOU UM OBSTÁCULO
            elif "obstaculo" in data:
                coordenadas = data["obstaculo"]
                linha, coluna = map(int, coordenadas.strip("()").split(","))

                # Atualizar o mapa
                self.matriz[linha][coluna] = 1
                desenhar_ambiente(self.ax, self.canvas, self.matriz, self.estado_robo[:2])

                # Exibir alerta na interface
                self.label_coordenadas.config(text=f"⚠️ Obstáculo detectado em {coordenadas}")

                print("⚠️ Execução pausada devido a um obstáculo!")
                return  # Não continua a rota até o usuário decidir

        except json.JSONDecodeError:
            print("❌ Erro ao interpretar mensagem MQTT.")

    def atualizar_status_robo(self, status):
        # Se o JSON recebido tiver posição do robô
        if "posicao" in status:
            linha, coluna = status["posicao"]
            self.label_coordenadas.config(text=f"📍 Robô em ({linha}, {coluna})")

        # Se tiver um estado atual (movendo, parado, erro, etc.)
        if "estado" in status:
            self.label_estado.config(text=f"📡 Estado: {status['estado']}")

        # Se tiver nível de bateria 🔋
        if "bateria" in status:
            self.label_bateria.config(text=f"🔋 Bateria: {status['bateria']}%")

    def enviar_comando_mqtt(self, comando):
        
        if comando.startswith("W"):
            self.mover_robo(comando)  # Use the new pause system
        else:
            self.mqtt_client.publish(comando)
            self.mover_robo(comando)
        self.lista_comandos.insert(tk.END, f"[{comando}]")  # Insert command in the list
        print(f"Comando enviado: {comando}")

 
    def carregar_ultima_posicao(self):
        caminho_arquivo = "python/graphic_method/position.json"
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    dados = json.load(f)
                    return (dados["linha"], dados["coluna"], dados["orientacao"], dados["passos"])
                except json.JSONDecodeError:
                    pass
        # Se o arquivo não existir ou houver um erro, inicializar no centro, virado para o norte
        return (self.linhas // 2, self.colunas // 2, "N", 0)

    def mover_robo(self, comando):
        linha, coluna, orientacao, passos = self.estado_robo

        if comando.startswith("W"):  # Comando de Espera
            segundos = int(self.spin_wait.get())  # Get time from GUI spinbox
            self.label_coordenadas.config(text=f"Esperando {segundos} segundos...")

            # Pause without freezing the interface
            self.root.after(segundos * 1000, lambda: self.label_coordenadas.config(
                text=f"Coordenadas: ({linha}, {coluna})"))
            return  # Don't continue movement if it's a waiting command

        # Verificar sensores
        sensores = verificar_sensores(self.matriz, linha, coluna, orientacao)

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

        # Atualizar a exibição das coordenadas
        self.label_coordenadas.config(text=f"Coordenadas: ({linha}, {coluna})")

        # Salvar coordenadas no arquivo JSON
        self.salvar_coordenadas((linha, coluna, orientacao, passos + 1))

        # Desenhar o ambiente e o robô
        desenhar_ambiente(self.ax, self.canvas, self.matriz, (linha, coluna))

    def iniciar_gravacao(self):
        self.comandos = []
        self.lista_comandos.delete(0, tk.END)  # Clear the list
        print("Gravação de rota iniciada.")


    def salvar_rota(self):
        caminho_arquivo = "python/graphic_method/rotas_salvas.json"
        rota_nome = f"Rota {len(self.lista_rotas.get(0, tk.END)) + 1}"
        rota = {
            "nome": rota_nome,
            "comandos": self.comandos,
            "orientacao_inicial": self.estado_robo[2]
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
        self.lista_rotas_sequencia.insert(tk.END, rota_nome)

        # Limpar a lista de comandos após salvar a rota
        self.comandos = []

    def salvar_coordenadas(self, estado_robo):
        caminho_arquivo = "python/graphic_method/position.json"
        dados = {
            "linha": estado_robo[0],
            "coluna": estado_robo[1],
            "orientacao": estado_robo[2],
            "passos": estado_robo[3]
        }
        with open(caminho_arquivo, "w") as f:
            json.dump(dados, f, indent=4)
        print(f"Coordenadas salvas em {caminho_arquivo}")

    def inserir_pausa(self):
        segundos = int(self.spin_wait.get())  # Get time from spinbox
        comando = f"W{segundos}"  # Create the command like "W5" for 5 seconds
        self.comandos.append(comando)  # Add to command list
        self.label_coordenadas.config(text=f"Pausa de {segundos} segundos inserida")
        self.lista_comandos.insert(tk.END, f"[{comando}]")  # Add to command listbox
        print(f"Pausa de {segundos} segundos inserida na rota.")  # Show in console

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
                    self.lista_rotas_sequencia.insert(tk.END, rota["nome"])

    def adicionar_sequencia(self):
        selecionados = self.lista_rotas_sequencia.curselection()
        for i in selecionados:
            rota_nome = self.lista_rotas_sequencia.get(i)
            self.lista_sequencia_atual.insert(tk.END, rota_nome)
        print(f"Rotas adicionadas à sequência: {[self.lista_rotas_sequencia.get(i) for i in selecionados]}")

    def remover_sequencia(self):
        selecionados = self.lista_sequencia_atual.curselection()
        for i in reversed(selecionados):
            self.lista_sequencia_atual.delete(i)
        print(f"Rotas removidas da sequência: {[self.lista_sequencia_atual.get(i) for i in selecionados]}")

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

            # Criar JSON com a rota completa
            payload = json.dumps({
                "rota": comandos, 
                "id": "robo_01"  # ID opcional para identificar o robô
            })

            # Enviar para o ESP32 via MQTT
            self.mqtt_client.publish("robo_gaveteiro/comandos", payload)
            print(f"📡 Rota enviada para o robô: {rota_nome}")
            print(f"📜 JSON Enviado: {payload}")

    def executar_comandos(self, comandos):
        if comandos:
            comando = comandos.pop(0)
            if comando.startswith("W"):  # Comando de espera
                segundos = int(comando[1:])
                self.root.after(segundos * 1000, lambda: self.executar_comandos(comandos))
            else:
                self.mover_robo(comando)
                self.root.after(500, lambda: self.executar_comandos(comandos))  # Atraso de 500ms entre os comandos

    def criar_sequencia(self):
        selecionados = self.lista_rotas_sequencia.curselection()
        if selecionados:
            self.sequencia = [self.lista_rotas_sequencia.get(i) for i in selecionados]
            print(f"Sequência criada: {self.sequencia}")

    def executar_sequencia(self):
        sequencia = list(self.lista_sequencia_atual.get(0, tk.END))
        if sequencia:
            self.executar_rotas_sequencia(sequencia)

    def executar_rotas_sequencia(self, sequencia):
        if sequencia:
            rota_nome = sequencia.pop(0)
            caminho_arquivo = "python/graphic_method/rotas_salvas.json"
            with open(caminho_arquivo, "r") as f:
                dados = json.load(f)
            for r in dados:
                if r["nome"] == rota_nome:
                    comandos = r["comandos"]
                    orientacao_inicial = r.get("orientacao_inicial", "N")
                    break
            self.executar_comandos_sequencia(comandos, sequencia, orientacao_inicial)
            
    def ajustar_orientacao(self, orientacao_inicial):
        orientacao_atual = self.estado_robo[2]
        while orientacao_atual != orientacao_inicial:
                self.mover_robo("D")
                orientacao_atual = self.estado_robo[2]
            
    def executar_comandos_sequencia(self, comandos, sequencia, orientacao_inicial):
        if comandos:
            comando = comandos.pop(0)
            if comando.startswith("W"):  # Comando de espera
                segundos = int(comando[1:])
                self.root.after(segundos * 1000, lambda: self.executar_comandos_sequencia(comandos, sequencia, orientacao_inicial))
            else:
                self.mover_robo(comando)
                self.root.after(500, lambda: self.executar_comandos_sequencia(comandos, sequencia, orientacao_inicial))
        else:
            self.ajustar_orientacao(orientacao_inicial)
            if self.loop_var.get() == 1:
                self.executar_rotas_sequencia(self.sequencia.copy())
            else:
                self.executar_rotas_sequencia(sequencia)

    def retornar_inicio(self):
        comandos_retorno = inverter_comandos(self.comandos, self.estado_robo[2])
        
        for comando in comandos_retorno:
            self.lista_comandos.insert(tk.END, f"[{comando}]")  # Show each command in the list
            self.lista_comandos.yview(tk.END)  # Scroll the list automatically
        
        print("Executando retorno ao início...")
        self.executar_comandos(comandos_retorno)

    def limpar_memoria(self):
        # Deletar arquivos de rotas e coordenadas
        if os.path.exists("python/graphic_method/rotas_salvas.json"):
            os.remove("python/graphic_method/rotas_salvas.json")
        if os.path.exists("python/graphic_method/position.json"):
            os.remove("python/graphic_method/position.json")

        # Reposicionar o robô no centro, orientado ao norte
        self.estado_robo = (self.linhas // 2, self.colunas // 2, "N", 0)
        self.comandos = []
        self.label_coordenadas.config(text=f"Coordenadas: ({self.estado_robo[0]}, {self.estado_robo[1]})")
        self.lista_rotas.delete(0, tk.END)
        self.lista_rotas_sequencia.delete(0, tk.END)
        self.lista_sequencia_atual.delete(0, tk.END)
        desenhar_ambiente(self.ax, self.canvas, self.matriz, (self.linhas // 2, self.colunas // 2))
        print("Memória limpa e robô reposicionado.")

    def on_closing(self):
        if tk.messagebox.askokcancel("Sair", "Tem certeza que deseja fechar o programa?"):
            self.mqtt_client.disconnect()
            self.root.destroy()
            self.root.quit()  # Stop all Tkinter threads
            print("Janela fechada e programa finalizado.")
