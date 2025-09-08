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
        return neighbors
    
    def heuristic(self, pos, goal):
        (y1, x1) = pos
        (y2, x2) = goal
        return abs(x2 - x1) + abs(y2 - y1)  # Manhattan
       
    def aStar(self, start, goal):
        print(self.agent.idRobot, "ENTRO AL A*")
        openSet = []
        
        heappush(openSet, (0, start))
        cameFrom = {}  # ahora guarda: { nodo: (padre, acción) }
        gScore = {start : 0}
        cost = 0

        # acción : (costo_apagaFuego, costo_salvavida)
        act_priority = {
            'extinguir_llamas': (1, 4),         
            'extinguir_humo': (2, 5),           
            'moverse': (3, 1),                  
            'abrir_puerta': (4, 3),            
            'extinguir_llamas_parcialmente': (5, 6),
            'moverse_a_llamas': (6, 7),       
            'derribar_pared' : (7, 8)
        }

        # acción : (costo_apagaFuego, costo_salvavida)
        action_cost = {
            'extinguir_llamas': 2,         
            'extinguir_humo':1,           
            'moverse': 1,                  
            'abrir_puerta': 1,         
            'extinguir_llamas_parcialmente': 1,
            'moverse_a_llamas': 2,       
            'derribar_pared' : 4
        }

        while openSet:
            _, currentNode = heappop(openSet)

            if currentNode == goal:
                path = []
                while currentNode in cameFrom:
                    parent, action = cameFrom[currentNode]
                    path.append((currentNode, action))
                    currentNode = parent
                path.reverse()
                return path

            best_priority = float('inf')
            best_action = None

            for (neighbor, d) in self.getNeighbors(currentNode):
            

                #costo de moverse a la celda (igual que en move)
                ny, nx = neighbor
                #print("neigbhor: ", ny, nx, " ", d, flush=True)
                cell = self.model.grid[ny][nx]

                if self.agent.model.randomStatus: 
                    # Para comportamiento aleatorio, solo usamos costo directo
                    if self.agent.rolRobot == 1: 
                        cost = 2 if cell.fire or self.agent.carriesPOI else 1
                        best_action = 'moverse'
                else:
                    # Aquí sigue la lógica de prioridad y costo real según rol
                    possible_actions = []
                    if cell.fire:
                        possible_actions.append('extinguir_llamas')
                        possible_actions.append('moverse_a_llamas')  
                    if cell.smoke:
                        possible_actions.append('extinguir_humo')
                    possible_actions.append('moverse')
                    possible_actions.append('abrir_puerta')
                    possible_actions.append('derribar_pared')
                    possible_actions.append('extinguir_llamas_parcialmente')
                    
                    for action_name in possible_actions:
                        # 0 -> apagaFuegos | 1 -> salvaVidas
                        priority = act_priority[action_name][0] if self.agent.rolRobot == 1 else act_priority[action_name][1]

                        if priority < best_priority:
                            best_priority = priority
                            best_action = action_name
                            
                    bestcost = action_cost[best_action]
                    cost = bestcost

                tentativeG = gScore[currentNode] + cost

                if neighbor not in gScore or tentativeG < gScore[neighbor]:
                    gScore[neighbor] = tentativeG
                    fScore = tentativeG + self.heuristic(neighbor, goal)
                    heappush(openSet, (fScore, neighbor))
                    #print(f"Expand {currentNode} -> {neighbor}, acción={best_action}, g={tentativeG}, h={self.heuristic(neighbor, goal)}, f={fScore}", flush=True)
                    cameFrom[neighbor] = (currentNode, best_action) 
        return None       
    
    def closestExit(self):
        print(self.agent.idRobot,"Entro al closes Exit", flush=True)
        print("PUNTOS DE ACCION ",self.agent.actionPoints)
        exits = self.agent.model.exitPositions

        if (self.agent.positionY, self.agent.positionX) in exits:
            print(f"Agente {self.agent.idRobot} YA ESTÁ en una salida -> no busca más")
            return None, (self.agent.positionY, self.agent.positionX)
        
        min_path = None
        exit_final = None

        for exitPos in exits:
            path = self.aStar((self.agent.positionY, self.agent.positionX), exitPos)
            if path:
                if  min_path is None or len(path) < len(min_path):
                    exit_final = exitPos
                    min_path = path
        
        print("MIN PATH: ", min_path, "desde", self.agent.positionY, self.agent.positionX, "hasta:", exit_final, flush=True)
        return min_path, exit_final

    ## Encontrar un POI
    # def closestPOI(self):

