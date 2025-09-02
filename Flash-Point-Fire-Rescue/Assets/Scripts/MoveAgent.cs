using UnityEngine; // Necesario para MonoBehaviour y componentes de Unity
using System.Collections; // Para poder usar corrutinas (IEnumerator)

public class MoveAgent : MonoBehaviour
{
    // Cada cuántos segundos se actualiza la posición del agente
    public float updateInterval = 2f;

    // Referencia al script ApiHelper (para comunicar con Flask)
    private ApiHelper api;

    void Start()
    {
        // Busca el componente ApiHelper en el mismo GameObject
        api = GetComponent<ApiHelper>();
        // Inicia la corrutina que periódicamente actualizará la posición del agente
        StartCoroutine(UpdateAgentPosition());
    }

    // Corrutina que actualiza continuamente la posición del agente
    IEnumerator UpdateAgentPosition()
    {
        while (true) // Bucle infinito mientras el objeto exista

        {
            // Llama a la API Flask para obtener la posición (x, y)
            yield return StartCoroutine(api.pos_agent()); // solo llamamos al método

            // Si se recibió correctamente la posición
            if (api.lastPos != null)
            {
                // Actualiza la posición del objeto en la escena de Unity
                transform.position = new Vector3(api.lastPos.x, api.lastPos.y, 0);
            }

            // Espera el intervalo definido antes de la siguiente actualización
            yield return new WaitForSeconds(updateInterval);
        }
    }
}
