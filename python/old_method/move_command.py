import numpy as np
import wifi_server_conect as wsc
import ambiente_grid as ag
import time as t

# Atualiza a posição do robô na matriz do ambiente
def update_environment(environment, robot_position):
    x, y = robot_position
    environment[x][y] = 1

# Rotação do robô
def rotate_robot(rotation, command):
    if command == "E":
        rotation += 1
        if rotation > 3:
            rotation = 0
    elif command == "D":
        rotation -= 1
        if rotation < 0:
            rotation = 3
    return rotation

# Movimento do robô
def move_robot(current_position, rotation):
    x, y = current_position
    if rotation == 0:
        y -= 1
    elif rotation == 1:
        x += 1
    elif rotation == 2:
        y += 1
    elif rotation == 3:
        x -= 1
    return (x, y)

# Envia o comando para o meio físico e processa a lógica local
def send_command(command, canvas, figure, client_socket, environment):
    if client_socket:
        client_socket.sendall(command.encode("utf-8"))
        t.sleep(2) # Espera 2 segundos para parar o robô em outro quadrado
        client_socket.sendall("T".encode("utf-8")) # Envia comando de parada
        print(f"Comando enviado: {command}")
        process_command(command, canvas, figure, environment)
    else:
        print("Nenhum cliente conectado.")

# Processa o comando
def process_command(command, canvas, figure, environment):
    global rotation, robot_position
    if command in ["E", "D"]:
        rotation = rotate_robot(rotation, command)
    elif command == "F":
        robot_position = move_robot(robot_position, rotation)
        update_environment(environment, robot_position)
    print(f"Posição do robô: {robot_position}")
    print(environment)
    ag.draw_environment(canvas, figure, environment)
