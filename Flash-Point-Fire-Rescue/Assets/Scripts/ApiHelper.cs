using UnityEngine;
using UnityEngine.Networking;
using System.Collections;   // ← necesario para IEnumerator
using System.Linq;

[System.Serializable]
public class ActionPayload
{
    public string source;
    public string action;
    public int x;
    public int y;
    public string agent;
    public string kind;
    public int direction;
}

[System.Serializable]
public class FullStatePayload
{
    public ActionPayload[] actions;
}

public class ApiHelper : MonoBehaviour
{
    public string url = "http://127.0.0.1:5000";
    public float updateInterval = 2f;
    public float actionDelay = 0.3f;     // pausa entre acciones normales
    public float pauseAfterMove = 0.3f;  // pausa extra tras terminar un movimiento

    public GridFireManager gridFireManager;
    public DoorsManager doorsManager;
    public AgentManager agentManager;
    public WallsManager wallsManager;

    public FullStatePayload lastFullState;
    public float groupPause = 0.25f; // pausa entre tipos de acciones


    void Start()
    {
        StartCoroutine(LoopUpdate());
    }

    IEnumerator LoopUpdate()
    {
        while (true)
        {
            yield return StartCoroutine(GetFullState());
            yield return new WaitForSeconds(updateInterval);
        }
    }

    public IEnumerator GetFullState()
    {
        string web_url = url + "/state";
        using (UnityWebRequest webRequest = UnityWebRequest.Get(web_url))
        {
            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.ConnectionError ||
                webRequest.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError("Error: " + webRequest.error);
            }
            else
            {
                string jsonResponse = webRequest.downloadHandler.text.Trim();
                lastFullState = JsonUtility.FromJson<FullStatePayload>(jsonResponse);

                if (lastFullState != null && lastFullState.actions != null)
                {
                    var agentActions = lastFullState.actions
                        .Where(a => a.source != null && a.source.ToLowerInvariant() == "agent")
                        .ToArray();

                    var modelActions = lastFullState.actions
                        .Where(a => a.source != null && a.source.ToLowerInvariant() == "model")
                        .ToArray();
                    
                    var initialActions = lastFullState.actions
                        .Where(a => a.source != null && a.source.ToLowerInvariant() == "initial")
                        .ToArray();

                    // 1) INIT
                    foreach (var act in initialActions)
                    {
                        Debug.Log($"[ApiHelper] INIT: {act.action} ({act.x},{act.y})");
                        yield return StartCoroutine(ApplyInitialAction(act));
                    }
                    // Barrera: espera a que todo esté idle y luego pausa breve
                    yield return StartCoroutine(agentManager.WaitForAllAgentsIdle());
                    yield return new WaitForSeconds(groupPause);

                    // 2) AGENT
                    foreach (var act in agentActions)
                    {
                        Debug.Log($"[ApiHelper] AGENT: {act.action} ({act.x},{act.y})");
                        yield return StartCoroutine(ApplyAgentAction(act)); // move ya espera a terminar
                    }
                    // Barrera entre grupos
                    yield return StartCoroutine(agentManager.WaitForAllAgentsIdle());
                    yield return new WaitForSeconds(groupPause);

                    // 3) MODEL
                    foreach (var act in modelActions)
                    {
                        Debug.Log($"[ApiHelper] MODEL: {act.action} ({act.x},{act.y})");
                        yield return StartCoroutine(ApplyModelAction(act));
                    }
                }
            }
        }
    }

    // ===== Corrutinas de aplicación de acciones =====

    IEnumerator ApplyAgentAction(ActionPayload act)
    {
        if (agentManager == null) yield break;

        if (act.action == "extinguish")
        {
            gridFireManager.ApplyChange("extinguish", act.x, act.y);
            yield return new WaitForSeconds(actionDelay);
        }
        else if (act.action == "smoke")
        {
            gridFireManager.ApplyChange("smoke", act.x, act.y);
            yield return new WaitForSeconds(actionDelay);
        }
        else if (act.action == "stopSmoke")
        {
            gridFireManager.ApplyChange("stopSmoke", act.x, act.y);
            yield return new WaitForSeconds(actionDelay);
        }
        else if (act.action == "weakenWall")
        {
            wallsManager.DamageWall(act.x, act.y, act.direction);
            yield return new WaitForSeconds(actionDelay);
        }
        else if (act.action == "breakWall")
        {
            wallsManager.BreakWall(act.x, act.y, act.direction);
            yield return new WaitForSeconds(actionDelay);
        }
        else if (act.action == "openDoor")
        {
            doorsManager.OpenDoor(act.x, act.y, act.direction);
            yield return new WaitForSeconds(actionDelay);
        }
        else if (act.action == "move")
        {
            // 1) iniciar movimiento
            agentManager.MoveAgentTo(act.agent, act.x, act.y);

            // 2) esperar a que ese agente termine de moverse
            yield return StartCoroutine(agentManager.WaitUntilIdle(act.agent));

            // 3) pausa extra de respiro
            yield return new WaitForSeconds(pauseAfterMove);
        }
        else
        {
            // acción desconocida: respeta pacing
            yield return new WaitForSeconds(actionDelay);
        }
    }

    IEnumerator ApplyModelAction(ActionPayload act)
    {
        if (gridFireManager == null) yield break;

        if (act.action == "ignite")
            gridFireManager.ApplyChange("fire", act.x, act.y);
        else if (act.action == "smoke")
            gridFireManager.ApplyChange("smoke", act.x, act.y);
        else if (act.action == "stopSmoke")
            gridFireManager.ApplyChange("stopSmoke", act.x, act.y);
        else if (act.action == "extinguish")
            gridFireManager.ApplyChange("extinguish", act.x, act.y);
        else if (act.action == "openDoor")
            doorsManager.OpenDoor(act.x, act.y, act.direction);
        else if (act.action == "weakenWall")
            wallsManager.DamageWall(act.x, act.y, act.direction);
        else if (act.action == "breakWall")
            wallsManager.BreakWall(act.x, act.y, act.direction);
        

        yield return new WaitForSeconds(actionDelay);
    }

    IEnumerator ApplyInitialAction(ActionPayload act)
    {
        if (agentManager == null) yield break;

        if (act.action == "placeRobot")
            agentManager.SetAgentPosition(act.agent, act.x, act.y);
        // else if (act.action == "placePOI")
        //     agentManager.SetPOI(act.agent, act.x, act.y);

        yield return new WaitForSeconds(actionDelay);
    }
}
