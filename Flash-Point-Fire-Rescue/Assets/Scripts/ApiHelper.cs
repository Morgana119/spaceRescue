using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
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
    public float actionDelay = 0.3f;
    public GridFireManager gridFireManager;
    public DoorsManager doorsManager;
    public AgentManager agentManager; 

    public FullStatePayload lastFullState;

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
                    var agentActions = lastFullState.actions.Where(a => a.source == "agent").ToArray();
                    var modelActions = lastFullState.actions.Where(a => a.source == "model").ToArray();

                    foreach (var act in agentActions)
                    {   
                        Debug.Log($"[ApiHelper] Acción recibida: {act.action} en ({act.x},{act.y}) desde {act.source}");
                        ApplyAgentAction(act);
                        yield return new WaitForSeconds(actionDelay);
                    }

                    foreach (var act in modelActions)
                    {   
                        Debug.Log($"[ApiHelper] Acción recibida: {act.action} en ({act.x},{act.y}) desde {act.source}");
                        ApplyModelAction(act);
                        yield return new WaitForSeconds(actionDelay);
                    }
                }
            }
        }
    }

    void ApplyAgentAction(ActionPayload act)
    {
        if (agentManager == null) return;

        if (act.action == "extinguish")
            gridFireManager.ApplyChange("extinguish", act.x, act.y);
        else if (act.action == "smoke")
            gridFireManager.ApplyChange("smoke", act.x, act.y);
        else if (act.action == "stopSmoke")
            gridFireManager.ApplyChange("stopSmoke", act.x, act.y);
        else if (act.action == "weakenWall")
            Debug.Log($"Direccion: {act.direction}");
        else if (act.action == "openDoor" ) {
            Debug.Log(($"Direccion: {act.direction}"));
            doorsManager.OpenDoor(act.x, act.y, act.direction);
        }
    }

    void ApplyModelAction(ActionPayload act)
    {
        if (gridFireManager == null) return;

        if (act.action == "ignite")
            gridFireManager.ApplyChange("fire", act.x, act.y);
        else if (act.action == "smoke")
            gridFireManager.ApplyChange("smoke", act.x, act.y);
        else if (act.action == "stopSmoke")
            gridFireManager.ApplyChange("stopSmoke", act.x, act.y);
        else if (act.action == "extinguish")
            gridFireManager.ApplyChange("extinguish", act.x, act.y);
        else if (act.action == "openDoor" ) {
            Debug.Log(($"Direccion: {act.direction}"));
            doorsManager.OpenDoor(act.x, act.y, act.direction);
        } else if (act.action == "weakenWall")
            Debug.Log($"Direccion: {act.direction}");
            
    }

}