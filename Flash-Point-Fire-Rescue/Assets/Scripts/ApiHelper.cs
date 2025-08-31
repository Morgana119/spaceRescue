using UnityEngine; //Para la clase JsonUtility
using UnityEngine.Networking;
using System.Collections;
using System;

public class ApiHelper : MonoBehaviour
{
    private string url = "http://127.0.0.1:5000";
    public Variables lastPos;

    void Start(){
        StartCoroutine(GetRequest(url));
    }

    IEnumerator GetRequest(string uri){

        string web_url_get = uri + "/agent/state";
        Debug.Log("Get: " + web_url_get);

        using (UnityWebRequest webRequest = UnityWebRequest.Get(web_url_get)){
            yield return webRequest.SendWebRequest();

            if (webRequest.isNetworkError){
                Debug.Log("Error " + webRequest.error); 
            } else {
                Debug.Log(webRequest.downloadHandler.text);
            }
        }
    }

    public IEnumerator pos_agent()
    {
        string web_url_getPos = url + "/agent/pos";
        Debug.Log("Get: " + web_url_getPos);
        using (UnityWebRequest webRequest = UnityWebRequest.Get(web_url_getPos))
        {
            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.ConnectionError ||
                webRequest.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError("Error: " + webRequest.error);
                lastPos = null;
            }
            else
            {
                string jsonResponse = webRequest.downloadHandler.text;
                lastPos = JsonUtility.FromJson<Variables>(jsonResponse);
                Debug.Log($"API x:{lastPos.x}, y:{lastPos.y}");
            }
        }
    }

    IEnumerator MoveAgent(string action, string uri)
    {
        string web_url_post = uri + "/agent/move";
        Debug.Log("Post: " + web_url_post);

        var jsonData = JsonUtility.ToJson(new ActionData { action = action });
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);

        using (UnityWebRequest webRequest = new UnityWebRequest(web_url_post, "POST"))
        {
            webRequest.uploadHandler = new UploadHandlerRaw(bodyRaw);
            webRequest.downloadHandler = new DownloadHandlerBuffer();
            webRequest.SetRequestHeader("Content-Type", "application/json");

            yield return webRequest.SendWebRequest();

            if (webRequest.isNetworkError)
            {
                Debug.LogError("POST Error: " + webRequest.error);
            }
            else
            {
                Debug.Log("POST Response: " + webRequest.downloadHandler.text);
            }
        }
    }
}

[System.Serializable]
public class ActionData
{
    public string action;

}
