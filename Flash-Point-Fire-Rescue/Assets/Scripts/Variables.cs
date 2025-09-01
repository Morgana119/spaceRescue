// Esta etiqueta indica que la clase puede ser convertida a JSON y viceversa
[System.Serializable]  

// Clase que representa las variables de posición del agente
public class Variables
{
    public float x;
    public float y;
}

// Clase que representa los datos de una acción enviada al servidor para el POST
public class ActionData
{
    public string action;
}