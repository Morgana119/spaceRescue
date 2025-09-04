# Importamos las librerías necesarias
from flask import Blueprint, jsonify, request
# from Model.agent import Model  # diccionario con todos los agentes
from Model.agentes import ExplorerModel


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

# Ruta para mover todos los agentes a la vez
'''
@agent_bp.route("/move/agents", methods=["GET"])
def all_agents_pos():
    # por cada agente se llama el metodo get_next_position()
    for ag in agents.values():
        ag.get_next_position()

    # Se agrega a un diccionario el estado actual que tiene   
    payload = {'agents' : [ag.get_state() for ag in agents.values()]}
    # se manda en formato JSON
    return jsonify(payload)
'''

# Agent names
agent_names = ["morado", "rosa", "rojo", "azul", "naranja", "verde"]

# Se inicializa el modelo con esos agentes
# Cada agente recibe un nombre y una posición inicial aleatoria
#model = Model(COLORS)

# ------------------- RUTA FLASK -------------------

# # Ruta para mover agentes: "/move/agents"
# # Método: GET
# @agent_bp.route("/move/agents", methods=["GET"])
# def move_agents_step():
#     # Ejecuta un paso de la simulación
#     # En este paso SOLO se mueve el agente cuyo turno corresponde
#     model.step()
#     # Devuelve en formato JSON las posiciones actualizadas de todos los agentes
#     return jsonify(model.get_payload())
explorer_model = ExplorerModel(agent_names)

@agent_bp.route("/state", methods=["GET"])
def get_state():
    # explorer_model.step()  
    return jsonify(explorer_model.get_full_state())
