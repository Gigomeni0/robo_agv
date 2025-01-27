import tkinter as tk
from tkinter import ttk
import move_command as mc
import wifi_server_conect as wsc
import ttkbootstrap as ttk
import ambiente_grid as ag
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#inicializa o servidor wifi
server = wsc.WifiServer()
server.start_server()

#inicializa o ambiente GUI
window = ttk.Window(themename="yeti")
window.title("Controle do Robô")
window.geometry("1000x800")
title_label = ttk.Label(master= window, text="Controle do Robô", font = 'Calibri 24 bold')
title_label.pack()

#Abas de acesso ao controle manual e automático com mapa 20x20 do robô
tab_control = ttk.Notebook(window)
tab_control.pack(expand=1, fill='both')
tab1 = ttk.Frame(tab_control)
tab_control.add(tab1, text='Controle Manual')

commands_frame = ttk.Frame(master= tab1)
commands_frame.pack(padx=10, pady=10)

# Controle manual
btn_Avanco = ttk.Button(master=commands_frame, text="Frente", command=lambda: mc.send_command("F", canvas, figure, server.client_socket, environment)).pack()
btn_Right_Rotate = ttk.Button(master=commands_frame, text="Giro Horário", command=lambda: mc.send_command("D", canvas, figure, server.client_socket, environment)).pack()
btn_Left_Rotate = ttk.Button(master= commands_frame, text="Giro Anti-horário", command=lambda: mc.send_command("E", canvas, figure, server.client_socket, environment)).pack()
btn_Trás = ttk.Button(master=commands_frame, text="Parada", command=lambda: mc.send_command("T", canvas, figure, server.client_socket, environment)).pack()

tab2 = ttk.Frame(tab_control)
tab_control.add(tab2, text='Controle Automático')

# Criação da figura do Matplotlib
figure = plt.figure(figsize=(5, 5))
canvas = FigureCanvasTkAgg(figure, master=tab2)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side= tk.TOP, fill=tk.NONE, expand=True)

# Botões de comando
frame = tk.Frame(tab2)
frame.pack(side=tk.BOTTOM)

def send_forward():
    mc.send_command("F", canvas, figure)

def send_left():
    mc.send_command("E", canvas, figure)

def send_right():
    mc.send_command("D", canvas, figure)

tk.Button(frame, text="Frente", command=send_forward).pack(side=tk.LEFT)
tk.Button(frame, text="Esquerda", command=send_left).pack(side=tk.LEFT)
tk.Button(frame, text="Direita", command=send_right).pack(side=tk.LEFT)

# Inicializa o ambiente
environment = np.zeros((20, 20))
mc.update_environment(environment, (0, 0))
ag.draw_environment(canvas, figure, np.zeros((20, 20)), (0, 0))


tab3 = ttk.Frame(tab_control)
tab_control.add(tab3, text='Configurações de Robô')

# Configurações de Robô
ttk.LabelFrame(tab3, text="Configurações de Robô").pack()
btn_start_server = ttk.Button(tab3, text="Ligar Servidor", command=lambda: server.start_server).pack()
btn_close_server = ttk.Button(tab3, text="Desligar Servidor", command=lambda: server.stop_server_func()).pack()
#btn_handle_client = ttk.Button(tab3, text="Conectar Cliente", command=lambda: wsc.WifiServer.ha).pack()



tab4 = ttk.Frame(tab_control)
tab_control.add(tab4, text='Mapeamento do Ambiente')


# Loop Tkinter
window.mainloop()