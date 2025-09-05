using System.Collections.Generic;
using UnityEngine;

public class GridFireManager : MonoBehaviour {
    public GameObject firePrefab;
    public GameObject smokePrefab;

    private Dictionary<(int,int), GameObject> activeObjects = new();

    public void ApplyChange(string type, int x, int y) {
        var key = (x, y);
        Vector3 pos = new Vector3(x, 0, y);

        // 🔹 Si ya hay algo en esa celda → lo destruyo antes
        // if (activeObjects.ContainsKey(key)) {
        //     Destroy(activeObjects[key]);
        //     activeObjects.Remove(key);
        // }

        // 🔹 Crear nuevo objeto según el tipo
        GameObject prefab = null;
        if (type == "fire") prefab = firePrefab;
        else if (type == "smoke") prefab = smokePrefab;

        if (prefab != null) {
            var obj = Instantiate(prefab, pos, Quaternion.identity);
            activeObjects[key] = obj;
        }
    }
}
