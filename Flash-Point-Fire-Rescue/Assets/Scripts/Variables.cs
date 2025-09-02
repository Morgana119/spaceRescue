// Esta etiqueta indica que la clase puede ser convertida a JSON y viceversa
[System.Serializable]  
// Clase que representa las variables de posición del agente
public class AgentPos
{
    public string name; // nombre del agente para identificarlo
    public float x; // posicion en x
    public float y; // posicion en y
}

[System.Serializable]
// clase que representa todos los agentes creados 
public class AgentsPayLoad{
    public AgentPos[] agents;  // arreglo de agentes de instancias de la clase AgentPos
}

/*[System.Serializable]
// Clase que representa los datos de una acción enviada al servidor para el POST
public class ActionData
{
    public string action;
}*/