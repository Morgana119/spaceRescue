# Importamos la librería random para generar valores aleatorios
import random

# Definición de la clase Agent que representa a un agente en un espacio 2D
'''
class Agent:
    def __init__(self, name):
         # El agente empieza en la posición inicial (0,0) y nombre
        self.x = 0
        self.y = 0
        self.name = name
        
    # Devuelve el estado actual del agente como un diccionario con sus coordenadas
    def get_state(self):
        return {"name" : self.name, "x": self.x, "y": self.y}

    # Calcula una posible siguiente posición modificando X aleatoriamente
    def get_next_position(self):
        # random.choice([-1, 0, 1]) elige un valor al azar (-1, 0 o 1)
        self.x += random.choice([-1, 0, 1])

# Creamos 6 agentes con los nombres que se usan en Unity
COLORS = ["morado", "rosa", "rojo", "azul", "naranja", "verde"]
# Diccionario: nombre -> instancia Agent
agents = {name: Agent(name) for name in COLORS}
'''
# ---------------------------
# Model/agent_model.py
# ---------------------------

class Agent:
    def __init__(self, name, x, y, z):
        self.name = name
        self.x = x
        self.y = y
        self.z = z

    def move(self, width=11, height=11):
        """
        Mueve al agente de forma aleatoria en los ejes X y Z.
        - random.choice([-1, 1]) hace que se desplace 1 unidad a la izquierda o derecha.
        - Este método no restringe el movimiento dentro de los límites del grid todavía.
        """
        self.x += random.choice([-1, 1])
        self.y += random.choice([-1, 1])

    def get_state(self):
        """
        Devuelve el estado actual del agente como un diccionario,
        incluyendo su nombre y posición (solo X, Y).
        """
        return {"name": self.name, "x": self.x, "y": self.y, "z": self.z}

class Model:
    def __init__(self, agent_names, width=11, height=11):
        """
        Constructor de la clase Model.
        - agent_names: lista de nombres para crear agentes.
        - width, height: dimensiones del espacio de simulación.
        - current_turn: lleva el control de qué agente se mueve en cada paso.
        """
        self.agents = []
        self.width = width
        self.height = height
        self.current_turn = 0  # Which agent moves next

        # Se crean los agentes en posiciones aleatorias dentro del grid
        z = 0
        for name in agent_names:
            x = random.randrange(width)
            y = random.randrange(height)
            self.agents.append(Agent(name, x, y, z))

    def step(self):
        """Move only the agent whose turn it is""""""
        Avanza un turno en la simulación.
        - Solo se mueve el agente cuyo turno corresponde.
        - current_turn se actualiza de forma cíclica con módulo (%).
        """
        agent = self.agents[self.current_turn]
        agent.move(self.width, self.height)
        self.current_turn = (self.current_turn + 1) % len(self.agents)

    def get_payload(self):
        """
        Devuelve el estado de todos los agentes en formato diccionario.
        Ideal para enviar como JSON a un cliente (ej. Flask -> Unity).
        """
        return {"agents": [a.get_state() for a in self.agents]}
