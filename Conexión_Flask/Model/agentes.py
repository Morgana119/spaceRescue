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
    def __init__(self, x, y, walls):
        self.x = x
        self.y = y
        
        self.walls = walls
        self.fire = False
        self.hasToken = False
        self.smoke = False

class GridChange:
    def __init__(self, change_type, x, y):
        self.type = change_type 
        self.pos = (x, y)        

    def __repr__(self):
        return f"GridChange(type={self.type}, pos={self.pos})"

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

        # auto-revelar POI si entras en la celda
        if dest.hasToken:
            dest.hasToken = False
            self.carriesPOI = True
            print(f"[Agente {self.idRobot}] AUTO_REVEAL_POI en {(nx, ny)}")

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
            print(f"[Agente {self.idRobot}] STOP_SMOKE en {(nx, ny)}, AP={self.actionPoints}")
            return True

        # Fuego -> humo
        if dest.fire:
            if self.actionPoints < 1: 
                return False
            dest.fire = False
            dest.smoke = True
            self.actionPoints -= 1
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
            print(f"[Agente {self.idRobot}] BREAK_WALL (debilitar 1→2) en {(x, y)} lado {DIR_NAMES[d]} | AP={self.actionPoints}")
            return True

        # Caso 2: 2 -> 0 (romper del todo, ya se puede pasar)
        if wall == 2:
            # actualizar ambos lados a "abierta" (0)
            self.model.updateNeighbors(x, y, d, 0)
            self.model.grid[y][x].walls[d] = 0
            self.model.damagedWalls += 1
            self.actionPoints -= 2
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

class ExplorerModel(Model):
    def __init__(self,agent_names, width = 10, height = 8, numRobots = 6):
        super().__init__()
        self.agentsGrid = MultiGrid(width, height, torus=False)    
        self.schedule = RandomActivation(self)
        self.damagedWalls = 0
        self.savedVictims = 0
        self.randomStatus = True
        self.width = width
        self.height = height
        self.agentIndex = 0
        self.currentStep = 0 
        self.numRobots = numRobots
        self.changes = []
        self.current_turn = 0
        self.myAgents = []
        
        # Se llena el grid de los estados de las paredes
        # 0 -> ausencia
        # 1 -> pared completa
        # 2 -> pared dañada
        # 3 -> puerta cerrada
        # arriba | derecha | abajo | izquierda
        gridValues = [
            ["0000","0010","0010","0010","0010","0010","0010","0010","0010","0000"],
            ["0100","1001","1000","1300","1003","1100","0001","1000","1100","0001"],
            ["0100","0001","0000","0110","0011","0310","0013","0010","0130","0001"],
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
        print(f"[INIT] Fuego inicial en: {firePositions}")

        # Crear agentes
        self.agents_list = []
        self.current_turn = 0
        for i in range(self.numRobots):
            a = RobotAgent(self)
            self.schedule.add(a)
            self.agents_list.append(a)

        # colocar agentes
        for agent in self.agents_list:
            while True:
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                if self.agentsGrid.is_cell_empty( (x, y) ) and self.grid[y][x].fire == False:
                    self.agentsGrid.place_agent(agent, (x, y))
                    agent.positionX, agent.positionY = x, y
                    print(f"[INIT] Agente {agent.idRobot} colocado en {(x, y)}")
                    break
                    
    # Definir parejas -> model.assignPairs
    def assignPairs(self):
        for i in range(0, len(self.agents_list), 2):
            if i + 1 < len(self.agents_list):
                a1 = self.agents_list[i]
                a2 = self.agents_list[i + 1]
                a1.partner = a2.unique_id
                a2.partner = a1.unique_id
    
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
        if not self.agents_list:
            return

        # agente del turno actual
        agent = self.agents_list[self.current_turn]
        print(f"[TURN {self.currentStep}] Actúa agente {agent.idRobot} desde {(agent.positionX, agent.positionY)}")
        agent.step()  # este agente gasta hasta 4 PA en su propio step()

        # avanza el turno de forma cíclica
        self.current_turn = (self.current_turn + 1) % len(self.agents_list)

        # dinámica de fuego
        x, y = self.RollDice()
        print(f"[FIRE] Tirada de fuego desde {(x, y)}")
        self.spreadFire(x, y)
        # pongo un agente de prueba
    
    def get_full_state(self):
        changes_list = [
            {"type": change.type, "x": change.pos[0], "y": change.pos[1]}
            for change in self.changes
        ]

        return {
            "changes": changes_list
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
                print(f"[FIRE→SPREAD] Se encendió fuego en {(nx, ny)} por dirección {coordinate} desde {(x, y)}")
                fire = (y, x)
                self.changes.append(GridChange("fire", x, y))
                break

            ny += dy
            nx += dx
    
    def updateSmoke(self) : 
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x].smoke == True:
                    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < self.height and 0 <= nx < self.width:
                            neighbor = self.grid[ny][nx]
                            if self.grid[ny][nx].fire == True: 
                                self.grid[y][x].fire = True
                                self.grid[y][x].smoke = False
                                self.changes.append(GridChange("fire", x, y))
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
        if self.grid[y][x].fire == False and self.grid[y][x].smoke == False:
            self.grid[y][x].smoke = True
            smoke = (y, x)
            self.changes.append(GridChange("smoke", x, y))
        elif self.grid[y][x].fire == False and self.grid[y][x].smoke == True:
            self.grid[y][x].smoke = False
            self.grid[y][x].fire = True
            self.model.changes.append(GridChange("fire", x, y))

        else : # explosion
            print(f"[FIRE] ¡Explosión! en {(x, y)}")
            for i in range(4):

                # no hay pared ni nada
                if self.grid[y][x].walls[i] == 0:
                    print(f"[FIRE|EXPLODE] Paso libre hacia dir {i} → propagar")
                    self.placeFire(y, x, i)

                # hay una pared completa
                elif self.grid[y][x].walls[i] == 1:
                    # actualizar los vecinos de la pared dañada
                    self.updateNeighbors(x, y, i, 2)
                    self.grid[y][x].walls[i] = 2
                    self.damagedWalls += 1
                    print(f"[FIRE|EXPLODE] Pared completa dañada (1→2) en {(x, y)} dir {i}")

                # hay una pared dañada
                elif self.grid[y][x].walls[i] == 2:
                    # ya no hay pared
                    # actualizo vecinos que ya no hay pared
                    self.updateNeighbors(x, y, i, 0)
                    self.grid[y][x].walls[i] = 0
                    self.damagedWalls += 1
                    print(f"[FIRE|EXPLODE] Pared dañada colapsa (2→0) en {(x, y)} dir {i}")

                # hay una puerta cerrada
                elif self.grid[y][x].walls[i] == 3:
                    # abro la puerta
                    # actualizo vecinos que ya no hay pared
                    self.updateNeighbors(x, y, i, 0)
                    self.grid[y][x].walls[i] = 0
    
    
    def print_grid(self):
        for y in range(self.height):
            fila = []
            for x in range(self.width):
                walls_str = "".join(map(str, self.grid[y][x].walls))
                if self.grid[y][x].fire:
                    walls_str += "F"
                elif self.grid[y][x].smoke:
                    walls_str += "S"
                fila.append(walls_str)
            print(fila)
            

def gridArray(model):
    arr = np.zeros((model.height, model.width))
    for y in range(model.height):
        for x in range(model.width):
            if model.grid[y][x].fire:
                arr[y][x] = 1
            elif model.grid[y][x].smoke: 
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
# fig, axs = plt.subplots(figsize=(5, 5))
# axs.set_xticks([])
# axs.set_yticks([])

# # Definir colores: 0=blanco, 1=rojo (fuego), 2=gris (humo)
# cmap = ListedColormap(['white', 'red', 'gray'])

# # Margen visual entre celdas
# margin = 0.5
# height, width = allGrids[0].shape
# patch = axs.imshow(
#     allGrids[0],
#     cmap=cmap,
#     extent=[-margin, width-1+margin, -margin, height-1+margin],
#     interpolation='none'
# )

# def animate(i):
#     patch.set_data(allGrids[i])
#     return [patch]

# anim = animation.FuncAnimation(
#     fig,
#     animate,
#     frames=len(allGrids),
#     interval=300,
#     blit=True
# )

# plt.show()