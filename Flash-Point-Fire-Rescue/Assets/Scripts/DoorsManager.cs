using UnityEngine;

public class DoorsManager : MonoBehaviour
{
    public GameObject firePrefab;      // Prefab del fuego (solo para referencia)
    public GameObject openDoorPrefab;  // Prefab de la puerta
    public float offset = 1.5f;        // Ajuste opcional

    public void OpenDoor(int x, int y, int direction)
    {
        // Posición base igual que usarías para el fuego
        Vector3 basePosition = new Vector3(x*4, 5, y*4);

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
        Instantiate(openDoorPrefab, position, Quaternion.Euler(0, 90, 0) );

        // Eliminar el fuego temporal
        Destroy(fireTemp);
    }
}
