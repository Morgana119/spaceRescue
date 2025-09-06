using UnityEngine;
using UnityEngine.Networking;
using System.Collections;

[System.Serializable]
public class ActionPayload {
    public string source;
    public string action;
    public int x;
    public int y;
}

[System.Serializable]
public class FullStatePayload {
    public ActionPayload[] actions;
}

public class ApiHelper : MonoBehaviour {
    public string url = "http://127.0.0.1:5000";
    public float updateInterval = 2f;           // aparecerá
    public float actionDelay = 0.3f;            // aparecerá
    public GridFireManager gridFireManager; 

    public FullStatePayload lastFullState;

    void Start() {
        StartCoroutine(LoopUpdate());
    }

    IEnumerator LoopUpdate() {
        while (true) {
            yield return StartCoroutine(GetFullState());
            yield return new WaitForSeconds(updateInterval);
        }
    }

    public IEnumerator GetFullState() {
        string web_url = url + "/state";
        using (UnityWebRequest webRequest = UnityWebRequest.Get(web_url)) {
            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.ConnectionError ||
                webRequest.result == UnityWebRequest.Result.ProtocolError) {
                Debug.LogError("Error: " + webRequest.error);
            } else {
                string jsonResponse = webRequest.downloadHandler.text.Trim();
                lastFullState = JsonUtility.FromJson<FullStatePayload>(jsonResponse);

                if (lastFullState != null && lastFullState.actions != null) {
                    foreach (var act in lastFullState.actions) {
                        Debug.Log($"Acción recibida: {act.action} en ({act.x},{act.y})");

                        if (gridFireManager != null) {
                            if (act.action == "ignite") {
                                gridFireManager.ApplyChange("fire", act.x, act.y);
                            } else if (act.action == "smoke") {
                                gridFireManager.ApplyChange("smoke", act.x, act.y);
                            }
                        }

                        // ⏱️ espera antes de aplicar la siguiente acción
                        yield return new WaitForSeconds(actionDelay);
                    }
                }
            }
        }
    }
}
