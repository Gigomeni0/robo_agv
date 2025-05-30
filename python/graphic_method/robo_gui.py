import os
import json
import tkinter as tk
from tkinter import ttk
import subprocess
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mqtt_manager import MQTTManager
#from mqtt_manager import porta_em_uso
from robo_controller import RoboController
from utils import desenhar_ambiente, inverter_comandos
import socket
from paho.mqtt import client as mqtt
import tkinter.messagebox

class RoboGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Manual do Robô")

        # Definindo status do robô
        self.executando_rota = False
        self.pausado_por_obstaculo = False
        
        # Criando a matriz do ambiente (10x10)
        self.matriz = [[0] * 30 for _ in range(30)]
        self.estado_robo = self.carregar_ultima_posicao()  # Posição inicial

        # Carregar a base do arquivo JSON
        self.base = self.carregar_base()

        # Criar controlador do robô
        self.robo_controller = RoboController(self.matriz, self.estado_robo)

        # Criar cliente MQTT
        self.mqtt_client = MQTTManager(
            broker=self.obter_ip_local(),
            port=1883,
            topics=["robo_gaveteiro/comandos", "robo_gaveteiro/status", "robo_gaveteiro/plotter"],
            on_message_callback=self.on_mqtt_message
        )
        self.mqtt_client.connect()

        # Criando interface gráfica
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=1, fill='both')
        
        self.frame_controles = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_controles, text='Manual')
        
        # Aba Automação
        self.frame_automacao = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_automacao, text='Automação')

        
        self.frame_rotas = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_rotas, text='Rotas Salvas')
        self.frame_sequencia = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_sequencia, text='Sequência de Rotas')
        
        # Criar frame para configuração de servidor MQTT local (opcional)
        self.frame_mqtt = ttk.Frame(self.frame_controles)
        self.frame_mqtt.pack(side=tk.LEFT, padx=10, pady=10)    
        self.frame_controles_lateral = ttk.Frame(self.frame_controles)
        self.frame_controles_lateral.pack(side=tk.LEFT, padx=10, pady=10)

        # Configurar o layout do gráfico
        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)  # Reduzir margens
        self.ax.set_aspect('equal')  # Garantir que o gráfico seja quadrado
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_controles)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Widgets da aba Controles ---
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
        
        # Botão para simular obstáculo
        self.btn_simular_obstaculo = ttk.Button(self.frame_controles_lateral, text="Simular Obstáculo", command=self.simular_obstaculo)
        self.btn_simular_obstaculo.grid(row=11, column=0, columnspan=3, pady=10)
        
        # Botão para simular caminho livre
        self.btn_simular_livre = ttk.Button(self.frame_controles_lateral, text="Simular Livre", command=self.simular_livre)
        self.btn_simular_livre.grid(row=12, column=0, columnspan=3, pady=10)    
        
        #Grafico locomoção 
        self.canvas_automacao = FigureCanvasTkAgg(self.fig, master=self.frame_automacao)
        self.canvas_automacao.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)


        # --- Widgets da aba Automação ---
        # Exemplo: botões e listas para gravação, salvar, executar rotas, etc.
        self.btn_iniciar_gravacao = ttk.Button(self.frame_automacao, text="Iniciar Gravação", command=self.iniciar_gravacao)
        self.btn_iniciar_gravacao.pack(pady=5)
        self.btn_salvar_rota = ttk.Button(self.frame_automacao, text="Salvar Rota", command=self.salvar_rota)
        self.btn_salvar_rota.pack(pady=5)
        self.btn_executar_rota = ttk.Button(self.frame_automacao, text="Executar Rota", command=self.executar_rota)
        self.btn_executar_rota.pack(pady=5)
        self.btn_retornar_base = ttk.Button(self.frame_automacao, text="Voltar à Base", command=self.retornar_inicio)
        self.btn_retornar_base.pack(pady=5)
        # Lista de rotas salvas
        self.lista_rotas = tk.Listbox(self.frame_automacao)
        self.lista_rotas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.btn_executar_rota = ttk.Button(self.frame_automacao, text="Executar Rota", command=self.executar_rota)
        self.btn_executar_rota.pack(pady=10)

        # --- Widgets da aba Sequência de Rotas ---
        # Exemplo: botões e listas para executar sequências de rotas, etc.
        # Adicionar botão para definir a base
        self.btn_definir_base = ttk.Button(self.frame_controles_lateral, text="Definir Base", command=self.definir_base)
        self.btn_definir_base.grid(row=5, column=0, pady=5)

        # Exibir a base atual
        self.label_base = ttk.Label(self.frame_controles_lateral, text="Base: Não definida")
        self.label_base.grid(row=6, column=0, columnspan=3, pady=5)

        # Configuração de tempo de espera
        self.label_wait = ttk.Label(self.frame_controles_lateral, text="Tempo de Espera (s):")
        self.label_wait.grid(row=6, column=0, pady=5)

        # Exibir status do MQTT
        self.label_status_mqtt = ttk.Label(self.frame_controles_lateral, text="Status MQTT: Desconectado", foreground="red")
        self.label_status_mqtt.grid(row=7, column=0, columnspan=3, pady=5)  
        # ...após outros botões na self.frame_controles_lateral...
        self.btn_bluetooth = ttk.Button(self.frame_controles_lateral, text="Ativar Bluetooth", command=self.ativar_bluetooth)
        self.btn_bluetooth.grid(row=10, column=0, columnspan=3, pady=10)
        
        # Caixa de seleção para escolher o tempo de espera
        self.spin_wait = ttk.Spinbox(self.frame_controles_lateral, from_=1, to=30, width=5)
        self.spin_wait.grid(row=6, column=1, pady=5)
        self.spin_wait.set(1)
        
        # Lista de comandos
        self.lista_comandos = tk.Listbox(self.frame_controles_lateral, height=10)
        self.lista_comandos.grid(row=8, column=0, columnspan=3, pady=5)
                
        # Inicializar o ambiente
        desenhar_ambiente(self.ax, self.canvas, self.matriz, self.estado_robo[:2])

        # Capturar evento de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Carregar rotas salvas
        self.carregar_rotas_salvas()

        # Iniciar servidor MQTT local
        self.iniciar_servidor_mqtt()

        # Criar aba para visualizar informações do servidor MQTT
        self.frame_servidor_mqtt = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_servidor_mqtt, text='Servidor MQTT')

        self.label_ip = ttk.Label(self.frame_servidor_mqtt, text=f"Endereço IP: {self.ip_local}")
        self.label_ip.pack(pady=5)

        self.label_porta = ttk.Label(self.frame_servidor_mqtt, text=f"Porta: {self.porta_mqtt}")
        self.label_porta.pack(pady=5)

        self.label_topicos = ttk.Label(self.frame_servidor_mqtt, text="Tópicos MQTT:")
        self.label_topicos.pack(pady=5)

        self.lista_topicos = tk.Listbox(self.frame_servidor_mqtt, height=10)
        self.lista_topicos.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Atualizar tópicos recebidos
        self.mqtt_local_client.on_message = self.on_local_mqtt_message
        self.mqtt_local_client.subscribe("#")  # Inscrever-se em todos os tópicos

        # Botão para resetar tudo
        self.btn_resetar = ttk.Button(self.frame_controles_lateral, text="Resetar Tudo", command=self.confirmar_resetar)
        self.btn_resetar.grid(row=9, column=0, columnspan=3, pady=10)

        # Aba Plotter para calibragem de pulsos
        self.frame_plotter = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_plotter, text='Plotter')
        self.listbox_plotter = tk.Listbox(self.frame_plotter, height=10)
        self.listbox_plotter.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def porta_em_uso(self, porta):
        """Verifica se a porta está em uso."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", porta)) == 0
        
    def atualizar_status_mqtt(self):
        """Atualiza o status do cliente MQTT na interface."""
        if  self.mqtt_client.client.is_connected():
                self.label_status_mqtt.config(text="Status MQTT: Conectado", foreground="green")
        else:
            self.label_status_mqtt.config(text="Status MQTT: Desconectado", foreground="red")
    def carregar_ultima_posicao(self):
        """Carrega a última posição do robô a partir do arquivo JSON."""
        caminho_arquivo = os.path.join(os.path.dirname(__file__), "position.json")
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    raw = f.read().splitlines()
                    raw = [l for l in raw if not l.strip().startswith('//')]
                    dados = json.loads("\n".join(raw))
                    return (dados["linha"], dados["coluna"], dados["orientacao"], dados["passos"])
                except json.JSONDecodeError:
                    pass
        # Se o arquivo não existir ou houver um erro, inicializar no centro, virado para o norte
        return (self.linhas // 2, self.colunas // 2, "N", 0)

    def carregar_base(self):
        """Carrega a base salva no arquivo JSON."""
        caminho_arquivo = os.path.join(os.path.dirname(__file__), "positions.json")
        try:
            with open(caminho_arquivo, "r") as f:
                raw = f.read().splitlines()
                raw = [l for l in raw if not l.strip().startswith('//')]
                dados = json.loads("\n".join(raw))
                if "base" in dados:
                    print(f"📂 Base carregada: {dados['base']}")
                    return dados["base"]
        except (FileNotFoundError, json.JSONDecodeError):
            print("⚠️ Nenhuma base encontrada no arquivo JSON.")
        return None
    
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
        """Envia um comando MQTT para a ESP32."""
        try:
            self.mqtt_local_client.publish("robo_gaveteiro/comandos", comando)
            print(f"✅ Comando '{comando}' enviado para o tópico 'robo_gaveteiro/comandos'")
            self.lista_comandos.insert(tk.END, f"[{comando}]")
            self.estado_robo = self.robo_controller.mover_robo(comando)

            # Salvar a posição atual do robô
            self.salvar_posicao_atual()
            self.atualizar_interface()
        except Exception as e:
            print(f"❌ Erro ao enviar comando: {e}")
        # Salvar a posição atual do robô
        self.salvar_posicao_atual()
        self.atualizar_interface()
    
    def atualizar_interface(self):
        """Atualiza a interface gráfica com a posição atual do robô."""
        desenhar_ambiente(self.ax, self.canvas, self.matriz, self.estado_robo, getattr(self, "base", None))
        self.canvas.draw()
        self.canvas_automacao.draw()
        
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

        # Verificar se a base está definida
        if not hasattr(self, "base"):
            print("⚠️ Base não definida. Defina a base antes de salvar uma rota.")
            return

        # Verificar se o robô está na base
        if (self.estado_robo[0] != self.base["linha"] or
            self.estado_robo[1] != self.base["coluna"] or
            self.estado_robo[2] != self.base["orientacao"]):
            print("⚠️ O robô não está na base. Não é possível salvar a rota.")
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
    # Funçao para executar rota selecionada
    def executar_rota(self):
        # Só executar se estiver na base e orientado para Norte
        if not self.base or self.estado_robo[2] != 'N' or (self.estado_robo[0] != self.base['linha'] or self.estado_robo[1] != self.base['coluna']):
            print("⚠️ Só é possível executar rotas quando o robô estiver na base e orientado para Norte (N).")
            return
        selecionado = self.lista_rotas.curselection()
        if selecionado:
            rota_nome = self.lista_rotas.get(selecionado)
            print(f"🔄 Executando rota: {rota_nome}")
            comandos = self.robo_controller.carregar_rotas(rota_nome)
            print(f"📜 Comandos carregados: {comandos}")
            self.executar_comandos_sequencialmente(comandos)
        else:
            print("⚠️ Nenhuma rota selecionada.")

    def executar_comandos_sequencialmente(self, comandos, idx=0):
        # Salva o estado para possível retomada
        self.comandos_em_execucao = comandos
        self.idx_parado = idx

        if self.pausado_por_obstaculo:
            print("Execução pausada por obstáculo.")
            return
        if idx < len(comandos):
            comando = comandos[idx]
            self.enviar_comando(comando)
            self.executando_rota = True
            self.root.after(500, lambda: self.executar_comandos_sequencialmente(comandos, idx+1))
        else:
            self.executando_rota = False
            print("✅ Execução da rota concluída.")
    
    def simular_obstaculo(self):
        """Simula o recebimento de um obstáculo pelo MQTT."""
        class DummyMsg:
            topic = "robo_gaveteiro/status"
            payload = b"obstaculoFrente"
        self.on_mqtt_message(None, None, DummyMsg())
    
    def simular_livre(self):
        """Simula o recebimento da mensagem 'livre' pelo MQTT."""
        class DummyMsg:
            topic = "robo_gaveteiro/status"
            payload = b"livre"
        self.on_mqtt_message(None, None, DummyMsg())
        
    # Função de callback para mensagens recebidas do MQTT
    def on_mqtt_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print(f"📡 Mensagem recebida: {msg.topic} {payload}")

        if msg.topic == "robo_gaveteiro/status":
            if payload == "obstaculoFrente":
                print("⚠️ Obstáculo detectado! Robô parado.")
                # Marcar obstáculo à frente do robô
                linha, coluna, orientacao, _ = self.estado_robo
                if orientacao == "N":
                    linha_obs, coluna_obs = linha - 1, coluna
                elif orientacao == "S":
                    linha_obs, coluna_obs = linha + 1, coluna
                elif orientacao == "E":
                    linha_obs, coluna_obs = linha, coluna + 1
                elif orientacao == "W":
                    linha_obs, coluna_obs = linha, coluna - 1
                # Verifica se está dentro dos limites
                if 0 <= linha_obs < len(self.matriz) and 0 <= coluna_obs < len(self.matriz[0]):
                    self.matriz[linha_obs][coluna_obs] = 1  # 1 = obstáculo
                    self.atualizar_interface()
                
                
                    
                self.pausado_por_obstaculo = True
                self.executando_rota = False
                # Exibir aviso visual
                tkinter.messagebox.showwarning("Obstáculo detectado", "O robô parou devido a um obstáculo!\nRemova o obstáculo para continuar.")
                # (Opcional) Emitir som
                self.root.bell()
                return  # Não continue executando comandos
            elif payload == "obstaculoDireita":
                print("⚠️ Obstáculo detectado à direita!")
                linha, coluna, orientacao, _ = self.estado_robo
                # calcula posição à direita
                if orientacao == 'N': dr, dc = 0, 1
                elif orientacao == 'E': dr, dc = 1, 0
                elif orientacao == 'S': dr, dc = 0, -1
                else: dr, dc = -1, 0  # W
                r, c = linha+dr, coluna+dc
                if 0 <= r < len(self.matriz) and 0 <= c < len(self.matriz[0]):
                    self.matriz[r][c] = 1
                    self.atualizar_interface()
                return
            elif payload == "obstaculoEsquerda":
                print("⚠️ Obstáculo detectado à esquerda!")
                linha, coluna, orientacao, _ = self.estado_robo
                # calcula posição à esquerda
                if orientacao == 'N': dr, dc = 0, -1
                elif orientacao == 'E': dr, dc = -1, 0
                elif orientacao == 'S': dr, dc = 0, 1
                else: dr, dc = 1, 0  # W
                r, c = linha+dr, coluna+dc
                if 0 <= r < len(self.matriz) and 0 <= c < len(self.matriz[0]):
                    self.matriz[r][c] = 1
                    self.atualizar_interface()
                return
            elif payload == "livre":
                print("✅ Caminho livre! Robô pode continuar.")
                # Remove obstáculo à frente do robô
                linha, coluna, orientacao, _ = self.estado_robo
                if orientacao == "N":
                    linha_obs, coluna_obs = linha - 1, coluna
                elif orientacao == "S":
                    linha_obs, coluna_obs = linha + 1, coluna
                elif orientacao == "E":
                    linha_obs, coluna_obs = linha, coluna + 1
                elif orientacao == "W":
                    linha_obs, coluna_obs = linha, coluna - 1
                if 0 <= linha_obs < len(self.matriz) and 0 <= coluna_obs < len(self.matriz[0]):
                    self.matriz[linha_obs][coluna_obs] = 0  # Remove obstáculo
                    self.atualizar_interface()
                if self.pausado_por_obstaculo:
                    self.pausado_por_obstaculo = False
                    # Retoma a execução do ponto parado
                    if hasattr(self, 'comandos_em_execucao') and hasattr(self, 'idx_parado'):
                        self.executar_comandos_sequencialmente(self.comandos_em_execucao, self.idx_parado)
                return
            
            else:
                print(f"📍 Novo status do robô: {payload}")
                try:
                    self.estado_robo = json.loads(payload)
                    self.atualizar_interface()
                except Exception:
                    pass
        elif msg.topic == "robo_gaveteiro/comandos":
            print(f"🔄 Comando recebido: {payload}")
        elif msg.topic == "robo_gaveteiro/plotter":
            print(f"📊 Pulsos recebidos: {payload}")
            self.listbox_plotter.insert(tk.END, payload)
            return

    # Função para definir a base do robô
    def definir_base(self):
        """Define a posição e orientação atual do robô como a base e salva no arquivo JSON."""
        self.base = {
            "linha": self.estado_robo[0],
            "coluna": self.estado_robo[1],
            "orientacao": self.estado_robo[2]
        }
        self.label_base.config(text=f"Base: ({self.base['linha']}, {self.base['coluna']}, {self.base['orientacao']})")
        print(f"📍 Base definida: {self.base}")

        # Salvar a base no arquivo JSON
        caminho_arquivo = os.path.join(os.path.dirname(__file__), "positions.json")
        try:
            with open(caminho_arquivo, "r") as f:
                dados = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            dados = {}

        dados["base"] = self.base

        with open(caminho_arquivo, "w") as f:
            json.dump(dados, f, indent=4)

        # Redesenhar o ambiente com a base
        desenhar_ambiente(self.ax, self.canvas, self.matriz, self.estado_robo, self.base)
   
   
   # Função de fechamento da janela
    def on_closing(self):
        self.mqtt_client.disconnect()
        self.root.destroy()
        self.root.quit()
    # Iniciar o loop do cliente MQTT E as funções relacionadas ao servidor MQTT local
    def obter_ip_local(self):
        """Obtém o endereço IP local da máquina."""
        try:
            # Conecta a um endereço externo para descobrir o IP local
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))  # Conexão com o DNS do Google
                return s.getsockname()[0]  # Retorna o IP local
        except Exception as e:
            print(f"⚠️ Erro ao obter o IP local: {e}")
        return "127.0.0.1"  # Retorna localhost como fallback 
    
    def iniciar_servidor_mqtt(self):
        """Inicia um servidor MQTT local usando um arquivo de configuração."""
        self.ip_local = self.obter_ip_local()  # Obtém o IP local dinamicamente
        self.porta_mqtt = 1883
        self.mqtt_local_client = mqtt.Client()
        self.mqtt_local_client.on_message = self.on_local_mqtt_message
        self.mqtt_local_client.on_connect = lambda client, userdata, flags, rc: self.atualizar_status_mqtt()
        self.mqtt_local_client.on_disconnect = lambda client, userdata, rc: self.atualizar_status_mqtt()

        self.mqtt_local_client.connect(self.ip_local, self.porta_mqtt)
        self.mqtt_local_client.loop_start()
        # Atualize o status logo após tentar conectar
        self.atualizar_status_mqtt()

        def iniciar_broker():
            # Substitua o caminho para o arquivo mqtt.conf pelo caminho correto no seu sistema
            caminho_config = "C:\\Program Files\\mosquitto\\mosquitto.conf"
            subprocess.Popen(["mosquitto", "-c", caminho_config])

        # Verifica se a porta está em uso
        if self.porta_em_uso(self.porta_mqtt):
            print(f"⚠️ O servidor MQTT já está em execução em {self.ip_local}:{self.porta_mqtt}.")
        else:
            try:
                iniciar_broker()
                print(f"Servidor MQTT iniciado em {self.ip_local}:{self.porta_mqtt}")
            except FileNotFoundError:
                print("⚠️ Mosquitto não encontrado. Certifique-se de que está instalado e no PATH.")

        # Configurar cliente MQTT local
        self.mqtt_local_client = mqtt.Client()
        self.mqtt_local_client.on_message = self.on_local_mqtt_message
        self.mqtt_local_client.connect(self.ip_local, self.porta_mqtt)
        self.mqtt_local_client.loop_start()

    def on_local_mqtt_message(self, client, userdata, msg):
        """Callback para mensagens recebidas no servidor MQTT local."""
        topico = msg.topic
        payload = msg.payload.decode()
        print(f"📡 Mensagem recebida no servidor local: {topico} -> {payload}")
        # Atualizar a interface gráfica, se necessário
        self.lista_topicos.insert(tk.END, f"{topico}: {payload}")

    # Definir o comando para ativar o Bluetooth
    def ativar_bluetooth(self):
        """Envia comando para ESP entrar em modo Bluetooth."""
        try:
            self.mqtt_local_client.publish("robo_gaveteiro/status", "bluetooth")
            print("✅ Comando 'bluetooth' enviado para o tópico 'robo_gaveteiro/status'")
        except Exception as e:
            print(f"❌ Erro ao enviar comando bluetooth: {e}")

    def confirmar_resetar(self):
        """Exibe uma caixa de confirmação antes de resetar tudo."""
        resposta = tkinter.messagebox.askyesno(
            "Confirmação",
            "Tem certeza que deseja apagar todas as rotas, histórico e reiniciar o robô no centro?"
        )
        if resposta:
            self.resetar_robo_e_historico()

    def resetar_robo_e_historico(self):
        """Limpa rotas, histórico e reinicia o robô no centro."""
        # Limpar rotas salvas
        caminho_rotas = os.path.join(os.path.dirname(__file__), "rotas_salvas.json")
        if os.path.exists(caminho_rotas):
            with open(caminho_rotas, "w") as f:
                json.dump([], f, indent=4)
        self.lista_rotas.delete(0, tk.END)

        # Limpar comandos e histórico do robô
        self.robo_controller.comandos = []
        self.lista_comandos.delete(0, tk.END)

        # Reiniciar posição do robô no centro
        linhas = len(self.matriz)
        colunas = len(self.matriz[0])
        self.estado_robo = (linhas // 2, colunas // 2, "N", 0)
        self.robo_controller.estado_robo = self.estado_robo
        self.salvar_posicao_atual()
        self.base = None
        self.label_base.config(text="Base: Não definida")

        # Atualizar interface
        self.atualizar_interface()
        tkinter.messagebox.showinfo("Reset", "Sistema reiniciado com sucesso!")

