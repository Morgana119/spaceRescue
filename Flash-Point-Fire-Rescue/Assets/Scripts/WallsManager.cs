using UnityEngine;

public class WallsManager : MonoBehaviour
{
    public GameObject firePrefab1, firePrefab2;
    public GameObject damageWall;
    public GameObject destroyedWall;
    public float offset = 1.57f;   

    public void BreakWall(int x, int y, int direction)
    {
        Vector3 basePosition = new Vector3(x*4, 4.3f, y*4);

        GameObject fireTemp = Instantiate(firePrefab1, basePosition, Quaternion.identity);

        Vector3 position = fireTemp.transform.position;

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
            if (col.CompareTag("damagedWall"))
            {
                Destroy(col.gameObject);
            }
        }

        Instantiate(destroyedWall, position, Quaternion.Euler(0, 90, 0) );

        Destroy(fireTemp);
    }

    public void DamageWall(int x, int y, int direction)
    {
        // Posición base igual que usarías para el fuego
        Vector3 basePosition = new Vector3(x*4, 4.3f, y*4);

        // Instanciar un fuego temporal SOLO para obtener su posición real
        GameObject fireTemp = Instantiate(firePrefab2, basePosition, Quaternion.identity);

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
        Instantiate(damageWall, position, Quaternion.Euler(0, 90, 0) );

        // Eliminar el fuego temporal
        Destroy(fireTemp);
    }    
}
