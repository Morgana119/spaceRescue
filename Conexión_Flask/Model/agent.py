class Agent:
    def __init__(self):
        self.x = 0
        self.y = 0

    def move_forward(self):
        self.y += 1  # ejemplo: mover hacia adelante en eje Y

    def move_left(self):
        self.x -= 1

    def move_right(self):
        self.x += 1

    def get_state(self):
        return {"x": self.x, "y": self.y}

# Instancia global del agente
agent = Agent()
