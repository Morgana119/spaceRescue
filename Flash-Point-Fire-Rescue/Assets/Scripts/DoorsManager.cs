using UnityEngine;
using System.Collections.Generic;

public class DoorsManager : MonoBehaviour
{
    public GameObject firePrefab;      // Prefab del fuego (solo para referencia)
    public GameObject openDoorPrefab;  // Prefab de la puerta
    public GameObject closedDoorPrefab;
    public float offset = 1.57f;        // Ajuste opcional

    void Start() {
        List<(int x, int y, int d)> initialClosedDoors = new List<(int x, int y, int d)> {
            (1,3,1), (2, 5, 1), (2, 8, 2), (4, 6, 1), (4, 4, 2), (6, 5, 1), (6, 7, 1), (3, 2, 1)
        };

        List<(int x, int y, int d)> initialOpenDoors = new List<(int x, int y, int d)> {
            (3, 0, 1), (0, 6, 2), (4, 8, 1), (6, 3, 2)
        };

        foreach (var pos in initialClosedDoors) {
            ClosedDoor( pos.x, pos.y, pos.d);
        }

        foreach (var pos in initialOpenDoors) {
            OpenDoor( pos.x, pos.y, pos.d);
        }

        
    }

    public void OpenDoor(int x, int y, int direction)
    {
        // Posición base igual que usarías para el fuego
        Vector3 basePosition = new Vector3(x*4, 4.3f, y*4);

        // Instanciar un fuego temporal SOLO para obtener su posición real
        GameObject fireTemp = Instantiate(firePrefab, basePosition, Quaternion.identity);

        // Tomar esa posición como referencia
        Vector3 position = fireTemp.transform.position;

        // Desplazar según dirección
        switch (direction)
        {
            case 0: // up
                position.x -= offset;
                break;
            case 2: // down
                position.x += offset;
                break;
            case 3: // left
                position.z -= offset;
                break;
            case 1: // right
                position.z += offset;
                break;
        }

        Collider[] colliders = Physics.OverlapSphere(position, 0.1f); // radio pequeñito
        foreach (Collider col in colliders)
        {
            if (col.CompareTag("closeDoor"))
            {
                Destroy(col.gameObject);
            }
        }

        // Instanciar la puerta en la misma posición (sin rotación)
        Instantiate(openDoorPrefab, position, Quaternion.Euler(0, 90, 0) );

        // Eliminar el fuego temporal
        Destroy(fireTemp);
    }

    public void ClosedDoor(int x, int y, int direction)
    {
        // Posición base igual que usarías para el fuego
        Vector3 basePosition = new Vector3(x*4, 4.3f, y*4);

        // Instanciar un fuego temporal SOLO para obtener su posición real
        GameObject fireTemp = Instantiate(firePrefab, basePosition, Quaternion.identity);

        // Tomar esa posición como referencia
        Vector3 position = fireTemp.transform.position;

        // Desplazar según dirección
        switch (direction)
        {
            case 0: // up
                position.x -= offset;
                break;
            case 2: // down
                position.x += offset;
                break;
            case 3: // left
                position.z -= offset;
                break;
            case 1: // right
                position.z += offset;
                break;
        }

        // Instanciar la puerta en la misma posición (sin rotación)
        Instantiate(closedDoorPrefab, position, Quaternion.Euler(0, 90, 0) );

        // Eliminar el fuego temporal
        Destroy(fireTemp);
    }
}
