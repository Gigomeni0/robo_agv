import socket
import threading

class WifiServer:
    def __init__(self, host="0.0.0.0", port=65432):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.client_socket = None
        self.stop_server = False
        print(f"Servidor escutando em {self.host}:{self.port}")

    def start_server(self):
        self.stop_server = False
        threading.Thread(target=self._client_thread).start()

    def stop_server_func(self):
        self.stop_server = True
        if self.client_socket:
            self.client_socket.close()
        self.server_socket.close()

    def _client_thread(self):
        while not self.stop_server:
            print("Aguardando conexão...")
            self.server_socket.settimeout(5.0)  # Tempo limite de 5 segundos
            try:
                self.client_socket, client_address = self.server_socket.accept()
                print(f"Conexão estabelecida com {client_address}")
                
                try:
                    while not self.stop_server:
                        # Recebe dados da ESP32
                        data = self.client_socket.recv(1024)
                        if not data:
                            break
                        mensagem = data.decode("utf-8")
                        print(f"Mensagem recebida: {mensagem}")
                except Exception as e:
                    print(f"Erro na conexão: {e}")
                finally:
                    self.client_socket.close()
                    self.client_socket = None
                    print("Cliente desconectado.")
            except socket.timeout:
                continue
