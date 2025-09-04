using UnityEngine;
using System.Collections;

public class GameManager : MonoBehaviour
{
    public float updateInterval = 2f;

    private ApiHelper api;
    private MoveAgent agentManager;
    private GridFireManager fireManager;

    void Awake()
    {
        api = GetComponent<ApiHelper>();
        agentManager = FindObjectOfType<MoveAgent>();
        fireManager = FindObjectOfType<GridFireManager>();
    }

    void Start()
    {
        StartCoroutine(LoopUpdate());
    }

    IEnumerator LoopUpdate()
    {
        while (true)
        {
            yield return StartCoroutine(api.GetFullState());

            if (api.lastFullState != null)
            {
                // 🔹 Actualiza agentes
                agentManager.UpdateAgents(api.lastFullState.agents);

                // 🔹 Actualiza fuegos
                fireManager.ClearFires();
                foreach (var f in api.lastFullState.fires)
                {
                    fireManager.SetFire(f.x, f.y);
                }
            }

            yield return new WaitForSeconds(updateInterval);
        }
    }
}
