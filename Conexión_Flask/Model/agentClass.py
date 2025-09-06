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

class RobotAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.idRobot = self.unique_id    # Mesa ya lo define 
        self.rolRobot = 0                # 0 -> apagaFuegos | 1 -> salvaVidas
        self.actionPoints = 4
        self.partner = None
        self.positionX = 0
        self.positionY = 0
        self.savedVictims = 0
        self.health = 1
        self.carriesPOI = False

    def neighborCoords(self, d):
        # Calcula las coordenadas de la celda vecina en la dirección d
        x, y = self.positionX, self.positionY
        #Convierte un índice de dirección (0–3) en un desplazamiento (dy, dx).
        # 0 = Norte (arriba): y-1
        # 1 = Este (derecha): x+1
        # 2 = Sur (abajo): y+1
        # 3 = Oeste (izquierda): x-1
        dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # N, E, S, O
        dy, dx = dirs[d]
        ny, nx = y + dy, x + dx
        return (x, y, nx, ny)
    
    def insideGrid(self, y, x):
        # Checa si unas coordenadas (y, x) están dentro de los límites del grid.
        return 0 <= y < self.model.height and 0 <= x < self.model.width
    
    # Moverse si wall == 0, se puede mover sobre fuego, a menos que esté cargando un POI
    def move(self, d):
        x, y, nx, ny = self.neighborCoords(d)
        if not self.insideGrid(ny, nx): 
            return False
        if self.model.grid[y][x].walls[d] != 0: 
            return False
        dest = self.model.grid[ny][nx]
        if dest.fire and self.carriesPOI:
            return False

        # costo: 2 si es fuego, 2 si lleva POI, sino 1
        cost = 2 if dest.fire or self.carriesPOI else 1
        if self.actionPoints < cost: 
            return False

        self.model.agentsGrid.move_agent(self, (nx, ny))
        self.positionX, self.positionY = nx, ny
        self.actionPoints -= cost
        self.model.actionsLog.append(('agent', self.idRobot, 'move', self.positionY, self.positionX))

        # auto-revelar POI si entras en la celda
        if dest.hasToken:
            self.model.revealPOI(nx, ny, self)  # ahora el modelo maneja revelar y reponer

        print(f"[Agente {self.idRobot}] MOVE a {(nx, ny)} cost={cost}, AP={self.actionPoints}")
        return True

    # Abrir puerta si wall == 3 (actualizar vecino opuesto y poner 0)
    def openDoor(self, d):
        x, y, nx, ny = self.neighborCoords(d)
        if not self.insideGrid(ny, nx): 
            return False
        if self.model.grid[y][x].walls[d] != 3: 
            return False
        if self.actionPoints < 1: 
            return False

        self.model.updateNeighbors(x, y, d, 0)
        self.model.grid[y][x].walls[d] = 0
        self.actionPoints -= 1
        self.model.actionsLog.append(('agent', self.idRobot, 'openDoor', y, x, d))
        print(f"[Agente {self.idRobot}] OPEN_DOOR dir={d}, AP={self.actionPoints}")
        return True  
    
    # Apagar fuego en destino si wall == 0 y hay fuego | Extinguir humo (1 AP) o convertir fuego en humo (1 AP)
    def stopFire(self, d):
        x, y, nx, ny = self.neighborCoords(d)
        if not self.insideGrid(ny, nx): 
            return False
        if self.model.grid[y][x].walls[d] != 0: 
            return False
        dest = self.model.grid[ny][nx]

        # Apagar humo
        if dest.smoke:
            if self.actionPoints < 1: 
                return False
            dest.smoke = False
            self.actionPoints -= 1
            self.model.actionsLog.append(('agent', self.idRobot, 'stopSmoke', ny, nx))
            print(f"[Agente {self.idRobot}] STOP_SMOKE en {(nx, ny)}, AP={self.actionPoints}")
            return True

        # Fuego -> humo
        if dest.fire:
            if self.actionPoints < 1: 
                return False
            dest.fire = False
            dest.smoke = True
            self.actionPoints -= 1
            self.model.actionsLog.append(('agent', self.idRobot, 'fireToSmoke', ny, nx))
            print(f"[Agente {self.idRobot}] EXTINGUISH_FIRE→SMOKE en {(nx, ny)}, AP={self.actionPoints}")
            return True
        return False  

    # Extinguir fuego completamente (2 AP) en casilla propia o adyacente
    def extinguishFireFull(self, d=None):
        if d is None:
            # casilla propia
            cell = self.model.grid[self.positionY][self.positionX]
            if not cell.fire: 
                return False
            if self.actionPoints < 2: 
                return False
            cell.fire = False
            cell.smoke = False
            self.actionPoints -= 2
            self.model.actionsLog.append(('agent', self.idRobot, 'fullExtinguish', self.positionY, self.positionX))
            print(f"[Agente {self.idRobot}] FULL_EXTINGUISH en propia {(self.positionX, self.positionY)}, AP={self.actionPoints}")
            return True
        else:
            x, y, nx, ny = self.neighborCoords(d)
            if not self.insideGrid(ny, nx): 
                return False
            dest = self.model.grid[ny][nx]
            if not dest.fire: 
                return False
            if self.actionPoints < 2: 
                return False
            dest.fire = False
            dest.smoke = False
            self.actionPoints -= 2
            self.model.actionsLog.append(('agent', self.idRobot, 'fullExtinguish', ny, nx))
            print(f"[Agente {self.idRobot}] FULL_EXTINGUISH en {(nx, ny)}, AP={self.actionPoints}")
            return True

    # Romper pared completa/dañada (1/2) -> 0 y vecino 0
    def breakWall(self, d):
        # 0:N, 1:E, 2:S, 3:O  (coincide con índices de walls)
        DIR_NAMES = {0: "Norte", 1: "Este", 2: "Sur", 3: "Oeste"}

        x, y, nx, ny = self.neighborCoords(d)
        if not self.insideGrid(ny, nx):
            return False

        wall = self.model.grid[y][x].walls[d]
        if wall not in (1, 2):  # solo se puede sobre pared completa (1) o dañada (2)
            return False
        if self.actionPoints < 2:
            return False

        # Caso 1: 1 -> 2 (debilitar, aún no se puede pasar)
        if wall == 1:
            # actualizar ambos lados a "dañada" (2)
            self.model.updateNeighbors(x, y, d, 2)
            self.model.grid[y][x].walls[d] = 2
            self.model.damagedWalls += 1
            self.actionPoints -= 2
            self.model.actionsLog.append(('agent', self.idRobot, 'weakenWall', y, x, d))
            print(f"[Agente {self.idRobot}] BREAK_WALL (debilitar 1→2) en {(x, y)} lado {DIR_NAMES[d]} | AP={self.actionPoints}")
            return True

        # Caso 2: 2 -> 0 (romper del todo, ya se puede pasar)
        if wall == 2:
            # actualizar ambos lados a "abierta" (0)
            self.model.updateNeighbors(x, y, d, 0)
            self.model.grid[y][x].walls[d] = 0
            self.model.damagedWalls += 1
            self.actionPoints -= 2
            self.model.actionsLog.append(('agent', self.idRobot, 'breakWall', y, x, d))
            print(f"[Agente {self.idRobot}] BREAK_WALL (romper 2→0) en {(x, y)} lado {DIR_NAMES[d]} | AP={self.actionPoints}")
            return True
            
        return False
    
    def actions(self):
        while self.actionPoints > 0:
            dirs = [0, 1, 2, 3]
            self.model.random.shuffle(dirs)

            # acciones con dirección
            directional = [self.move, self.openDoor, self.stopFire, self.breakWall]

            # acciones que no siempre necesitan dirección
            nondir = [self.extinguishFireFull]  # propia celda

            acted = False

            # primero prueba sin dirección
            for fn in nondir:
                if fn():
                    acted = True
                    break
            if acted: continue

            # luego prueba con dirección
            for d in dirs:
                a = directional + [lambda d=d: self.extinguishFireFull(d)]
                self.model.random.shuffle(a)
                for fn in a:
                    if fn(d):
                        acted = True
                        break
                if acted: break

            if not acted:
                print(f"[Agente {self.idRobot}] No pudo actuar (AP={self.actionPoints})")
                break

    # def meetPartner(self):
    
    # def saveVictim(self):

    # def damaged(self):

    def step(self):
        # Reinicia PA y ejecuta hasta agotarlos
        self.actionPoints = 4
        self.actions()