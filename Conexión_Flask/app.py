# Importamos Flask (para crear APIs en Python) y jsonify (para devolver respuestas en formato JSON)
from flask import Flask, jsonify
# Importamos el blueprint que contiene las rutas del agente (controlador separado para mantener el codigo ordenado)
from Controller.agent_controller import agent_bp

# Creamos la aplicación principal de Flask
app = Flask(__name__)

# Registramos el blueprint de las rutas del agente en la app principal
app.register_blueprint(agent_bp)

# Ruta principal de prueba
@app.route("/")
def index():
    return jsonify("API running")

# Punto de entrada de la aplicación
if __name__ == "__main__":
    # Ejecutamos el servidor Flask en el puerto por defecto (5000)
    # Se accede con http://127.0.0.1:5000
    app.run(debug=True)

