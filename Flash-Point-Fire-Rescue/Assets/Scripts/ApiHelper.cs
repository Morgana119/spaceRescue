using UnityEngine; // Necesario para usar MonoBehaviour y JsonUtility
using UnityEngine.Networking; // Para hacer peticiones HTTP (GET, POST)
using System.Collections; // Para corutinas
//using System;


public class ApiHelper : MonoBehaviour
{
    private string url = "http://127.0.0.1:5000"; // Dirección del servidor Flask
    public AgentsPayLoad lastPayload; // Último JSON parseado

    // Corutina que obtiene la posición actualizada del agente desde el servidor
    public IEnumerator pos_agent()
    {
        // Endpoint que consulta el estado del agente
        string web_url_getPos = url + "/move/agents";
        Debug.Log("Get: " + web_url_getPos);

        // Realiza la petición GET
        using (UnityWebRequest webRequest = UnityWebRequest.Get(web_url_getPos))
        {
            // Espera a que termina la conexión
            yield return webRequest.SendWebRequest();

            // Manejo de errores
            if (webRequest.isNetworkError)
            {
                // Si falla la conexión, se muestra error y se resetea la variable
                Debug.LogError("Error: " + webRequest.error);
            }
            else
            {
                // Se recibe la respuesta JSON con "x" y "y"
                string jsonResponse = webRequest.downloadHandler.text.Trim();

                // Convierte el JSON recibido a la clase AgentsPayLoad
                lastPayload = JsonUtility.FromJson<AgentsPayLoad>(jsonResponse);

                // Muestra en consola la posición recibida desde Flask
                foreach (var a in lastPayload.agents) Debug.Log($"{a.name}: ({a.x},{a.y}, {a.z})");
            }
        }
    }

    public FullStatePayload lastFullState;
    public GridFireManager gridFireManager;

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

                // Parsear lista de fuegos
                FireList fireList = JsonUtility.FromJson<FireList>(jsonResponse);
                foreach (var fire in fireList.fires)
                {
                    gridFireManager.SetFire(fire.x, fire.y, true);
                }

                // Guardar el estado completo
                lastFullState = JsonUtility.FromJson<FullStatePayload>(jsonResponse);
            }
        }
    }

}

    /* void Start(){
        // Inicia la primera petición GET al servidor para probar conexión
        StartCoroutine(GetRequest(url));
    } */

     // Corrutina para realizar un GET de prueba al servidor
    /*IEnumerator GetRequest(string uri){
        // Endpoint que consulta el estado del agente
        string web_url_get = uri + "/agent/state";
        Debug.Log("Get: " + web_url_get);

        // Realiza la petición GET
        using (UnityWebRequest webRequest = UnityWebRequest.Get(web_url_get)){
            // Espera a que termina la conexión
            yield return webRequest.SendWebRequest();

            // Manejo de errores
            if (webRequest.isNetworkError){
                Debug.Log("Error " + webRequest.error); 
            } else {
                // Imprime en consola el JSON de respuesta
                Debug.Log(webRequest.downloadHandler.text);
            }
        }
    }

    // -------------------- POST -----------------------------------
    // Corrutina para enviar un movimiento al agente en Flask
    IEnumerator PostMoveAgent(string action, string uri)
    {
        string web_url_post = uri + "/agent/move";
        Debug.Log("Post: " + web_url_post);

        // Convierte la acción a JSON, usando la clase ActionData
        var jsonData = JsonUtility.ToJson(new ActionData { action = action });

        // Codifica el JSON en bytes para enviarlo en el body de la petición
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);

        // Configura la petición POST
        using (UnityWebRequest webRequest = new UnityWebRequest(web_url_post, "POST"))
        {
            webRequest.uploadHandler = new UploadHandlerRaw(bodyRaw); // Se adjunta el body
            webRequest.downloadHandler = new DownloadHandlerBuffer(); // Se espera respuesta
            webRequest.SetRequestHeader("Content-Type", "application/json"); // Tipo JSON

            // Se envía la petición y se espera la respuesta
            yield return webRequest.SendWebRequest();

            if (webRequest.isNetworkError)
            {
                Debug.LogError("POST Error: " + webRequest.error);
            }
            else
            {
                // Imprime la respuesta del servidor (nuevo estado del agente)
                Debug.Log("POST Response: " + webRequest.downloadHandler.text);
            }
        }
    }
    */
