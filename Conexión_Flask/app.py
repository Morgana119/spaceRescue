from flask import Flask, jsonify
from Controller.agent_controller import agent_bp

app = Flask(__name__)
app.register_blueprint(agent_bp)

@app.route("/")
def index():
    return jsonify("Ya funciona")

if __name__ == "__main__":
    app.run()

