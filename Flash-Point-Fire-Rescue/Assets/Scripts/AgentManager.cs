using UnityEngine;
using System.Collections;
using System.Collections.Generic;

[System.Serializable]
public class AgentSlot
{
    public string name;        // "purple", "pink", ...
    public GameObject agent;   // Prefab o instancia en escena
}

public class AgentManager : MonoBehaviour
{
    [Header("Refs")]
    public GameObject firePrefab;

    [Header("Grid")]
    public float cellSize = 4f;
    public float baseY = 0.2f;

    [Header("Speeds")]
    public float defaultMoveSpeed = 2f;
    public float rotationSpeedDeg = 360f;

    [Header("Agents (asignar en Inspector)")]
    public AgentSlot[] agentSlots;

    // Interno: nombre -> GO
    private Dictionary<string, GameObject> agents = new Dictionary<string, GameObject>();
    private readonly Dictionary<string, Coroutine> activeMoves = new Dictionary<string, Coroutine>();

    // Cache offset fire
    private bool hasOffset = false;
    private Vector3 referenceOffset = Vector3.zero;

    void Awake()
    {
        agents.Clear();
        if (agentSlots != null)
        {
            foreach (var s in agentSlots)
            {
                if (s == null || string.IsNullOrWhiteSpace(s.name) || s.agent == null) {
                    Debug.LogWarning("AgentSlot vacío o incompleto en AgentManager.");
                    continue;
                }
                if (agents.ContainsKey(s.name))
                    Debug.LogWarning($"Nombre duplicado '{s.name}' en AgentSlots. Se sobrescribirá la referencia.");

                agents[s.name] = s.agent;
            }
        }
    }

    // ---------- API ----------
    public void SetAgentPosition(string agentName, int x, int y)
    {
        if (!agents.TryGetValue(agentName, out var go))
        {
            Debug.LogWarning($"Agente {agentName} no encontrado.");
            return;
        }
        go.transform.position = GetAlignedPosition(x, y);
    }

    public void MoveAgentTo(string agentName, int x, int y, int direction, float moveSpeed = -1f, float rotSpeedDeg = -1f)
    {
        if (!agents.TryGetValue(agentName, out var go))
        {
            Debug.LogWarning($"Agente {agentName} no encontrado.");
            return;
        }

        if (moveSpeed <= 0f) moveSpeed = defaultMoveSpeed;
        if (rotSpeedDeg <= 0f) rotSpeedDeg = rotationSpeedDeg;

        Vector3 targetPos = GetAlignedPosition(x, y);
        Quaternion targetRot = RotationFromDirection(direction);

        if (activeMoves.TryGetValue(agentName, out var running) && running != null)
            StopCoroutine(running);

        var co = StartCoroutine(MoveThenRotate(agentName, go, targetPos, targetRot, moveSpeed, rotSpeedDeg));
        activeMoves[agentName] = co;
    }

    // ---------- Helpers ----------
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

    private Quaternion RotationFromDirection(int direction)
    {
        // 0=N(+Z), 1=E(+X), 2=S(-Z), 3=O(-X)
        switch ((direction % 4 + 4) % 4)
        {
            case 0: return Quaternion.Euler(0f, 0f, 0f);
            case 1: return Quaternion.Euler(0f, 90f, 0f);
            case 2: return Quaternion.Euler(0f, 180f, 0f);
            case 3: return Quaternion.Euler(0f, -90f, 0f);
        }
        return Quaternion.identity;
    }

    private IEnumerator MoveThenRotate(string agentName, GameObject agent, Vector3 targetPos, Quaternion targetRot, float moveSpeed, float rotSpeedDeg)
    {
        const float posEps = 0.01f;
        const float rotEps = 0.5f;

        while (Vector3.Distance(agent.transform.position, targetPos) > posEps)
        {
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

        if (activeMoves.ContainsKey(agentName)) activeMoves[agentName] = null;
    }

    public IEnumerator WaitUntilIdle(string agentName)
    {
        // Usa la misma clave que empleas en activeMoves (si normalizas el nombre, normaliza aquí también)
        string key = (agentName ?? "").Trim().ToLowerInvariant();

        while (activeMoves.TryGetValue(key, out var co) && co != null)
            yield return null;
    }

    public IEnumerator WaitForAllAgentsIdle()
    {
        // Espera a que no quede NINGÚN movimiento activo
        while (true)
        {
            bool any = false;
            foreach (var kv in activeMoves)
            {
                if (kv.Value != null) { any = true; break; }
            }
            if (!any) break;
            yield return null;
        }
    }
}
