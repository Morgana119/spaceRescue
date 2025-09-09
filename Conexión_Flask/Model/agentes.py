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

from agentClass import RobotAgent
from collections import deque

class Cell:
    def __init__(self, x, y, walls):
        self.x = x
        self.y = y
        
        self.walls = walls
        self.fire = False
        self.hasToken = False
        self.smoke = False
        self.isExit = False
        self.poiHidden = None   # 'V' o 'F' si hay POI oculto

class ExplorerModel(Model):
    def __init__(self,agent_names,  randomStatus,  width = 10, height = 8, numRobots = 6):
        super().__init__()
        self.agentsGrid = MultiGrid(width, height, torus=False)    
        self.schedule = RandomActivation(self)
        self.damagedWalls = 0
        self.savedVictims = 0
        self.randomStatus = randomStatus
        self.width = width
        self.height = height
        self.agentIndex = 0
        self.currentStep = 0 
        self.numRobots = numRobots
        self.newFire = []
        self.newSmoke = []
        self.current_turn = 0
        self.myAgents = []
        self.deadVictims = 0
        self.maxDamagedWalls = 24     # pierde si llega aquí
        self.maxDeadVictims = 4       # pierde si llega aquí
        self.victimsToSave = 7        # gana si llega aquí
        
        self.ambulanceSpots = [(0, 0), (5, 0), (6, 0), (9, 3), (9, 4), (0, 3), (0, 4), (3, 7), (4, 7)]
        self.newlyIgnited = set()  # {(x, y)} casillas que pasaron a fuego en el turno

        self.actionsLog = []

        # Se llena el grid de los estados de las paredes
        # 0 -> ausencia
        # 1 -> pared completa
        # 2 -> pared dañada
        # 3 -> puerta cerrada
        # arriba | derecha | abajo | izquierda
        gridValues = [
            ["0000","0010","0010","0010","0010","0010","0000","0010","0010","0000"],
            ["0100","1001","1000","1300","1003","1100","0001","1000","1100","0001"],
            ["0100","0001","0000","0110","0011","0310","0013","0010","0130","0001"],
            ["0000","0000","0300","1003","1000","1000","1100","1001","3100","0001"],
            ["0100","0011","0110","0011","0030","0010","0310","0013","0010","0000"],
            ["0100","1001","1000","1000","3000","1100","1001","1100","1101","0001"],
            ["0100","0011","0010","0000","0010","0310","0013","0310","0113","0001"],
            ["0000","1000","1000","0000","1000","1000","1000","1000","1000","0000"]
        ]
        gridValues2 = [
            ["0000","0010","0010","0010","0010","0010","0000","0010","0010","0000"],
            ["0100","1001","1000","1000","1000","1100","0001","1000","1100","0001"],
            ["0100","0001","0000","0110","0011","0010","0010","0010","0100","0001"],
            ["0000","0000","0000","1000","1000","1000","1100","1001","0100","0001"],
            ["0100","0011","0110","0011","0000","0010","0010","0010","0010","0000"],
            ["0100","1001","1000","1000","0000","1100","1001","1100","1101","0001"],
            ["0100","0011","0010","0000","0010","0010","0010","0010","0110","0001"],
            ["0000","1000","1000","0000","1000","1000","1000","1000","1000","0000"]
        ]

        self.grid = [
                [Cell(x, y, walls=[int(d) for d in gridValues2[y][x]])
                for x in range(self.width)]
                for y in range(self.height)
            ]

        # Se llena el grid de fuego con posiciones iniciales
        self.firePositions = [(2, 2), (2, 3), (3, 2), (4, 3), (3, 3), (5, 3), (4, 4), (6, 5), (7, 5), (6, 6) ]
        for x, y in self.firePositions:
            self.grid[y][x].fire = True
        print(f"[INIT] Fuego inicial en: {self.firePositions}")
        
        self.exitPositions = [(0,6), (3,0), (7,3), (4,9)]
        for y, x in self.exitPositions:
            self.grid[y][x].isExit = True
        print(f"[INIT] Puertas inicial en: {self.exitPositions}")

        for y, x in self.firePositions:
            print(f"[DEBUG] FUEGO inicial en: {y,x, self.grid[y][x].fire}")

        self.poiDeck = ['V'] * 10 + ['F'] * 5
        self.random.shuffle(self.poiDeck)
        self.poisOnBoard = set()   # {(x,y)}

        # Iniciales
        initPOI = [(4, 2), (1, 5), (8, 5)]
        for (x, y) in initPOI:
            self.placeNewPOI(x, y, by_dice=False)

        # Si alguna no pudo (fuego, fuera, agente, etc.), rellena por dados hasta llegar a 3
        self.ensure3POI()
        print(f"[POI|INIT] POIs en tablero: {sorted(list(self.poisOnBoard))} | mazo={len(self.poiDeck)}")

        # Crear agentes
        self.agentList = []
        self.current_turn = 0
        for i in range(self.numRobots):
            a = RobotAgent(agent_names[i], self)
            self.schedule.add(a)
            self.agentList.append(a)
        
        if self.randomStatus == True: 
            print("Random----------------------------------------------------")
            self.placeRandomAgents()
        else:
            print("Not random----------------------------------------------------")
            self.assignPairs()

    # Colocar agentes en solucion random
    def placeRandomAgents(self):
        for agent in self.agentList:
            while True:
                # elegir una casilla de las orillas
                side = self.random.choice(["top", "bottom", "left", "right"])
                if side == "top":
                    x = self.random.randrange(self.width)
                    y = 0
                elif side == "bottom":
                    x = self.random.randrange(self.width)
                    y = self.height - 1
                elif side == "left":
                    x = 0
                    y = self.random.randrange(self.height)
                elif side == "right":
                    x = self.width - 1
                    y = self.random.randrange(self.height)

                # condiciones: celda vacía y sin fuego
                if self.agentsGrid.is_cell_empty((x, y)) and not self.grid[y][x].fire:
                    self.agentsGrid.place_agent(agent, (x, y))
                    agent.positionX, agent.positionY = x, y
                    print(f"[INIT] Agente {agent.idRobot} colocado en {(x, y)})")
                    break

    # Definir parejas -> model.assignPairs
    def assignPairs(self):
        entrances = [(0,6), (9,4), (3,7), (1,3)]
        pairs = [(self.agentList[i], self.agentList[i+1]) for i in range(0, len(self.agentList)-1, 2)]
        chosen = self.random.sample(entrances, k=min(3, len(pairs), len(entrances)))

        for (a1, a2), (ex, ey) in zip(pairs, chosen):
            # a1 directo en la entrada
            self.agentsGrid.place_agent(a1, (ex, ey))
            a1.positionX, a1.positionY = ex, ey
            print(f"[INIT] {a1.idRobot} en entrada {(ex, ey)}")

            # a2 en una orilla adyacente a la entrada
            placed_pair = False
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = ex + dx, ey + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx == 0 or ny == 0 or nx == self.width - 1 or ny == self.height - 1):
                        if self.agentsGrid.is_cell_empty((nx, ny)):
                            self.agentsGrid.place_agent(a2, (nx, ny))
                            a2.positionX, a2.positionY = nx, ny
                            print(f"[INIT] {a2.idRobot} en {(nx, ny)} (pareja de {a1.idRobot})")
                            placed_pair = True
                            break
            # Si no encontró adyacente libre, ponlo en otra entrada libre
            if not placed_pair:
                for (fx, fy) in entrances:
                    if self.agentsGrid.is_cell_empty((fx, fy)):
                        self.agentsGrid.place_agent(a2, (fx, fy))
                        a2.positionX, a2.positionY = fx, fy
                        print(f"[INIT] {a2.idRobot} en {(fx, fy)} (fallback)")
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
    
    def get_full_state(self):
        actions_list = []
        for act in self.actionsLog:
            entry = {"source": act[0]}

            if act[0] == "model":
                # acciones del modelo
                if act[1] == "ignite":
                    entry.update({"action": "ignite", "x": act[2], "y": act[3]})
                elif act[1] == "smoke":
                    entry.update({"action": "smoke", "x": act[2], "y": act[3]})
                elif act[1] == "dice":
                    entry.update({"action": "dice", "x": act[2], "y": act[3]})
                elif act[1] == "poiPlaced":
                    entry.update({"action": "poiPlaced", "x": act[2], "y": act[3]})
                elif act[1] == "poiReveal":
                    entry.update({"action": "poiReveal", "x": act[2], "y": act[3], "kind": act[4]})
                elif act[1] == "knockdown":
                    entry.update({"action": "knockdown", "agent": act[2], "x": act[3], "y": act[4]})
                elif act[1] == "openDoor":
                    entry.update({"action": "openDoor", "x": act[2], "y": act[3], "direction": act[4]})
                else:
                    entry.update({"action": act[1], "data": act[2:]})

            elif act[0] == "agent":
                # acciones de agentes
                entry.update({
                    "agent": act[1],        # id del robot
                    "action": act[2],       # acción que realizó
                    "x": act[3], 
                    "y": act[   4]
                })

            actions_list.append(entry)

        state = {"actions": actions_list}

        # limpiar después de mandar
        self.actionsLog = []

        return state


    def RollDice(self,):
        x = random.randint(1, self.width - 2)
        y = random.randint(1, self.height - 2) 
        return x, y
    
    def updateSmoke(self) : 
        initial_ignition_points = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x].smoke == True:
                    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < self.height and 0 <= nx < self.width:
                            neighbor = self.grid[ny][nx]
                            if self.grid[ny][nx].fire == True: 
                                initial_ignition_points.add((y, x))
        for y, x in initial_ignition_points:
            self.propagateFire(y, x)    

    def propagateFire(self, y_start, x_start):
        queue = deque()
        processed_cells = set()

        queue.append((y_start, x_start))
        processed_cells.add((y_start, x_start))

        while queue:
            y, x = queue.popleft()
            
            self.grid[y][x].fire = True
            self.grid[y][x].smoke = False
            self.actionsLog.append(('model', 'stopSmoke', y, x))
            self.actionsLog.append(('model', 'ignite', y, x))

            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx

                if 0 <= ny < self.height and 0 <= nx < self.width and (ny, nx) not in processed_cells:
                    neighbor = self.grid[ny][nx]
                    if neighbor.smoke:
                        queue.append((ny, nx))
                        processed_cells.add((ny, nx))

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
        cell = self.grid[y][x]

        if not cell.fire and not cell.smoke:
            cell.smoke = True
            self.actionsLog.append(('model', 'smoke', y, x))
        
        elif not cell.fire and cell.smoke:
            cell.smoke = False
            cell.fire = True
            self.newlyIgnited.add((x, y))
            self.actionsLog.append(('model', 'stopSmoke', y, x))
            self.actionsLog.append(('model', 'ignite', y, x))
        
        else:
            print(f"[FIRE] ¡Explosión! en {(x, y)}")
            self.handleExplosion(y, x)


    def handleExplosion(self, y, x):
        for direction in range(4):
            self.propagateExplosion(y, x, direction)


    def propagateExplosion(self, y, x, direction):
        moves = {0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)}
        dy, dx = moves[direction]
        ny, nx = y + dy, x + dx

        while 0 <= ny < self.height and 0 <= nx < self.width:
            wall_status = self.grid[y][x].walls[direction]

            if wall_status != 0:
                self.damageWall(y, x, direction, wall_status)
                break

            neighbor = self.grid[ny][nx]

            if not neighbor.fire:
                neighbor.fire = True
                neighbor.smoke = False
                print(f"[FIRE→SPREAD] Se encendió fuego en {(nx, ny)} por dir {direction} desde {(x, y)}")
                self.newlyIgnited.add((ny, nx))
                self.actionsLog.append(('model', 'ignite', ny, nx))
                break

            ny += dy
            nx += dx


    def damageWall(self, y, x, direction, wall_status):
        if wall_status == 1:  # pared intacta → dañada
            self.updateNeighbors(x, y, direction, 2)
            self.grid[y][x].walls[direction] = 2
            self.damagedWalls += 1
            print(f"[FIRE|EXPLODE] Pared completa dañada (1→2) en {(x, y)} dir {direction}")

        elif wall_status == 2:  # pared dañada → colapsa
            self.updateNeighbors(x, y, direction, 0)
            self.grid[y][x].walls[direction] = 0
            self.damagedWalls += 1
            print(f"[FIRE|EXPLODE] Pared dañada colapsa (2→0) en {(x, y)} dir {direction}")

        elif wall_status == 3:  # puerta cerrada → abierta
            self.updateNeighbors(x, y, direction, 0)
            self.grid[y][x].walls[direction] = 0
            self.actionsLog.append(('model', 'openDoor', y, x, direction))
            print(f"[FIRE|EXPLODE] Puerta cerrada se abre en {(x, y)} dir {direction}")
        


    # Válida = dentro de tablero, sin fuego, sin otro POI.
    # Permitimos humo y agentes (si quieres evitar agentes, agrega un check a is_cell_empty).
    def cellPOI(self, x, y):
        # Debe estar dentro del tablero
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        cell = self.grid[y][x]

        # No permitir si: fuego, humo o ya hay otro POI
        if cell.fire or cell.smoke or cell.hasToken:
            return False

        # No permitir si hay cualquier agente en la celda
        if self.agentsGrid.get_cell_list_contents((x, y)):
            return False

        return True
    
    # Elige coordenadas con dados (RollDice) hasta encontrar una celda válida
    def dicePOI(self, max_tries=500):
        print("Entro al roll dice:")
        for _ in range(max_tries):
            x, y = self.RollDice() 
            print("DICE", x,y, "----------------------------------------------------------------")       
            if self.cellPOI(x, y):
                return (x, y)
        return None
    
    # Coloca un POI boca abajo sacando del mazo. Si by_dice=True y la celda no sirve, reintenta por dados
    def placeNewPOI(self, x, y, by_dice=True):
        print("Entro al place New POI------------------------------------------------------")
        if not self.poiDeck:
            print("[POI|PLACE] Mazo vacío: no se puede colocar más POI")
            return False


        # Saca la carta del mazo y colócala oculta en la celda
        card = self.poiDeck.pop()   # 'V' o 'F', queda oculta
        print("CELL: ", x, y)
        cell = self.grid[y][x]
        cell.hasToken = True
        cell.poiHidden = card
        self.poisOnBoard.add((y, x))
        self.actionsLog.append(('model', 'poiPlaced', y, x))
        print(f"[POI|PLACE] POI oculto colocado en {(x, y)} (mazo restante={len(self.poiDeck)})")
        return True

    # Mantiene 3 POI en tablero mientras quede mazo; coloca por 'dados'
    def ensure3POI(self):
        print("Entro al ensure#POI")
        while len(self.poisOnBoard) < 3 and self.poiDeck:
            spot = self.dicePOI()
            if spot is None:
                print("[POI|ENSURE] No hay spots válidos por dados para reponer POI")
                break
            x, y = spot
            self.placeNewPOI(x, y, by_dice=False)
        print(f"[POI|STATE] En tablero={len(self.poisOnBoard)} | Mazo={len(self.poiDeck)}")
    
    # Se llama cuando el agente entra a la celda (x,y) con un POI
    def revealPOI(self, x, y, agent):
        print("ENTRO A REVEAL POI --------------------------------------------------------")
        cell = self.grid[y][x]
        if not cell.hasToken:
            return

        kind = cell.poiHidden  # 'V' o 'F'
        cell.hasToken = False
        cell.poiHidden = None

        agent.posPOI = y, x
        # if (y, x) in self.poisOnBoard:
        #     print("Entro al remove ------------------------------------")
        #     self.poisOnBoard.remove((y, x))

        if kind == 'V':
            agent.carriesPOI = True
            agent.rolRobot = 1
            agent.saveVictim()
            print(f"[POI|REVEAL] VÍCTIMA en {(x, y)} → {agent.idRobot} ahora la transporta")
        else:
            print(f"[POI|REVEAL] FALSA ALARMA en {(x, y)}")
        
        self.actionsLog.append(('model', 'poiReveal', x, y, kind))  # kind: 'V' o 'F'
        # Reponer hasta 3 por dados
        # self.ensure3POI()
    
    # Escoge la ambulancia más cercana por distancia Manhattan
    def nearestAmbulance(self, x, y):
        return min(self.ambulanceSpots, key=lambda s: abs(x - s[0]) + abs(y - s[1]))
    
    def teleportTo(self, agent, pos):
        ax, ay = pos
        self.agentsGrid.move_agent(agent, (ax, ay))
        agent.positionX, agent.positionY = ax, ay
        self.actionsLog.append(('model', 'teleport', agent.idRobot, ax, ay))
        
    def knockdown(self, agent):
        self.actionsLog.append(('model', 'knockdown', agent.idRobot, agent.positionX, agent.positionY))

        # Si llevaba víctima, se pierde
        if agent.carriesPOI:
            agent.carriesPOI = False
            self.deadVictims += 1
            print(f"[KNOCKDOWN] {agent.idRobot} derribado CON VÍCTIMA → víctima perdida. Muertas={self.deadVictims}")

        # Teletransporte a ambulancia
        ax, ay = self.nearestAmbulance(agent.positionX, agent.positionY)
        print(f"[KNOCKDOWN] {agent.idRobot} → Ambulancia {(ax, ay)}")
        self.teleportTo(agent, (ax, ay))

        # Cerrar su turno actual (el siguiente turno arrancará con 4 PA)
        agent.actionPoints = 0

    def checkGameOver(self):
        # Colapso edificio
        if self.damagedWalls >= self.maxDamagedWalls:
            print("[GAME OVER] El edificio colapsó")
            return False, "LOSE"

        # Demasiadas víctimas muertas
        if self.deadVictims >= self.maxDeadVictims:
            print("[GAME OVER] Han muerto 4 víctimas")
            return False, "LOSE"

        # Suficientes víctimas rescatadas
        if self.savedVictims >= self.victimsToSave:
            print("[VICTORY] Se rescataron 7 víctimas")
            return False, "WIN"

        return True, None

    def step(self):
        self.actionsLog = []
        self.newlyIgnited = set()
        if not self.agentList:
            return

        # agente del turno actual
        agent = self.agentList[self.current_turn]
        print(f"[TURN {self.currentStep}] Actúa agente {agent.idRobot} desde {(agent.positionY, agent.positionX)}")

        agent.step()  # este agente gasta hasta 4 PA en su propio step()

        # avanza el turno de forma cíclica
        self.current_turn = (self.current_turn + 1) % len(self.agentList)

        # dinámica de fuego
        x, y = self.RollDice()
        self.actionsLog.append(('model', 'dice', y, x))
        print(f"[FIRE] Tirada de fuego desde {(x, y)}")
        self.spreadFire(x, y)
        self.updateSmoke()
        print("YA TERMINO DE EXPANDIR EL FUEGO")

        # Si alguien está en una casilla recién encendida, knockdown
        for a in self.agentList:
            if (a.positionX, a.positionY) in self.newlyIgnited:
                self.knockdown(a)

        # Checar si se acabó el juego
        ended, result = self.checkGameOver()
        if ended:
            print(f"[END] Resultado: {result}")
            return

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


agent_names = ["morado", "rosa", "rojo", "azul", "naranja", "verde"]
model = ExplorerModel(agent_names, True)
allGrids = []
num_steps = 40  # cuántos pasos quieres simular desde el estado actual
model.print_grid()
print("----------------------")

# # for agent in model.agents:
# #     agent.carriesPOI = False
# #     print(f"[Agente {agent.idRobot}] Posición: ({agent.positionY}, {agent.positionX}), "
# #           f"Lleva POI: {agent.carriesPOI}, Victimas salvadas: {agent.savedVictims}, AP: {agent.actionPoints}")

while model.currentStep < num_steps:
    model.step()
    allGrids.append(gridArray(model))
    model.currentStep += 1 
model.print_grid()

# print("Estado inicial del tablero:")
# model.print_grid()
# print("----------------------")

# for agent in model.agents:
#     print(f"[Agente {agent.idRobot}] Posición: ({agent.positionY}, {agent.positionX}), "
#           f"Lleva POI: {agent.carriesPOI}, Victimas salvadas: {agent.savedVictims}, AP: {agent.actionPoints}")


# ------------- PRUEBA A* PARA 1 AGENTE ----------------------
# agent = model.agents[0]  # tomar un agente cualquiera
# agent.carriesPOI = False
# agent.model.randomStatus = True  # activar modo aleatorio
# # Definir un objetivo cualquiera (por ejemplo la salida más cercana)
# pathfinder = agent.pathfinder
# goal = (4,8) # reemplaza con coordenadas reales de la salida
# path = pathfinder.aStar((agent.positionY, agent.positionX), goal)
# print("Posición del agente:", agent.positionY, agent.positionX)
# print("Goal:", goal[0], goal[1])

# if path is None:
#     print("A* no encontró camino.")
# else:
#     print("Path devuelto por A* (modo aleatorio):")
#     for step in path:
#         print(step)


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