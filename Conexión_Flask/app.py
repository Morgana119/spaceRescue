from flask import Flask
from Controller.agent_controller import agent_bp

app = Flask(__name__)
app.register_blueprint(agent_bp)

if __name__ == "__main__":
    app.run(debug=True)
