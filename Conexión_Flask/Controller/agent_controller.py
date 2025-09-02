# Importamos las librerías necesarias
from flask import Blueprint, jsonify, request
from Model.agent import agents  # diccionario con todos los agentes


# Definimos un "Blueprint" llamado agent_bp
# Un Blueprint en Flask sirve para organizar las rutas de manera modular
agent_bp = Blueprint("agent_bp", __name__)

'''
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

'''

@agent_bp.route("/move/agents", methods=["GET"])
def all_agents_pos():
    for ag in agents.values():
        ag.get_next_position()
    
    payload = {'agents' : [ag.get_state() for ag in agents.values()]}
    return jsonify(payload)
