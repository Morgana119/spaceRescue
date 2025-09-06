using System.Collections.Generic;
using UnityEngine;

public class GridFireManager : MonoBehaviour {
    public GameObject firePrefab;
    public GameObject smokePrefab;

    private Dictionary<(int,int), GameObject> activeObjects = new();

    void Start() {
        // Define las coordenadas iniciales del fuego directamente aquí.
        List<(int x, int y)> initialFirePositions = new List<(int x, int y)> {
            (2, 2), (2, 3), (3, 2), (3, 4), (3, 3), (3, 5), (4, 4), (5, 6), (5, 7), (6, 6)
        };
        
        // Aplica el cambio para cada posición en la lista.
        foreach (var pos in initialFirePositions) {
            ApplyChange("fire", pos.x, pos.y);
        }
    }

    public void ApplyChange(string type, int x, int y) {
        var key = (x, y);
        float spacing = 4.0f;
        Vector3 pos = new Vector3(x * spacing, 0, y * spacing);

        if (activeObjects.ContainsKey(key)) {
            var obj = activeObjects[key];

            // 🔹 Solo destruye si es fuego o humo
            if (obj != null && 
                (obj.CompareTag("Fire") || obj.CompareTag("Smoke"))) 
            {
                Destroy(obj);
                activeObjects.Remove(key);
            }
        }


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
