using UnityEngine; // Necesario para MonoBehaviour y componentes de Unity
using System.Collections; // Para poder usar corrutinas (IEnumerator)
using System.Collections.Generic;

public class MoveAgent : MonoBehaviour
{
    [Header("Cad cuantos segundos pedir a Flask")]
    public float updateInterval = 2f;

    [Header("Referencias a los Transforms de cada agente en la escena")]
    public Transform morado;
    public Transform rosa;
    public Transform rojo;
    public Transform azul;
    public Transform naranja;
    public Transform verde;

    // Referencia al script ApiHelper (para comunicar con Flask)
    private ApiHelper api;

    // Mapa nombre -> Transform para aplicar posiciones fácilmente
    private Dictionary<string, Transform> map;

    void Awake()
    {
        api = GetComponent<ApiHelper>(); // Debe estar en el mismo GameObject

        // Dictionario de objetos 
        map = new Dictionary<string, Transform> {
            { "morado",  morado  },
            { "rosa",    rosa    },
            { "rojo",    rojo    },
            { "azul",    azul    },
            { "naranja", naranja },
            { "verde",   verde   }
        };
    }

    // Se llama la corutina
    void Start()
    {
        StartCoroutine(LoopUpdate());
    }
    
    // Corrutina que actualiza continuamente la posición de TODOS agente
    IEnumerator LoopUpdate(){
        while(true){
            yield return StartCoroutine(api.pos_agent());

            // Si se recibio algo, recorre y actualiza cada Transform
            if (api.lastPayload != null && api.lastPayload.agents != null){
                foreach (var a in api.lastPayload.agents){
                    if (map.TryGetValue(a.name, out var t) && t != null){
                        t.position = new Vector3(a.x, a.y, 0);
                    } else {
                        Debug.Log("No hay Transform asignado para el agente: " + a.name);
                    }
                }

                yield return new WaitForSeconds(updateInterval);
            }
        }
    }

    // Corrutina que actualiza continuamente la posición de UN agente
    /* IEnumerator UpdateAgentPosition()
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
    }*/

}
