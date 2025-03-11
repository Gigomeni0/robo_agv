import json
from utils import verificar_sensores, desenhar_ambiente, inverter_comandos

class RoboController:
    def __init__(self, matriz, estado_robo):
        self.matriz = matriz
        self.estado_robo = estado_robo
        self.comandos = []

    def mover_robo(self, comando):
        linha, coluna, orientacao, passos = self.estado_robo

        if comando.startswith("W"):  # Comando de Espera
            return f"Esperando {int(comando[1:])} segundos..."

        sensores = verificar_sensores(self.matriz, linha, coluna, orientacao)

        if comando == "F" and sensores[0] == 1:
            if orientacao == "N": linha -= 1
            elif orientacao == "E": coluna += 1
            elif orientacao == "S": linha += 1
            elif orientacao == "W": coluna -= 1
        elif comando == "E":
            orientacao = {"N": "W", "W": "S", "S": "E", "E": "N"}[orientacao]
        elif comando == "D":
            orientacao = {"N": "E", "E": "S", "S": "W", "W": "N"}[orientacao]

        self.estado_robo = (linha, coluna, orientacao, passos + 1)
        self.comandos.append(comando)
        return self.estado_robo

    def iniciar_gravacao(self):
        self.comandos = []

    def salvar_rota(self, caminho_arquivo):
        rota = {"comandos": self.comandos, "orientacao_inicial": self.estado_robo[2]}
        with open(caminho_arquivo, "w") as f:
            json.dump(rota, f, indent=4)

    def carregar_rotas(self, caminho_arquivo):
        if not os.path.exists(caminho_arquivo):
            return []
        with open(caminho_arquivo, "r") as f:
            return json.load(f)

    def executar_comandos(self, comandos):
        for comando in comandos:
            self.mover_robo(comando)

    def inverter_rota(self):
        return inverter_comandos(self.comandos, self.estado_robo[2])
