// Esta etiqueta indica que la clase puede ser convertida a JSON y viceversa
[System.Serializable]  
// Clase que representa las variables de posición del agente
public class AgentPos
{
    public string name;
    public float x;
    public float y;
}

[System.Serializable]
public class AgentsPayLoad{
    public AgentPos[] agents; 
}

[System.Serializable]
// Clase que representa los datos de una acción enviada al servidor para el POST
public class ActionData
{
    public string action;
}