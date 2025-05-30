import json
import os
from utils import verificar_sensores, inverter_comandos

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
            if orientacao == "N": 
                linha -= 1
            elif orientacao == "E": 
                coluna += 1
            elif orientacao == "S": 
                linha += 1
            elif orientacao == "W": 
                coluna -= 1
                
        elif comando == "E":
            orientacao = {"N": "W", "W": "S", "S": "E", "E": "N"}[orientacao]
        elif comando == "D":
            orientacao = {"N": "E", "E": "S", "S": "W", "W": "N"}[orientacao]

        self.estado_robo = (linha, coluna, orientacao, passos + 1)
        self.comandos.append(comando)
        return self.estado_robo

    def simular_movimento(self, comandos):
        """Simula a execução dos comandos e retorna a posição final do robô."""
        linha, coluna, orientacao, _ = self.estado_robo
        
        for comando in comandos:
            if comando == "F":
                if orientacao == "N":
                    linha -= 1
                elif orientacao == "E":
                    coluna += 1
                elif orientacao == "S":
                    linha += 1
                elif orientacao == "W":
                    coluna -= 1
            elif comando == "E":
                orientacao = {"N": "W", "W": "S", "S": "E", "E": "N"}[orientacao]
            elif comando == "D":
                orientacao = {"N": "E", "E": "S", "S": "W", "W": "N"}[orientacao]
                
        return (linha, coluna)


    def iniciar_gravacao(self):
        self.comandos = []

    def salvar_rota(self, caminho_arquivo, nome_rota):
        nova_rota = {
            "nome": nome_rota,
            "comandos": self.comandos,
            "orientacao_inicial": self.estado_robo[2]
        }
        rotas = []
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r") as f:
                try:
                    rotas = json.load(f)
                except json.JSONDecodeError:
                    rotas = []
        rotas.append(nova_rota)
        with open(caminho_arquivo, "w") as f:
            json.dump(rotas, f, indent=4)


    def carregar_rotas(self, rota_nome):
            caminho_arquivo = os.path.join(os.path.dirname(__file__), "rotas_salvas.json")
            if os.path.exists(caminho_arquivo):
                with open(caminho_arquivo, "r") as f:
                    try:
                        dados = json.load(f)
                        for rota in dados:
                            if rota["nome"] == rota_nome:
                                return rota["comandos"]
                    except json.JSONDecodeError:
                        print("Erro ao decodificar o arquivo JSON.")
            return []

    def executar_comandos(self, comandos):
        for comando in comandos:
            self.mover_robo(comando)

    def inverter_rota(self):
        return inverter_comandos(self.comandos, self.estado_robo[2])
    
    def get_orientacao_final(self):
        """Retorna a orientação final após a execução da rota."""
        return self.estado_robo[2]

