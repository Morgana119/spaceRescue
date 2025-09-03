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

class Cell:
    def __init__(self,x, y, walls):
        self.x = x
        self.y = y
        
        self.walls = walls
        self.fire = False
        self.hasToken = False

class RobotAgent(Agent):
    def __init__(self, model, agentId):
        super().__init__(model)
        self.idRobot = self.unique_id    # Mesa ya lo define 
        self.rolRobot = 0                # 0 -> apagaFuegos | 1 -> salvaVidas
        self.actionPoints = 4
        self.partner = None
        self.positionX = 0
        self.positionY = 0
        self.savedVictims = 0
        self.health = 0

    def actions(self):
        actions = ["move","openClosedDoor","stopFire","breakWall","revealPOI","meetPartner", ]
        for i in actions:
            if actions[i] == False:
                self.actions(self)
            break

    # def move(self):


    # def openClosedDoor(self):
    
    # def stopFire(self):
    
    # def breakWall(self):

    # def revealPOI(self):

    # def meetPartner(self):

    # def savedVictim(self):

    # def damaged(self):

    # def step(self):
    #     print("Agente hizo su step")
    #     print(f"Soy {self.idRobot} y mi pareja es {self.partner}")


class ExplorerModel(Model):
    def __init__(self, width = 8, height = 6, numRobots = 6):
        super().__init__()
        self.agentsGrid = MultiGrid(width, height, torus=False)    
        self.schedule = RandomActivation(self)
        self.numRobots = 6
        self.damagedWalls = 0
        self.savedVictims = 0
        self.randomStatus = True
        self.width = width
        self.height = height
        self.agentIndex = 0
        self.currentStep = 0 
        self.numRobots = numRobots

        # Definir parejas
        self.agents_list = []
        for i in range(0, self.numRobots, 2):
            a1 = RobotAgent(self)
            a2 = RobotAgent(self)

            # Empareja por id
            a1.partner = a2.unique_id
            a2.partner = a1.unique_id

            self.schedule.add(a1)
            self.schedule.add(a2)
            self.agents_list.extend([a1, a2])

        # Se llena el grid de los estados de las paredes
        gridValues = [
            ["1001", "1000", "1300", "1001", "1100", "0001", "1000", "1100"],
            ["0001", "0000", "0110", "0011", "0310", "0011", "0010", "0130"],
            ["0000", "0300", "1003", "1000", "1000", "1100", "1001", "3100"],
            ["0011", "0110", "0011", "0030", "0010", "0310", "0013", "0010"],
            ["1001", "1000", "1000", "3000", "1100", "1001", "1100", "1101"],
            ["0011", "0010", "0000", "0010", "0310", "0013", "0310", "0113"]
        ]

        self.grid = [
                [Cell(x, y, walls=[int(d) for d in gridValues[y][x]])
                for x in range(self.width)]
                for y in range(self.height)
            ]

        # Se llena el grid de fuego con posiciones iniciales
        firePositions = [(1,1), (1,2), (3,4), (3,5), (6,5)]
        for x, y in firePositions:
            self.grid[y][x].fire = True

        # colocar agentes
        for agent in self.agents_list:
            while (i < self.numRobots):
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                if self.agentsGrid.is_cell_empty( (x, y) ) and self.grid[y][x].fire == False:
                    agent = RobotAgent(self)
                    self.agentsGrid.place_agent(agent, (x, y))
                    break

    def print_grid(self):
        for y in range(self.height):
            fila = []
            for x in range(self.width):
                walls_str = "".join(map(str, self.grid[y][x].walls))
                if self.grid[y][x].fire:
                    walls_str += "F"
                fila.append(walls_str)
            print(fila)

    def step(self):
        agentIndex = self.currentStep % self.robots
        agent = self.schedule.agents[agentIndex]
        agent.step()

        x,y = self.RollDice()
        self.spreadFire(x, y)

    def RollDice(self,):
        x = self.random.randrange(self.width)
        y = self.random.randrange(self.height)   
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
                break

            ny += dy
            nx += dx


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
        if self.grid[y][x].fire == 0:
            self.grid[y][x].fire = True
        else : # explosion
            for i in range(4):

                # no hay pared ni nada
                if self.grid[y][x].walls[i] == 0:
                    self.placeFire(y, x, i)

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
            

def gridArray(model):
    arr = np.zeros((model.height, model.width))
    for y in range(model.height):
        for x in range(model.width):
            if model.grid[y][x].fire:
                arr[y][x] = 1
    return arr

allGrids = []

model = ExplorerModel()
while model.currentStep < 50:
    model.step()
    allGrids.append(gridArray(model))
    model.currentStep += 1 

fig, axs = plt.subplots(figsize=(4, 4))
axs.set_xticks([])
axs.set_yticks([])

patch = axs.imshow(allGrids[0], cmap=plt.cm.binary)

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
