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

from pathfinder import Pathfinder

class RobotAgent(Agent):
    def __init__(self,name, model):
        super().__init__(model)
        self.idRobot = name    # Mesa ya lo define
        self.rolRobot = 0                # 0 -> apagaFuegos | 1 -> salvaVidas
        self.actionPoints = 4
        self.partner = None
        self.positionX = 0
        self.positionY = 0
        self.savedVictims = 0
        self.health = 1
        self.carriesPOI = False
        self.pathfinder = Pathfinder(self)
        self.posPOI = None
        self.inAmbulance = False
        self.myPOI = None # el poi que busco

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
        print("ENTRO AL MOVE")
        x, y, nx, ny = self.neighborCoords(d)
        if not self.insideGrid(ny, nx):
            print("MOVE NOT INSIDE GRID")
            return False
        if self.model.grid[y][x].walls[d] != 0:
            print("MOVE WALLS IN DANGER, ", self.model.grid[y][x].walls[d])
            return False
        dest = self.model.grid[ny][nx]
        if dest.fire and self.carriesPOI:
            print("Destino con FUEGO MOVE Y LLEVA POI", dest.fire,self.carriesPOI)
            return False

        # costo: 2 si es fuego, sino 1
        cost = 2 if dest.fire or self.carriesPOI else 1
        if self.actionPoints < cost:
            print("MOVE AP NOT ENOUGH", self.actionPoints)
            return False

        self.model.agentsGrid.move_agent(self, (nx, ny))
        self.positionX, self.positionY = nx, ny
        self.actionPoints -= cost
        self.model.actionsLog.append(('agent', self.idRobot, 'move', self.positionX, self.positionY, d))

        # auto-revelar POI si entras en la celda
        if dest.hasToken:
            self.model.revealPOI(nx, ny, self)  # ahora el modelo maneja revelar y reponer

        print(f"[Agente {self.idRobot}] MOVE a {(nx, ny)} cost={cost}, AP={self.actionPoints}")
        return True

    # Abrir puerta si wall == 3 (actualizar vecino opuesto y poner 0)
    def openDoor(self, d):
        print("CLOSED WALL")
        x, y, nx, ny = self.neighborCoords(d)
        if not self.insideGrid(ny, nx):
            print("Not inside grid")
            return False
        if self.model.grid[y][x].walls[d] != 3:
            print("Not a closed door")
            return False
        if self.actionPoints < 1:
            print("Action points not enough")
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
            self.model.actionsLog.append(('agent', self.idRobot, 'stopSmoke', ny, nx, d))
            print(f"[Agente {self.idRobot}] STOP_SMOKE en {(nx, ny)}, AP={self.actionPoints}")
            return True

        # Fuego -> humo
        if dest.fire:
            if self.actionPoints < 1:
                return False
            dest.fire = False
            dest.smoke = True
            self.actionPoints -= 1
            print("Fire POSITIONS: ", self.model.firePositions, nx, ny)
            self.model.firePositions.remove((nx, ny))
            self.model.actionsLog.append(('agent', self.idRobot, 'extinguish', ny, nx, d))
            self.model.actionsLog.append(('agent', self.idRobot, 'smoke', ny, nx, d))



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
            self.model.firePositions.remove((self.positionX, self.positionY))
            self.model.actionsLog.append(('agent', self.idRobot, 'extinguish', self.positionY, self.positionX, d))
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
            self.model.firePositions.remove((nx, ny))
            self.model.actionsLog.append(('agent', self.idRobot, 'extinguish', ny, nx, d))
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
            print("%%%%%%%%%% DIRECTION %%%%%%%%%%%%", d)
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

    def saveVictim(self):
        print("ENTRO AL SAVE VICTIM")
        print("ROL ROBOT: ", self.rolRobot)
        # self.model.actionsLog.append(('agent', self.idRobot, 'saveVictim:start', self.positionX, self.positionY))

        if not self.carriesPOI:
            print(f"[Agente {self.idRobot}] No lleva víctima, no va a la salida")
            return

        path, exit = self.pathfinder.closestExit()
        print("Path:_", path)
        print("EXIT: ", exit)

        if not path or len(path) == 0:
            print(f"[Agente {self.idRobot}] No hay camino a la salida")
            return

        path = [pos for pos, _ in path]

        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O

        for i in range(len(path)):
            next_x, next_y = path[i]
            # solo moverse si es vecino
            moved = False
            for d, (dy, dx) in enumerate(dirs):
                # print("MOVE: ", d, dx, dy)
                # PARA PROBAR EL SAVE VICTIMS SE RESTABLECE SUS AP A 4
                # if self.actionPoints <= 0: self.actionPoints = 4

                if self.positionY + dy == next_y and self.positionX + dx == next_x:
                    print(f"SV IF BEFORE MOVE", d, dy, dx)
                    moved = self.move(d)
                    # print("Move: ", moved)

                    if self.positionY == exit[1] and self.positionX == exit[0]:
                        print("EXIT ",self.positionY , self.positionX )
                        print("POS POI: ", self.posPOI)
                        if self.posPOI is not None:
                            print("POS POI IS NOT NONE")
                            self.carriesPOI = False
                            self.model.savedVictims += 1
                            self.savedVictims += 1
                            self.rolRobot = 0
                            self.model.actionsLog.append(('agent', self.idRobot, 'victimSaved'))
                            x, y = self.posPOI
                            self.model.poiPositions.remove((x, y))
                            self.model.ensure3POI()
                            print("LENGHT:", len(self.model.poiPositions))
                            print("POI", self.model.poiPositions)
                            print("Carries POI to false")
                        self.posPOI = None
                    break

            if not moved:
                print("No se pudo mover a", (next_x, next_y), " AP: ", self.actionPoints)
                break

    def exploreEstrategy(self, start, pair, pairPOS):
        print("PAIR: ", pair)

        for a1, a2 in self.model.pairs:
            print("Entro aqui")
            if self.idRobot == a1.idRobot:
                print("CLOSEST POI -----------------------------")
                path, goal = self.pathfinder.closestPOI()
                print(f"Entro al estrategy Action: ", path,"hasta", goal)
                break
            elif self.idRobot == a2.idRobot:
                print(f"Agent {self.idRobot} is looking for pair")
                path = self.pathfinder.aStar(start, pairPOS)
                # print("Pair PATH", path)
                goal = pairPOS
                print("EXPLORE ESTRATEGY PAIR", goal, "...........................................................")
                break

        if not path or not goal:
            print(f"[Agente {self.idRobot}] No hay POI accesible")
            path = []
            return

        if path and goal:
            for (x,y), action in path:
                if self.actionPoints <= 0:
                    break
                if action == 'move':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.move(d)
                            print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                elif action == 'putOutFire':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.extinguishFireFull(d)
                            print(f"[Agente {self.idRobot}] se extinguio fuego {(x, y)} -> {moved}")
                            break
                elif action == 'putOutSmoke':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.stopFire(d)
                            self.move(d)
                            print(f"[Agente {self.idRobot}] se apago humo {(x, y)} -> {moved}")
                            break
                elif action == 'partiallyPutOutFire':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.stopFire(d)
                            self.move(d)
                            print(f"[Agente {self.idRobot}] se apago fuego {(x, y)} -> {moved}")
                            break
                elif action == 'openDoor':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.openDoor(d)
                            print(f"[Agente {self.idRobot}] abrio una puerta {(x, y)} -> {moved}")
                            self.move(d)
                            break
                elif action == 'knowckDownWall':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.breakWall(d)
                            self.move(d)
                            print(f"[Agente {self.idRobot}] tiro una pared {(x, y)} -> {moved}")
                            break
                elif action == 'moveToFire':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.move(d)
                            print(f"[Agente {self.idRobot}] se movió a fuego  {(x, y)} -> {moved}")
                            break

    def do_actions(self, x, y, action):
        if action == 'move':
            dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
            for d, (dy, dx) in enumerate(dirs):
                if self.positionY + dy == y and self.positionX + dx == x:
                    moved = self.move(d)
                    print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
        elif action == 'putOutFire':
            dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
            for d, (dy, dx) in enumerate(dirs):
                if self.positionY + dy == y and self.positionX + dx == x:
                    moved = self.extinguishFireFull(d)
                    self.move(d)
                    print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                    break
        elif action == 'putOutSmoke':
            dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
            for d, (dy, dx) in enumerate(dirs):
                if self.positionY + dy == y and self.positionX + dx == x:
                    moved = self.stopFire(d)
                    self.move(d)
                    print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                    break
        elif action == 'partiallyPutOutFire':
            dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
            for d, (dy, dx) in enumerate(dirs):
                if self.positionY + dy == y and self.positionX + dx == x:
                    moved = self.stopFire(d)
                    self.move(d)
                    print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                    break
        elif action == 'openDoor':
            dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
            for d, (dy, dx) in enumerate(dirs):
                if self.positionY + dy == y and self.positionX + dx == x:
                    moved = self.openDoor(d)
                    self.move(d)
                    print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                    break
        elif action == 'knowckDownWall':
            dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
            for d, (dy, dx) in enumerate(dirs):
                if self.positionY + dy == y and self.positionX + dx == x:
                    moved = self.breakWall(d)
                    self.move(d)
                    print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                    break
        elif action == 'moveToFire':
            dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
            for d, (dy, dx) in enumerate(dirs):
                if self.positionY + dy == y and self.positionX + dx == x:
                    moved = self.move(d)
                    print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                    break

    def getVictimOUT(self, start, pair, pairPOS):
        print("PAIR: ", pair)

        if self.carriesPOI == True:
            self.saveVictim()
        elif self.carriesPOI == False:
            print("Entro get victim out :)")
            print(f"Agent {self.idRobot} is looking for pair")
            path = self.pathfinder.aStar(start, pairPOS)
            # print("Pair PATH", path)
            goal = pairPOS
            print("GET VICTIM OUT", goal, "...........................................................")

            if not path or not goal:
                print(f"[Agente {self.idRobot}] No hay POI accesible")
                path = []
                return

            if path and goal:
                print("PARTH", path)
                print("GOAL:", goal)

                for (x,y), action in path:
                    if self.actionPoints <= 0:
                        break
                    self.do_actions(x, y, action)

    def onedeath(self, start, pair, pairPOS):
        print("Entro get one death out :)")
        print(f"Agent {self.idRobot} is looking for pair")
        path = self.pathfinder.aStar(start, pairPOS)
        # path = pair.pathfinder.aStar(start, pairPOS)
        print("ONE DEATH PATH", path)
        goal = pairPOS
        print("ONE DEATH GOAL", goal, "...........................................................")

        if not path or not goal:
            print(f"[Agente {self.idRobot}] No hay POI accesible")
            path = []
            return

        if path and goal:
            for (x,y), action in path:
                if self.actionPoints <= 0:
                    break

                if action == 'move':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.move(d)
                            print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                            heuristic = self.pathfinder.heuristic(start, pairPOS)
                            if heuristic < 2:
                                self.inAmbulance = False
                            break
                elif action == 'putOutFire':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.extinguishFireFull(d)
                            self.move(d)
                            print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                            break
                elif action == 'putOutSmoke':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.stopFire(d)
                            self.move(d)
                            print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                            break
                elif action == 'partiallyPutOutFire':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.stopFire(d)
                            self.move(d)
                            print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                            break
                elif action == 'openDoor':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.openDoor(d)
                            self.move(d)
                            print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                            break
                elif action == 'knowckDownWall':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.breakWall(d)
                            self.move(d)
                            print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                            break
                elif action == 'moveToFire':
                    dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                    for d, (dy, dx) in enumerate(dirs):
                        if self.positionY + dy == y and self.positionX + dx == x:
                            moved = self.move(d)
                            print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                            break

    def savePoiNoMatterWhat(self, start, pair, pairPOS):
        print("SAVE POI ENTRO !!!!!!!!---------------------------------------------------------------------------------")
        if self.inAmbulance == True and pair.carriesPOI == True:
            # find path to one another
            print("Entro get one death out :)")
            print(f"Agent {self.idRobot} is looking for pair")
            path = self.pathfinder.aStar(start, pairPOS)
            print("Pair PATH", path)
            goal = pairPOS
            print("PRINT FIND PAIR", goal, "...........................................................")

            if not path or not goal:
                print(f"[Agente {self.idRobot}] No hay POI accesible")
                path = []
                return

            if path and goal:
                print("PARTH", path)
                print("GOAL:", goal)

                for (x,y), action in path:
                    if self.actionPoints <= 0:
                        break

                    if action == 'move':
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.move(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                heuristic = self.pathfinder.heuristic(start, pairPOS)
                                if heuristic < 2:
                                    self.inAmbulance = False
                                break
                    elif action == 'putOutFire':
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.extinguishFireFull(d)
                                self.move(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
                    elif action == 'putOutSmoke':
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.stopFire(d)
                                self.move(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
                    elif action == 'partiallyPutOutFire':
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.stopFire(d)
                                self.move(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
                    elif action == 'openDoor':
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.openDoor(d)
                                self.move(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
                    elif action == 'knowckDownWall':
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.breakWall(d)
                                self.move(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
                    elif action == 'moveToFire':
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.move(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
        elif self.carriesPOI == True and pair.inAmbulance == True:
            self.saveVictim()

    def reunite(self,start, pair, pairPOS):
        if self.inAmbulance and pair.inAmbulance:
            print("Entro get reunite LOLOLOLOLOLOOLLOOlololololololololOOLLOLOLOLOL")
            print(f"Agent {self.idRobot} is looking for pair")
            path = self.pathfinder.aStar(start, pairPOS)
            print("REUNITE PATH", path)
            goal = pairPOS
            print("REUNITE", goal, "...........................................................")

            if not path or not goal:
                print(f"[Agente {self.idRobot}] No hay PATH A REUNITE accesible")
                path = []
                return

            if path and goal:
                # print("PARTH", path)
                # print("GOAL:", goal)

                for (x,y), action in path:
                    if self.actionPoints <= 0:
                        break
                    self.do_actions(x, y, action)

    def estrategyActions(self):
        print("ENTRO AL ESTRATEGY ACTIONS-------------------------------------------------")
        print("FUEGOS", self.model.firePositions)
        print("ESTADO", self.carriesPOI)
        print("POIS", self.model.poiPositions)
        pair = self.model.getPair(self.idRobot)
        pairPOS = self.model.getPosPair(self.idRobot)
        print("ESTRATEGY PAIR POS: ", pairPOS)
        yMine,xMine = self.positionY, self.positionX
        xPair, yPair = pairPOS
        pairPosYX = yPair, xPair
        minePosYX = yMine, xMine
        print("in ambulance:", self.idRobot,self.inAmbulance)

        # self.exploreEstrategy(minePosYX, pair, pairPosYX)
        if (self.inAmbulance == True and pair.inAmbulance == True):
            self.reunite(minePosYX, pair, pairPosYX)

        elif (self.inAmbulance == True or pair.inAmbulance == True) and (self.carriesPOI == False and pair.carriesPOI == False):
            print(self.inAmbulance, "IN ONE DEATH")
            self.onedeath(minePosYX, pair, pairPosYX)

        elif (self.inAmbulance == True or pair.inAmbulance == True) and (self.carriesPOI == True or pair.carriesPOI == True):
            print("ENTRO A UNO POI OTRO MUERTO")
            self.savePoiNoMatterWhat(minePosYX, pair, pairPosYX)

        elif (self.carriesPOI == True and pair.carriesPOI == False) or (self.carriesPOI == False and pair.carriesPOI == True):
            self.getVictimOUT(minePosYX, pair, pairPosYX)

        elif (self.carriesPOI == False and pair.carriesPOI == False):
            print("[DEBUG]AMBOS SON FALSO")
            self.exploreEstrategy(minePosYX, pair, pairPosYX)

    def aStar(self):
        if self.carriesPOI != True:
            pathPOI, goal = self.pathfinder.closestPOI()
            print("Entro al estrategy Action: ", pathPOI)

            if not pathPOI or not goal:
                print(f"[Agente {self.idRobot}] No hay POI accesible")
                return

            if pathPOI and goal:
                print("PARTH", pathPOI)
                print("GOAL:", goal)

                for (x,y), action in pathPOI:
                    if self.actionPoints <= 0:
                        break
                    
                    if action == 'move':
                        # revisar qué dirección corresponde
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.move(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
                    elif action == 'putOutFire':
                        # revisar qué dirección corresponde
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.extinguishFireFull(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
                    #elif action == 'putOutSmoke':
                    elif action == 'openDoor':
                        # revisar qué dirección corresponde
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.openDoor(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
                    elif action == 'knowckDownWall':
                        # revisar qué dirección corresponde
                        dirs = [(-1,0), (0,1), (1,0), (0,-1)]  # N, E, S, O
                        for d, (dy, dx) in enumerate(dirs):
                            if self.positionY + dy == y and self.positionX + dx == x:
                                moved = self.breakWall(d)
                                print(f"[Agente {self.idRobot}] se movió a {(x, y)} -> {moved}")
                                break
        else:
            self.saveVictim()

    def step(self):
        # Reinicia PA y ejecuta hasta agotarlos
        self.actionPoints = 4

        if self.model.randomStatus == True:
            print("Entro a random to model")
            if self.carriesPOI:
                self.saveVictim()
            else:
                self.actions()
        else:
            print("Not RANDOM: ", self.model.randomStatus)
            self.estrategyActions()
            # self.aStar()

