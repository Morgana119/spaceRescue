using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;

public class AgentPayload {
    public string name;
    public int x;
    public int y;
    public int z;
}

[System.Serializable]
public class ChangePayload {
    public string type; // "fire" o "smoke"
    public int x;
    public int y;
}

[System.Serializable]
public class FullStatePayload {
    public List<AgentPayload> agents;
    public List<ChangePayload> changes;
}
