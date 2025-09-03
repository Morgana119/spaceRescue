# Importamos la librería random para generar valores aleatorios
import random

# Definición de la clase Agent que representa a un agente en un espacio 2D
class Agent:
    def __init__(self):
         # El agente empieza en la posición inicial (0,0)
        self.x = 0
        self.y = 0

    def move_forward(self):
        self.y += 1  # ejemplo: mover hacia adelante en eje Y

    def move_backward(self):
        self.y -= 1

    def move_left(self):
        self.x -= 1

    def move_right(self):
        self.x += 1

    # Devuelve el estado actual del agente como un diccionario con sus coordenadas
    def get_state(self):
        return {"x": self.x, "y": self.y}

    # Calcula una posible siguiente posición modificando X aleatoriamente
    def get_next_position(self):
        # random.choice([-1, 0, 1]) elige un valor al azar (-1, 0 o 1)
        self.x += random.choice([-1, 0, 1])

# Instancia global del agente   
agent = Agent()
