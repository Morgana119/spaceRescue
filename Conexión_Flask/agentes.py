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
%matplotlib inline
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






class RobotAgent(Agent):
    def __init__(self, model):
      super().__init__(model)
    
    def step(self):
       print("Agente hizo su step")




class ExplorerModel(Model):
   def __init__(self, width = 6, height = 8):
      super().__init__()
      self.fireGrid = np.zeros((width, height), dtype=int)
      self.wallsGrid = np.zeros((width, height, 5), dtype=int)
      self.agentsGrid = MultiGrid(width, height, torus=False)    
      self.schedule = RandomActivation(self)
      self.numRobots = 6
      self.damagedWalls = 0
      self.savedVictims = 0
      self.randomStatus = True
      self.width = width
      self.height = height
      self.robots = 1
      
      # Se llena el grid de los estados de las paredes
      grid = [
        ["1001", "1000", "1300", "1001", "1100", "4001", "1000", "1100"],
        ["0001", "0000", "0110", "0011", "0310", "0011", "0010", "0130"],
        ["0001", "0300", "1003", "1000", "1000", "1100", "1001", "3100"],
        ["0011", "0110", "0011", "0030", "0010", "0310", "0013", "0410"],
        ["1001", "1000", "1000", "3000", "1100", "1001", "1100", "1101"],
        ["0011", "0010", "0040", "0010", "0310", "0013", "0310", "0113"]
      ]

      self.wallsGrid = np.zeros((width, height, 4), dtype=int)

      for i in range(self.height):
        for j in range(self.width):
           self.wallsGrid[i, j] = [int(d) for d in grid[i][j]]


      # Se llena el grid de fuego con posiciones iniciales
      firePositions = [(2,3), (2,3), (4,5), (4,6), (7,6)]
      for x, y in firePositions:
        self.fireGrid[y,x] = 1 
      

      # pongo un agente de prueba
      i = 0
      while (i < self.robots):
        x = self.random.randrange(self.width)
        y = self.random.randrange(self.height)
        if self.agentsGrid.is_cell_empty( (x, y) ) and self.fireGrid[x, y] != 1:
            agent = RobotAgent(self)
            self.agentsGrid.place_agent(agent, (x, y))
            self.schedule.add(agent)
            i += 1



   def step(self):
      self.schedule.step()
      x,y = self.RollDice()
      self.spreadFire(x, y)

   def RollDice(self,):
      x = self.random.randrange(self.width)
      y = self.random.randrange(self.height)   
      return x, y
   
   def placeFire(self,  y, x, coordinate): 
      if coordinate == 0:
         self.fireGrid[y-1, x] = 1
      elif coordinate == 1:
         self.fireGrid[y, x+1] = 1
      elif coordinate == 2:
         self.fireGrid[y+1, x] = 1
      elif coordinate == 3: 
         self.fireGrid[y, x-1] = 1

   def spreadFire(self, x, y):
      if self.fireGrid[y, x] == 0:
         self.fireGrid[y][x] = 1
      else : # explosion
         for i in range(4):

            # no hay pared ni nada
            if self.wallsGrid[y, x, i] == 0:
               self.placeFire(self, y, x, i)

            # hay una pared completa
            elif self.wallsGrid[y, x, i] == 1:
               # actualizar los vecinos de la pared dañada
               self.wallsGrid[y, x, i] = 2
               self.damagedWalls += 1

            # hay una pared dañada
            elif self.wallsGrid[y, x, i] == 2:
               # ya no hay pared
               # actualizo vecinos que ya no hay pared
               self.wallsGrid[y, x, i] = 0
               self.damagedWalls += 1
            
            # hay una puerta cerrada
            elif self.wallsGrid[y, x, 1] == 3:
               # abro la puerta
               # actualizo vecinos que ya no hay pared
               self.wallsGrid[y, x, i] = 0
    
               
               

         

      
      



