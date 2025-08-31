using UnityEngine;
using System.Collections;

public class MoveAgent : MonoBehaviour
{
    public float updateInterval = 2f;
    private ApiHelper api;

    void Start()
    {
        api = GetComponent<ApiHelper>();
        StartCoroutine(UpdateAgentPosition());
    }

    IEnumerator UpdateAgentPosition()
    {
        while (true)
        {
            yield return StartCoroutine(api.pos_agent()); // solo llamamos al método

            if (api.lastPos != null)
            {
                transform.position = new Vector3(api.lastPos.x, api.lastPos.y, 0);
            }

            yield return new WaitForSeconds(updateInterval);
        }
    }
}
