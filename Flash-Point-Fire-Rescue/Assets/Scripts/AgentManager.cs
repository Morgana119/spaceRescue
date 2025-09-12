// AgentManager.cs
using UnityEngine;
using System.Collections;
using System.Collections.Generic;

[System.Serializable]
public class AgentSlot
{
    public string name;
    public GameObject agent;
}

public class AgentManager : MonoBehaviour
{
    [Header("Refs")]
    public GameObject firePrefab;
    public GameObject victim;
    public GameObject falseAlarm;
    public GameObject poi;

    [Header("Grid")]
    public float cellSize = 4f;
    public float baseY = 0.2f;

    [Header("Speeds")]
    public float defaultMoveSpeed = 2f;
    public float rotationSpeedDeg = 360f;

    [Header("Agents")]
    public AgentSlot[] agentSlots;

    private readonly Dictionary<string, GameObject> agents = new Dictionary<string, GameObject>();
    private readonly Dictionary<string, Coroutine> activeMoves = new Dictionary<string, Coroutine>();

    private bool hasOffset = false;
    private Vector3 referenceOffset = Vector3.zero;

    void Awake()
    {
        agents.Clear();
        if (agentSlots == null) return;

        foreach (var s in agentSlots)
        {
            if (s == null || string.IsNullOrWhiteSpace(s.name) || s.agent == null) continue;
            agents[Key(s.name)] = s.agent;
        }
    }

    public void SetAgentPosition(string agentName, int x, int y)
    {
        var key = Key(agentName);
        if (!agents.TryGetValue(key, out var go)) return;

        StopMoveIfAny(key);
        Vector3 basePos = GetAlignedPosition(x, y);
        Vector3 offset = GetAgentOffset(agentName, x, y);
        go.transform.position = basePos + offset;
    }

    public void MoveAgentTo(string agentName, int x, int y, float moveSpeed = -1f, float rotSpeedDeg = -1f)
    {
        var key = Key(agentName);
        if (!agents.TryGetValue(key, out var go)) return;

        if (moveSpeed <= 0f) moveSpeed = defaultMoveSpeed;
        if (rotSpeedDeg <= 0f) rotSpeedDeg = rotationSpeedDeg;

        Vector3 basePos = GetAlignedPosition(x, y);
        Vector3 offset = GetAgentOffset(agentName, x, y);
        Vector3 targetPos = basePos + offset;

        Quaternion targetRot = RotationFromDelta(go.transform.position, targetPos, go.transform.rotation);

        StopMoveIfAny(key);
        activeMoves[key] = StartCoroutine(MoveAndFaceCoroutine(key, go, targetPos, targetRot, moveSpeed, rotSpeedDeg));
    }

    public IEnumerator WaitUntilIdle(string agentName)
    {
        string key = Key(agentName);
        while (activeMoves.TryGetValue(key, out var co) && co != null) yield return null;
    }

    public IEnumerator WaitForAllAgentsIdle()
    {
        while (true)
        {
            bool any = false;
            foreach (var kv in activeMoves) { if (kv.Value != null) { any = true; break; } }
            if (!any) yield break;
            yield return null;
        }
    }

    private string Key(string s) => (s ?? "").Trim().ToLowerInvariant();

    private void StopMoveIfAny(string agentKey)
    {
        if (activeMoves.TryGetValue(agentKey, out var running) && running != null)
        {
            StopCoroutine(running);
            activeMoves[agentKey] = null;
        }
    }

    private Vector3 GetAlignedPosition(int x, int y)
    {
        Vector3 basePos = new Vector3(x * cellSize, baseY, y * cellSize);
        if (!hasOffset && firePrefab != null)
        {
            var temp = Instantiate(firePrefab, basePos, Quaternion.identity);
            referenceOffset = temp.transform.position - basePos;
            hasOffset = true;
            Destroy(temp);
        }
        return basePos + referenceOffset;
    }

    private Quaternion RotationFromDelta(Vector3 current, Vector3 target, Quaternion fallback)
    {
        Vector3 d = target - current;
        float dx = d.x, dz = d.z;

        if (Mathf.Abs(dx) < 1e-4f && Mathf.Abs(dz) < 1e-4f) return fallback;

        if (Mathf.Abs(dx) >= Mathf.Abs(dz))
            return dx > 0f ? Quaternion.Euler(0f, 90f, 0f) : Quaternion.Euler(0f, -90f, 0f);
        else
            return dz > 0f ? Quaternion.Euler(0f, 0f, 0f) : Quaternion.Euler(0f, 180f, 0f);
    }

    private IEnumerator MoveAndFaceCoroutine(string agentKey, GameObject agent, Vector3 targetPos, Quaternion targetRot, float moveSpeed, float rotSpeedDeg)
    {
        const float posEps = 0.01f, rotEps = 0.5f;

        while (Vector3.Distance(agent.transform.position, targetPos) > posEps)
        {
            agent.transform.rotation = Quaternion.RotateTowards(agent.transform.rotation, targetRot, rotSpeedDeg * Time.deltaTime);
            agent.transform.position = Vector3.MoveTowards(agent.transform.position, targetPos, moveSpeed * Time.deltaTime);
            yield return null;
        }
        agent.transform.position = targetPos;

        while (Quaternion.Angle(agent.transform.rotation, targetRot) > rotEps)
        {
            agent.transform.rotation = Quaternion.RotateTowards(agent.transform.rotation, targetRot, rotSpeedDeg * Time.deltaTime);
            yield return null;
        }
        agent.transform.rotation = targetRot;

        activeMoves[agentKey] = null;
    }

    // ---------------- POI ----------------------

    public void SetPOI(int x, int y)
    {
        Vector3 basePosition = new Vector3(x*4, 2f, y*4);

        // Instanciar un fuego temporal SOLO para obtener su posición real
        GameObject fireTemp = Instantiate(firePrefab, basePosition, Quaternion.identity);

        // Tomar esa posición como referencia
        Vector3 position = fireTemp.transform.position;

        Instantiate(poi, position, Quaternion.Euler(0, 90, 0));

        // Eliminar el fuego temporal
        Destroy(fireTemp);
    }

    public void RevealPOIDead(int x, int y, string k)
    {   
        Debug.Log($"ENTRO A REVEAL POI");
        Vector3 basePosition = new Vector3(x*4, 2f, y*4);

        // Instanciar un fuego temporal SOLO para obtener su posición real
        GameObject fireTemp = Instantiate(firePrefab, basePosition, Quaternion.identity);

        // Tomar esa posición como referencia
        Vector3 position = fireTemp.transform.position;
        
        Collider[] colliders = Physics.OverlapSphere(position, 1f); // radio pequeñito
        foreach (Collider col in colliders)
        {
            if (col.CompareTag("poi"))
            {
                Destroy(col.gameObject);
            }
        }
        
        if (k == "V"){
            Instantiate(victim, position, Quaternion.Euler(0, 90, 0));
        }
        else{
            Instantiate(falseAlarm, position, Quaternion.Euler(0, 90, 0));
        }
        // Eliminar el fuego temporal
        Destroy(fireTemp);
    }

    public void RevealPOI(string agentName, int x, int y, string k)
    {
        // 1) limpiar el POI de la celda
        Vector3 cellPos = GetAlignedPosition(x, y);
        foreach (var col in Physics.OverlapSphere(cellPos, 1f))
            if (col.CompareTag("poi")) Destroy(col.gameObject);

        // 2) ubicar el robot desde tu diccionario (todo minúscula)
        if (!agents.TryGetValue(Key(agentName), out var robot) || robot == null)
        {
            Debug.LogWarning($"Robot '{agentName}' no encontrado.");
            return;
        }

        if (k == "V")
        {
            // 3) instanciar como HIJO del robot y posicionar en local Y
            var token = Instantiate(victim);
            // importante: parentear con worldPositionStays = false para trabajar en local
            token.transform.SetParent(robot.transform, worldPositionStays: false);

            // opcional: ajustar escala del token
            token.transform.localScale = new Vector3(0.7f, 0.006f, 0.7f);

            // *** aquí “sube” sobre Y respecto al robot ***
            token.transform.localPosition = new Vector3(0.33f, 1.7f, 0.33f);
        }
        else
        {
            // Falsa alarma: NUNCA hija del robot, solo aparece y se puede borrar
            var fa = Instantiate(falseAlarm, cellPos, Quaternion.Euler(0, 90, 0));
            // si no quieres que quede, elimínala
            Destroy(fa, 2f);
        }
    }


    public void DeadPOI (int x, int y, string k) {
        Vector3 basePosition = new Vector3(x * 4, 2f, y * 4);

        // Instanciar un fuego temporal SOLO para obtener su posición real
        GameObject fireTemp = Instantiate(firePrefab, basePosition, Quaternion.identity);

        // Tomar esa posición como referencia
        Vector3 position = fireTemp.transform.position;

        Collider[] colliders = Physics.OverlapSphere(position, 0.1f); // radio pequeñito
        foreach (Collider col in colliders)
        {
            if (col.CompareTag("victim") || col.CompareTag("falseAlarm") || col.CompareTag("poi")) 
            {
                Destroy(col.gameObject);
            }
        }

        if (k == "V"){
            FindObjectOfType<Counters>().AddLostVictim();
        }
        

        Destroy(fireTemp);
    }

    public void VictimSaved(string agentName)
    {
        GameObject robot = GameObject.Find(agentName);
        if (robot != null)
        {
            Debug.Log("Entro a primer if de VS" + agentName);
            Transform token = robot.GetComponentInChildren<Transform>(true); 
            if (token != null && token.CompareTag("victim"))
            {
                Debug.Log("Entro al segundo if de VS" + agentName);
                token.localScale *= 1.5f;

                StartCoroutine(RemoveVictimAfterDelay(token.gameObject));
            }
            else
            {
                Debug.LogWarning("No se encontró el token Victim dentro de " + agentName);
            }
        }

        FindObjectOfType<Counters>().AddSavedVictim();
    }

    private IEnumerator RemoveVictimAfterDelay(GameObject token)
    {
        yield return new WaitForSeconds(2f);
        Destroy(token);
    }


    private Vector3 GetAgentOffset(string agentName, int x, int y)
    {
        // 🔹 Usamos un diccionario para dar a cada agente un offset único
        int hash = (agentName + x + "_" + y).GetHashCode();
        Random.InitState(hash);

        // Offset pequeño dentro de la celda (ej: 0.3f)
        float maxOffset = 1f;
        float offsetX = Random.Range(-maxOffset, maxOffset);
        float offsetZ = Random.Range(-maxOffset, maxOffset);

        return new Vector3(offsetX, 0f, offsetZ);
}

}
