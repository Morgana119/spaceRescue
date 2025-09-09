from heapq import heappush, heappop

class Pathfinder:
    def __init__(self, agent):
        self.agent = agent # instancia de robot agente
        self.model = agent.model # instancia del modelo
    
    def getNeighbors(self, pos):
        y, x = pos
        dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # N, E, S, O
        neighbors = []

        for d, (dy,dx) in enumerate(dirs):
            new_y, new_x = y + dy, x + dx            
            # 1. Verificar que esté dentro del grid
            if not (0 <= new_y < self.model.height and 0 <= new_x < self.model.width):
                continue

            # 2. Validar paredes solo si estamos dentro
            if (self.model.grid[y][x].walls[d] != 0):
                continue

            #print("Valida:", new_y, new_x)
            dest = self.model.grid[new_y][new_x]
            if dest.fire and self.agent.carriesPOI:
                #print(self.agent.idRobot, "LLEVO POI Y HAY FUEGO", flush=True)
                continue
    

            # agregar vecino como válido
            neighbors.append(((new_y, new_x), d))  
        # print(self.agent.rolRobot, self.agent.idRobot,"NEIGHBORS: ", neighbors)      
        return neighbors
    
    def heuristic(self, pos, goal):
        (y1, x1) = pos
        (y2, x2) = goal
        return abs(x2 - x1) + abs(y2 - y1)  # Manhattan
    
    def choose_best_action(self, possible_actions, ny, nx):
        # print("Entro al choose", flush=True)
        # 0 -> apagaFuegos | 1 -> salvaVidas
        # acción : (costo_apagaFuego, costo_salvavida)
        act_priority = {
            'extinguir_llamas': (1, 4),         
            'extinguir_humo': (2, 5),           
            'moverse': (3, 1),                  
            'abrir_puerta': (4, 3),            
            'extinguir_llamas_parcialmente': (5, 6),
            'moverse_a_llamas': (6, 7), 
            'dañar_una_pared': (7, 8),     
            'derribar_pared' : (8, 9)
        }

        best_action = None
        best_priority = float("inf")

        for action in possible_actions:
            if self.agent.rolRobot == 0:  # apagaFuegos
                priority = act_priority[action][0]
                # if ny==5 and nx==3:
                #     print("ENtro a choose apaga Fuegos", ny, nx, priority)
                    
            elif self.agent.rolRobot == 1:  # salvaVidas
                priority = act_priority[action][1]
                # if ny==5 and nx==3:
                #     print("ENtro a choose SV", ny, nx, priority)


            if priority < best_priority:
                best_priority = priority
                best_action = action

        # fallback (never return None)
        # if best_action is None:
        #     best_action = "moverse"

        # print(f"[RESULT] Agent {self.agent.idRobot} | Best priority: {best_priority} | Best action: {best_action} | POS: {self.agent.positionY, self.agent.positionX} | PÄRA {ny, nx}", flush=True)
        # if ny==5 and nx==3:
        #     print("Best action choosed", best_action, ny, nx)
        return best_action

       
    def aStar(self, start, goal):
        # print(self.agent.idRobot, "ENTRO AL A*")
        openSet = []
        closedSet = set()           
        heappush(openSet, (0, start))
        cameFrom = {}  # ahora guarda: { nodo: (padre, acción) }
        gScore = {start : 0}
        # print("Fuegos: ", self.agent.model.firePositions, flush=True)

        while openSet:
            # print("Open set: ", openSet, "------------------------------------------------------", flush=True)
            _, (x,y)= heappop(openSet)
            # print(x, y, "CURRRR-------------------")
            currentNode = x, y
            # print("CURENT:NODE: ", currentNode, "------------------------------------------------", flush=True)
            # print("Closed set: ", closedSet, "---------------------------------------------------", flush=True)
            cy, cx = currentNode
            cell_current = self.model.grid[cy][cx]

            # Guardar la acción junto con la posición

            if currentNode == goal:
                path = []
                while currentNode in cameFrom:
                    parent, action = cameFrom[currentNode]
                    path.append((currentNode, action))
                    currentNode = parent
                path.reverse()
                return path

            best_action = None
            for (neighbor, d) in self.getNeighbors(currentNode):
                # print("Neighbor", neighbor, "--------------------------------------------------------------------------", flush=True)
                #costo de moverse a la celda (igual que en move)
                ny, nx = neighbor

                for (pos, act) in closedSet:
                    if pos == (ny, nx):
                        # print("Entro al closed set con:", ny, nx, act)
                        continue
                
                cell = self.model.grid[ny][nx]
                # if ny==5 and nx==3:
                #     print(self.agent.model.firePositions)
                #     print("Cell", ny, nx, "Fire:",cell.fire,"Smoke", cell.smoke,possible_actions,  flush=True)
                

                if self.agent.model.randomStatus: 
                    # print("Entro al random")
                    # Para comportamiento aleatorio, solo usamos costo directo
                    if self.agent.rolRobot == 1: 
                        cost = 2 if cell.fire or self.agent.carriesPOI else 1
                        best_action = None
                else:
                    # print("Entro al no random")
                    # Aquí sigue la lógica de prioridad y costo real según rol
                    
                    possible_actions = []
                    if cell.fire:
                        possible_actions += ['extinguir_llamas', 'moverse_a_llamas', 'extinguir_llamas_parcialmente']
                        # if ny==5 and nx==3:
                        #     print("Cell.fire", ny, nx, cell.fire,possible_actions,  flush=True)
                    elif cell.smoke:
                        # print("Cell smoke", nx, ny, cell.smoke, flush=True)
                        possible_actions.append('extinguir_humo')
                        # if ny==5 and nx==3:
                        #     print("Cell.smoke", ny, nx, cell.smoke,possible_actions,  flush=True)
                    elif cell.fire == False and cell.smoke == False:
                        # print("Entro aqui", flush=True)
                        possible_actions += ['moverse', 'abrir_puerta', 'derribar_pared']
                        # if ny==5 and nx==3:
                        #     print("Cell alone", ny, nx,possible_actions,  flush=True)
                    # print(self.agent.model.firePositions, "FIRE POSITIONS -------------------------------------------------------------------------------------------------", flush=True)
                    best_action = self.choose_best_action(possible_actions, ny, nx)
                    # if ny==5 and nx==3:
                    #     print("Best action:", best_action, "-------------------------------------------------------------")

                    # acción : (costo_apagaFuego, costo_salvavida)
                    action_cost = {
                        'extinguir_llamas': 2,         
                        'extinguir_humo':1,           
                        'moverse': 1,                  
                        'abrir_puerta': 1,         
                        'extinguir_llamas_parcialmente': 1,
                        'moverse_a_llamas': 2,       
                        'derribar_pared' : 4
                    }[best_action]

                # print("Besct cost: ", bestcost)
                # cost = bestcost
                tentativeG = gScore[currentNode] + action_cost
                
                # print("Posible actions: ", possible_actions)

                if neighbor not in gScore or tentativeG < gScore[neighbor]:
                    # print(neighbor,"-------------------------------------------#####", flush=True)
                    if neighbor in closedSet:  # <-- revisar primero
                        # print("ALREADY IN SET")
                        continue
                    gScore[neighbor] = tentativeG
                    fScore = tentativeG + self.heuristic(neighbor, goal)
                    heappush(openSet, (fScore, neighbor))
                    cameFrom[neighbor] = (currentNode, best_action) 
                    closedSet.add((currentNode, best_action))
        return None       
    
    def closestExit(self):
        print(self.agent.idRobot,"Entro al closes Exit", flush=True)
        print("PUNTOS DE ACCION ",self.agent.actionPoints)
        print("POI", self.model.poisOnBoard)
        exits = self.agent.model.exitPositions

        if (self.agent.positionY, self.agent.positionX) in exits:
            print(f"Agente {self.agent.idRobot} YA ESTÁ en una salida -> no busca más")
            return None, (self.agent.positionY, self.agent.positionX)
        
        min_path = None
        exit_final = None

        for exitPos in exits:
            path = self.aStar((self.agent.positionY, self.agent.positionX), exitPos)
            if path:
                if min_path is None or len(path) < len(min_path):
                    exit_final = exitPos
                    min_path = path
        
        print("ROL", self.agent.idRobot, "MIN PATH: ", min_path, "desde", self.agent.positionY, self.agent.positionX, "hasta:", exit_final, flush=True)
        print("Fuegos: ", self.agent.model.firePositions)
        return min_path, exit_final

    ## Encontrar un POI
    def closestPOI(self):
        print("Entro al closest POI")
        pois = self.agent.model.poisOnBoard

        if (self.agent.positionY, self.agent.positionX) in pois:
            print(f"POI {self.agent.idRobot} YA ESTÁ en un poi -> no busca más")
            return None, (self.agent.positionY, self.agent.positionX)
        
        min_path = None
        final_poi = None

        # print(">>> Revisión de consistencia fuego:")
        # for (fy, fx) in self.agent.model.firePositions:
        #     print((fy, fx), "->", self.model.grid[fy][fx].fire)

        for poi in pois:
            path = self.aStar((self.agent.positionY, self.agent.positionX), poi)
            if path:
                if min_path is None or len(path) < len(min_path):
                    final_poi = poi
                    min_path = path
        print("ROL", self.agent.rolRobot,"MIN PATH: ", min_path, "desde", self.agent.positionY, self.agent.positionX, "hasta:", final_poi, flush=True)
        print("Fuegos: ", self.agent.model.firePositions, flush=True)
        # print(">>> Revisión de consistencia fuego:")
        # for (fy, fx) in self.agent.model.firePositions:
        #     print((fy, fx), "->", self.model.grid[fy][fx].fire)
        return min_path, final_poi

