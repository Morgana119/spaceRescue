# Requiero Mesa > 3.0.3
# Importamos las clases que se requieren para manejar los agentes (Agent) y su entorno (Model).
# Cada modelo puede contener múltiples agentes.
from mesa import Agent, Model

# Debido a que necesitamos que existe un solo agente por celda, elegimos ''SingleGrid''.
from mesa.space import SingleGrid
from mesa.space import MultiGrid

# Con ''RandomActivation'', hacemos que todos los agentes se activen de forma aleatoria.
from mesa.time import RandomActivation

# Haremos uso de ''DataCollector'' para obtener información de cada paso de la simulación.
from mesa.datacollection import DataCollector

# Haremos uso de ''batch_run'' para ejecutar varias simulaciones
from mesa.batchrunner import batch_run

# matplotlib lo usaremos crear una animación de cada uno de los pasos del modelo.
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap
plt.rcParams["animation.html"] = "jshtml"
matplotlib.rcParams['animation.embed_limit'] = 2**128

# Importamos los siguientes paquetes para el mejor manejo de valores numéricos.
import numpy as np
import pandas as pd
import seaborn as sns
sns.set()

# Definimos otros paquetes que vamos a usar para medir el tiempo de ejecución de nuestro algoritmo.
import time
import datetime
import random

class Cell:
    def __init__(self,x, y, walls):
        self.x = x
        self.y = y
        
        self.walls = walls
        self.fire = False
        self.hasToken = False
        self.hasSmoke = False


class RobotAgent(Agent):
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




class ExplorerModel(Model):
    def __init__(self,agent_names, width = 10, height = 8):
        super().__init__()
        self.agentsGrid = MultiGrid(width, height, torus=False)    
        self.schedule = RandomActivation(self)
        self.numRobots = 6
        self.damagedWalls = 0
        self.savedVictims = 0
        self.randomStatus = True
        self.width = width
        self.height = height
        self.robots = 1
        self.agentIndex = 0
        self.currentStep = 0 
        self.newFire = []
        self.newSmoke = []
        self.current_turn = 0
        self.myAgents = []
        
        # Se llena el grid de los estados de las paredes
        gridValues = [
            ["0000","0010","0010","0010","0010","0010","0010","0010","0010","0000"],
            ["0100","1001","1000","1300","1001","1100","0001","1000","1100","0001"],
            ["0100","0001","0000","0110","0011","0310","0011","0010","0130","0001"],
            ["0100","0000","0300","1003","1000","1000","1100","1001","3100","0001"],
            ["0100","0011","0110","0011","0030","0010","0310","0013","0010","0001"],
            ["0100","1001","1000","1000","3000","1100","1001","1100","1101","0001"],
            ["0100","0011","0010","0000","0010","0310","0013","0310","0113","0001"],
            ["0000","1000","1000","1000","1000","1000","1000","1000","1000","1000"]
        ]


        self.grid = [
                [Cell(x, y, walls=[int(d) for d in gridValues[y][x]])
                for x in range(self.width)]
                for y in range(self.height)
            ]

        # Se llena el grid de fuego con posiciones iniciales
        firePositions = [(2, 2), (2, 3), (3, 2), (4, 3), (3, 3), (5, 3), (4, 4), (6, 5), (7, 5), (6, 6) ]
        for x, y in firePositions:
            self.grid[y][x].fire = True
        

        # pongo un agente de prueba
        z = 0
        for name in agent_names:
            x = random.randrange(width)
            y = random.randrange(height)
            self.myAgents.append(RobotAgent(name, x, y, z))
    
    def get_new_fires_payload(self):
        return {"fires": [{"x": x, "y": y} for (x, y) in self.newFire]}

    def get_new_smoke_payload(self):
        return {"smokes": [{"x": x, "y": y} for (x, y) in self.newSmoke]}
    
    def get_full_state(self):
        agents = [
            {
                "name": agent.unique_id,
                "x": agent.pos[0],
                "y": 0,        # para Unity
                "z": agent.pos[1]
            }
            for agent in self.schedule.agents
        ]

        fires = [
            {"x": x, "y": y}
            for y in range(self.height)
            for x in range(self.width)
            if self.grid[y][x].fire
        ]

        return {
            "agents": agents,
            "fires": fires
        }

    def RollDice(self,):
        x = random.randint(1, self.width - 2)
        y = random.randint(1, self.height - 2) 
        return x, y
    
    def placeFire(self, y, x, coordinate):
        moves = {
            0: (-1, 0),
            1: (0, 1),
            2: (1, 0),
            3: (0, -1)
        }
        dy, dx = moves[coordinate]
        ny, nx = y + dy, x + dx

        # sigue buscando hasta que encuentra un lugar sin fuego
        while 0 <= ny < len(self.grid) and 0 <= nx < len(self.grid[0]):
            if not self.grid[ny][nx].fire:
                self.grid[ny][nx].fire = True
                fire = (y, x)
                self.newFire.append(fire)
                break

            ny += dy
            nx += dx
    
    def updateSmoke(self) : 
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x].hasSmoke == True:
                    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < self.height and 0 <= nx < self.width:
                            neighbor = self.grid[ny][nx]
                            if self.grid[ny][nx].fire == True: 
                                self.grid[y][x].fire = True
                                self.grid[y][x].hasSmoke = False
                                break

    def updateNeighbors(self, x, y, coordinate, newStatus):
        update = (coordinate + 2) % 4

        moves = {
            0: (-1, 0),
            1: (0, 1),
            2: (1, 0),
            3: (0, -1)
        }
        dy, dx = moves[coordinate]
        ny, nx = y + dy, x + dx 
        if 0 <= ny < len(self.grid) and 0 <= nx < len(self.grid[0]):
            self.grid[ny][nx].walls[update] = newStatus
    
    def IsCollapsed(self):
        return (self.damagedWalls == 24)

    def spreadFire(self, x, y):
        print(y, x)
        if self.grid[y][x].fire == False and self.grid[y][x].hasSmoke == False:
            self.grid[y][x].hasSmoke = True
            smoke = (y, x)
            self.newSmoke.append(smoke)
        elif self.grid[y][x].fire == False and self.grid[y][x].hasSmoke == True:
            self.grid[y][x].hasSmoke = False
            self.grid[y][x].fire = True
            fire = (y, x)
            self.newFire.append(fire)
        else : # explosion
            for i in range(4):

                # no hay pared ni nada
                if self.grid[y][x].walls[i] == 0:
                    self.placeFire( y, x, i)

                # hay una pared completa
                elif self.grid[y][x].walls[i] == 1:
                    # actualizar los vecinos de la pared dañada
                    self.updateNeighbors(x, y, i, 2)
                    self.grid[y][x].walls[i] = 2
                    self.damagedWalls += 1

                # hay una pared dañada
                elif self.grid[y][x].walls[i] == 2:
                    # ya no hay pared
                    # actualizo vecinos que ya no hay pared
                    self.updateNeighbors(x, y, i, 0)
                    self.grid[y][x].walls[i] = 0
                    self.damagedWalls += 1
                
                # hay una puerta cerrada
                elif self.grid[y][x].walls[i] == 3:
                    # abro la puerta
                    # actualizo vecinos que ya no hay pared
                    self.updateNeighbors(x, y, i, 0)
                    self.grid[y][x].walls[i] = 0
    
    def step(self):
        agent = self.myAgents[self.current_turn]
        agent.move(self.width, self.height)
        self.current_turn = (self.current_turn + 1) % len(self.myAgents)
        self.newFire = []
        self.newSmoke = []
        x,y = self.RollDice()
        self.spreadFire(x, y)
        self.updateSmoke()
    
    def print_grid(self):
        for y in range(self.height):
            fila = []
            for x in range(self.width):
                walls_str = "".join(map(str, self.grid[y][x].walls))
                if self.grid[y][x].fire:
                    walls_str += "F"
                elif self.grid[y][x].hasSmoke:
                    walls_str += "S"
                fila.append(walls_str)
            print(fila)
            

def gridArray(model):
    arr = np.zeros((model.height, model.width))
    for y in range(model.height):
        for x in range(model.width):
            if model.grid[y][x].fire:
                arr[y][x] = 1
            elif model.grid[y][x].hasSmoke: 
                arr[y][x] = 2
    return arr

allGrids = []
agent_names = ["morado", "rosa", "rojo", "azul", "naranja", "verde"]
model = ExplorerModel(agent_names)
model.print_grid()
print("----------------------")
while model.currentStep < 1:
    model.step()
    allGrids.append(gridArray(model))
    model.currentStep += 1 
model.print_grid()
fig, axs = plt.subplots(figsize=(5, 5))
axs.set_xticks([])
axs.set_yticks([])

# Definir colores: 0=blanco, 1=rojo (fuego), 2=gris (humo)
cmap = ListedColormap(['white', 'red', 'gray'])

# Margen visual entre celdas
margin = 0.5
height, width = allGrids[0].shape
patch = axs.imshow(
    allGrids[0],
    cmap=cmap,
    extent=[-margin, width-1+margin, -margin, height-1+margin],
    interpolation='none'
)

def animate(i):
    patch.set_data(allGrids[i])
    return [patch]

anim = animation.FuncAnimation(
    fig,
    animate,
    frames=len(allGrids),
    interval=300,
    blit=True
)

plt.show()