# Importamos las librerías necesarias
from flask import Blueprint, jsonify, request
from Model.agent import agent # Importamos la instancia global del agente

# Definimos un "Blueprint" llamado agent_bp
# Un Blueprint en Flask sirve para organizar las rutas de manera modular
agent_bp = Blueprint("agent_bp", __name__)

# ------------------- RUTAS -------------------

# Ruta para consultar el estado actual del agente
# Método: GET
@agent_bp.route("/agent/state", methods=["GET"])
def get_agent_state():
    # Devuelve las coordenadas actuales del agente en formato JSON
    return jsonify(agent.get_state())

# Ruta para consultar la posición del agente (y actualizarla aleatoriamente en X)
# Método: GET
@agent_bp.route("/agent/pos", methods=["GET"])
def pos_agent():
    # Modifica la posición X del agente con un movimiento aleatorio
    agent.get_next_position()
    # Devuelve la nueva posición en formato JSON
    return jsonify({"x": agent.x, "y": agent.y})

# Ruta para mover al agente según una acción enviada desde Unity
# Método: POST
@agent_bp.route("/agent/move", methods=["POST"])
def move_agent():
    # Recibimos los datos enviados en formato JSON
    data = request.get_json()
    action = data.get("action")  # Extraemos la acción

    # Ejecutamos la acción según lo que llegue
    if action == "forward":
        agent.move_forward()
    elif action == "left":
        agent.move_left()
    elif action == "right":
        agent.move_right()

    # Regresamos el estado actualizado del agente
    return jsonify(agent.get_state())
