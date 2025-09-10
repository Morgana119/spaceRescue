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

            if not (0 <= new_y < self.model.height and 0 <= new_x < self.model.width):
                continue

            if (self.model.grid[y][x].walls[d] != 0):
                continue

            dest = self.model.grid[new_y][new_x]
            if dest.fire and self.agent.carriesPOI:
                continue
    

            # agregar vecino como válido
            neighbors.append(((new_y, new_x), d))    
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
            'putOutFire': (1, 4),         
            'putOutSmoke': (2, 5),           
            'move': (3, 1),                  
            'openDoor': (4, 3),            
            'partiallyPutOutFire': (5, 6),
            'moveToFire': (6, 7), 
            'knowckDownWall': (7, 8),  
        }
        best_action = None
        best_priority = float("inf")

        for action in possible_actions:
            #print("DEBUG action:", action, type(action))
            if self.agent.rolRobot == 0:  # apagaFuegos
                priority = act_priority[action][0]
                    
            elif self.agent.rolRobot == 1:  # salvaVidas
                priority = act_priority[action][1]


            if priority < best_priority:
                best_priority = priority
                best_action = action

        # fallback (never return None)
        if best_action is None:
            best_action = "move"

        return best_action

       
    def aStar(self, start, goal):
        # convertir start y goal a (y, x) si vienen como (x, y)
        # heurística rápida: si el primero < altura -> es Y
        y_Start, x_Start = start
        y_goal, x_goal = goal
        
        # print(self.agent.idRobot, "ENTRO AL A*")
        openSet = []
        # closedSet = set()          
        heappush(openSet, (0, (y_Start, x_Start)))
        cameFrom = {}  # ahora guarda: { nodo: (padre, acción) }
        gScore = {(y_Start, x_Start ) : 0}

        while openSet:
            _, (y, x)= heappop(openSet)
            currentNode = y, x
            # if currentNode in closedSet:
            #     print("ALready in clolsed set")
            #     continue
            # closedSet.add(currentNode)

            if currentNode == (y_goal, x_goal):
                path = []
                while currentNode in cameFrom:
                    parent, action = cameFrom[currentNode]
                    y, x = currentNode   # aquí lo tienes como y, x
                    path.append(((x,y), action))  # lo guardas como x, y
                    currentNode = parent
                path.reverse()
                return path

            best_action = None
            for (neighbor, d) in self.getNeighbors(currentNode):
                ny, nx = neighbor

                # for (pos, act) in closedSet:
                #     if pos == (ny, nx):
                #         continue
                # if neighbor in closedSet:
                #     continue
                
                cell = self.model.grid[ny][nx]                

                if self.agent.model.randomStatus: 
                    if self.agent.rolRobot == 1: 
                        action_cost = 2 if cell.fire or self.agent.carriesPOI else 1
                        best_action = 'move'
                    else:
                        # fallback para otros roles
                        action_cost = 1
                        best_action = 'move'
                else:                    
                    possible_actions = []
                    if cell.fire:
                        possible_actions.append('putOutFire') #'moveToFire', 'partiallyPutOutFire']
                    elif cell.smoke:
                        possible_actions.append('putOutSmoke')
                    possible_actions += ['move', 'openDoor', 'knowckDownWall']
                    best_action = self.choose_best_action(possible_actions, ny, nx)
                    action_cost = {
                        'putOutFire': 2,         
                        'putOutSmoke':1,           
                        'move': 1,                  
                        'openDoor': 1,         
                        # 'partiallyPutOutFire': 1,
                        # 'moveToFire': 2,       
                        'knowckDownWall' : 4
                    }[best_action]

                tentativeG = gScore[currentNode] + action_cost

                if neighbor not in gScore or tentativeG < gScore[neighbor]:
                    # if neighbor in closedSet: 
                    #     continue
                    gScore[neighbor] = tentativeG
                    fScore = tentativeG + self.heuristic(neighbor, goal)
                    heappush(openSet, (fScore, neighbor))
                    cameFrom[neighbor] = (currentNode, best_action) 
                    # closedSet.add((currentNode, best_action))
        return None       
    
    def closestExit(self):
        # print(self.agent.idRobot,"Entro al closes Exit", flush=True)
        # print("PUNTOS DE ACCION ",self.agent.actionPoints)
        exits = self.agent.model.exitPositions
        print("CLOSETS EXITS: ", exits, "--------------------------------", flush=True)

        if (self.agent.positionX, self.agent.positionY) in exits:
            # print(f"Agente {self.agent.idRobot} YA ESTÁ en una salida -> no busca más")
            return None, (self.agent.positionX, self.agent.positionY)
        
        arr_YX_Pois = []
        for exit in exits:
            x, y = exit
            arr_YX_Pois.append((y,x))
        print(arr_YX_Pois)
        
        min_path = None
        exit_final = None

        print("Agente POS: ", self.agent.positionY, self.agent.positionX)

        for exitPos in arr_YX_Pois:
            # print("EXITPOS: ", exitPos)
            path = self.aStar((self.agent.positionY, self.agent.positionX), exitPos)
            if path:
                if min_path is None or len(path) < len(min_path):
                    exit_final = exitPos
                    min_path = path

        if exit_final is None:
            print(f"[WARN] Agente {self.agent.idRobot}: no hay camino a ninguna salida desde {self.agent.positionX}, {self.agent.positionY}")
            return None, None   
        
        yFPOI, xFPOI = exit_final
        exit = xFPOI, yFPOI
        print("ROL", self.agent.idRobot, "MIN PATH: ", min_path, "desde", self.agent.positionY, self.agent.positionX, "hasta:",  yFPOI, xFPOI, flush=True)
        print("Fuegos: ", self.agent.model.firePositions)
        return min_path, exit

    ## Encontrar un POI
    def closestPOI(self):
        # print("Entro al closest POI")
        pois = self.agent.model.poiPositions

        if (self.agent.positionY, self.agent.positionX) in pois:
            # print(f"POI {self.agent.idRobot} YA ESTÁ en un poi -> no busca más")
            return None, (self.agent.positionX, self.agent.positionY)
        
        min_path = None
        final_poi = None
        arr_YX_Pois = []

        for poi in pois:
            # print("POI: ", poi)
            x, y = poi
            arr_YX_Pois.append((y,x))
        # print(arr_YX_Pois)

        for poi in arr_YX_Pois:
            path = self.aStar((self.agent.positionY, self.agent.positionX), poi)
            if path:
                if min_path is None or len(path) < len(min_path):
                    final_poi = poi
                    min_path = path

        if final_poi is None:
            # print(f"[WARN] Agente {self.agent.idRobot}: no encontro ningún POI desde {self.agent.positionX}, {self.agent.positionY}")
            return None, None  
        
        yFPOI, xFPOI = final_poi
        final = xFPOI, yFPOI
        # print("ROL", self.agent.rolRobot,"MIN PATH: ", min_path, "desde", self.agent.positionX, self.agent.positionY, "hasta:", xFPOI, yFPOI, flush=True)
        # print("Fuegos: ", self.agent.model.firePositions, flush=True)
        return min_path, final
