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
        self.poiHidden = None   # 'V' o 'F' si hay POI oculto

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
        self.model.actionsLog.append(('agent', self.idRobot, 'move', self.positionX, self.positionY))

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
        self.model.actionsLog.append(('agent', self.idRobot, 'openDoor', x, y, d))
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
            self.model.actionsLog.append(('agent', self.idRobot, 'stopSmoke', nx, ny))
            print(f"[Agente {self.idRobot}] STOP_SMOKE en {(nx, ny)}, AP={self.actionPoints}")
            return True

        # Fuego -> humo
        if dest.fire:
            if self.actionPoints < 1: 
                return False
            dest.fire = False
            dest.smoke = True
            self.actionPoints -= 1
            self.model.actionsLog.append(('agent', self.idRobot, 'fireToSmoke', nx, ny))
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
            self.model.actionsLog.append(('agent', self.idRobot, 'fullExtinguish', self.positionX, self.positionY))
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
            self.model.actionsLog.append(('agent', self.idRobot, 'fullExtinguish', nx, ny))
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
            self.model.actionsLog.append(('agent', self.idRobot, 'weakenWall', x, y, d))
            print(f"[Agente {self.idRobot}] BREAK_WALL (debilitar 1→2) en {(x, y)} lado {DIR_NAMES[d]} | AP={self.actionPoints}")
            return True

        # Caso 2: 2 -> 0 (romper del todo, ya se puede pasar)
        if wall == 2:
            # actualizar ambos lados a "abierta" (0)
            self.model.updateNeighbors(x, y, d, 0)
            self.model.grid[y][x].walls[d] = 0
            self.model.damagedWalls += 1
            self.actionPoints -= 2
            self.model.actionsLog.append(('agent', self.idRobot, 'breakWall', x, y, d))
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
        self.newFire = []
        self.newSmoke = []
        self.current_turn = 0
        self.myAgents = []
        self.deadVictims = 0
        self.maxDamagedWalls = 24     # pierde si llega aquí
        self.maxDeadVictims = 4       # pierde si llega aquí
        self.victimsToSave = 7        # gana si llega aquí
        
        self.ambulanceSpots = [(0, 0), (self.width - 1, self.height - 1)]
        self.newlyIgnited = set()  # {(x, y)} casillas que pasaron a fuego en el turno

        self.actionsLog = []

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

        self.poiDeck = ['V'] * 10 + ['F'] * 5
        self.random.shuffle(self.poiDeck)
        self.poisOnBoard = set()   # {(x,y)}

        # Iniciales
        initPOI = [(2, 4), (5, 1), (5, 8)]
        for (x, y) in initPOI:
            self.placeNewPOI(x, y, by_dice=False)

        # Si alguna no pudo (fuego, fuera, agente, etc.), rellena por dados hasta llegar a 3
        self.ensure3POI()
        print(f"[POI|INIT] POIs en tablero: {sorted(list(self.poisOnBoard))} | mazo={len(self.poiDeck)}")

        # Crear agentes
        self.agentList = []
        self.current_turn = 0
        for i in range(self.numRobots):
            a = RobotAgent(self)
            self.schedule.add(a)
            self.agentList.append(a)

        # colocar agentes
        for agent in self.agentList:
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
        for i in range(0, len(self.agentList), 2):
            if i + 1 < len(self.agentList):
                a1 = self.agentList[i]
                a2 = self.agentList[i + 1]
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
                print(f"[FIRE→SPREAD] Se encendió fuego en {(nx, ny)} por dirección {coordinate} desde {(x, y)}")
                fire = (y, x)
                self.newFire.append(fire)
                self.newlyIgnited.add((nx, ny))
                self.actionsLog.append(('model', 'ignite', nx, ny))
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
            self.newSmoke.append(smoke)
            self.actionsLog.append(('model', 'smoke', x, y))
        elif self.grid[y][x].fire == False and self.grid[y][x].smoke == True:
            self.grid[y][x].smoke = False
            self.grid[y][x].fire = True
            fire = (y, x)
            self.newFire.append(fire)
            self.newlyIgnited.add((x, y))
            self.actionsLog.append(('model', 'ignite', x, y))


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
        for _ in range(max_tries):
            x, y = self.RollDice()          
            if self.cellPOI(x, y):
                return (x, y)
        return None
    
    # Coloca un POI boca abajo sacando del mazo. Si by_dice=True y la celda no sirve, reintenta por dados
    def placeNewPOI(self, x, y, by_dice=True):
        if not self.poiDeck:
            print("[POI|PLACE] Mazo vacío: no se puede colocar más POI")
            return False

        if by_dice and not self.cellPOI(x, y):
            # si nos dieron coords pero no es válida, ignora y busca por dados
            spot = self.dicePOI()
            if spot is None:
                print("[POI|PLACE] No hay lugar válido para colocar POI (dados)")
                return False
            x, y = spot
        else:
            if not self.cellPOI(x, y):
                print(f"[POI|PLACE] Invalid spot {(x,y)}; reintentando con dados...")
                spot = self.dicePOI()
                if spot is None:
                    print("[POI|PLACE] No hay lugar válido para colocar POI (dados)")
                    return False
                x, y = spot

        # Saca la carta del mazo y colócala oculta en la celda
        card = self.poiDeck.pop()   # 'V' o 'F', queda oculta
        cell = self.grid[y][x]
        cell.hasToken = True
        cell.poiHidden = card
        self.poisOnBoard.add((x, y))
        self.actionsLog.append(('model', 'poiPlaced', x, y))
        print(f"[POI|PLACE] POI oculto colocado en {(x, y)} (mazo restante={len(self.poiDeck)})")
        return True

    # Mantiene 3 POI en tablero mientras quede mazo; coloca por 'dados'
    def ensure3POI(self):
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
        cell = self.grid[y][x]
        if not cell.hasToken:
            return

        kind = cell.poiHidden  # 'V' o 'F'
        cell.hasToken = False
        cell.poiHidden = None
        if (x, y) in self.poisOnBoard:
            self.poisOnBoard.remove((x, y))

        if kind == 'V':
            agent.carriesPOI = True
            print(f"[POI|REVEAL] VÍCTIMA en {(x, y)} → {agent.idRobot} ahora la transporta")
        else:
            print(f"[POI|REVEAL] FALSA ALARMA en {(x, y)}")
        
        self.actionsLog.append(('model', 'poiReveal', x, y, kind))  # kind: 'V' o 'F'
        # Reponer hasta 3 por dados
        self.ensure3POI()
    
    # def nearestAmbulance():
        
    # def teleportTo():
        
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
            print("[GAME OVER] El edificio colapsó. 🔨")
            return True, "LOSE"

        # Demasiadas víctimas muertas
        if self.deadVictims >= self.maxDeadVictims:
            print("[GAME OVER] Han muerto 4 víctimas. 💀")
            return True, "LOSE"

        # Suficientes víctimas rescatadas
        if self.savedVictims >= self.victimsToSave:
            print("[VICTORY] Se rescataron 7 víctimas. 🏆")
            return True, "WIN"

        return False, None

    # def step(self):
    #     agent = self.myAgents[self.current_turn]
    #     agent.move(self.width, self.height)
    #     self.current_turn = (self.current_turn + 1) % len(self.myAgents)
    #     self.newFire = []
    #     self.newSmoke = []
    #     x,y = self.RollDice()
    #     self.spreadFire(x, y)
    #     self.updateSmoke()

    def step(self):
        self.actionsLog = []
        self.newlyIgnited = set()
        if not self.agentList:
            return

        # agente del turno actual
        agent = self.agentList[self.current_turn]
        print(f"[TURN {self.currentStep}] Actúa agente {agent.idRobot} desde {(agent.positionX, agent.positionY)}")
        agent.step()  # este agente gasta hasta 4 PA en su propio step()

        # avanza el turno de forma cíclica
        self.current_turn = (self.current_turn + 1) % len(self.agentList)

        # dinámica de fuego
        x, y = self.RollDice()
        self.actionsLog.append(('model', 'dice', x, y))
        print(f"[FIRE] Tirada de fuego desde {(x, y)}")
        self.spreadFire(x, y)
        self.ensure3POI()

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