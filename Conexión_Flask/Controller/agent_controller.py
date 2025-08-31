from flask import Blueprint, jsonify, request
from Model.agent import agent

agent_bp = Blueprint("agent_bp", __name__)

# Consultar estado actual
@agent_bp.route("/agent/state", methods=["GET"])
def get_agent_state():
    return jsonify(agent.get_state())

@agent_bp.route("/agent/pos", methods=["GET"])
def pos_agent():
    agent.get_next_position()
    return jsonify({"x": agent.x, "y": agent.y})

# Mandar acción desde Unity
@agent_bp.route("/agent/move", methods=["POST"])
def move_agent():
    data = request.get_json()
    action = data.get("action")

    if action == "forward":
        agent.move_forward()
    elif action == "left":
        agent.move_left()
    elif action == "right":
        agent.move_right()

    return jsonify(agent.get_state())
