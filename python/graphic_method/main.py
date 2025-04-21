#import tkinter as tk
import ttkbootstrap as tk
from robo_gui import RoboGUI

if __name__ == "__main__":
    root = tk.Window(themename="cyborg")  # Escolha um tema do ttkbootstrap
    app = RoboGUI(root)
    root.mainloop()