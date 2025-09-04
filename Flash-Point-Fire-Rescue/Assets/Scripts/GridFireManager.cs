using UnityEngine;
using System.Collections;
using System.Collections.Generic; 

public class GridFireManager : MonoBehaviour
{
    public int width = 10;
    public int height = 8;
    public GameObject firePrefab;

    private GameObject[,] grid;
    // (2, 2), (2, 3), (3, 2), (4, 3), (3, 3), (5, 3), (4, 4), (6, 5), (7, 5), (6, 6)
    // Lista de posiciones iniciales con fuego
    public List<Vector2Int> initialFires = new List<Vector2Int> {
        new Vector2Int(2,2),
        new Vector2Int(2,3),
        new Vector2Int(3,2),
        new Vector2Int(4,3),
        new Vector2Int(3,3),
        new Vector2Int(5,3),
        new Vector2Int(4,4),
        new Vector2Int(6,5),
        new Vector2Int(7,5),
        new Vector2Int(6,6)
    };
    public List<Vector2Int> newFires = new List<Vector2Int>();
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        grid = new GameObject[width, height];
        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                float spacing = 4f; 
                GameObject fire = Instantiate(firePrefab, new Vector3(x * spacing, 0, y * spacing), Quaternion.identity);
                fire.SetActive(false); // inactivo al inicio
                grid[x, y] = fire;
            }
        }

        foreach (var pos in initialFires)
        {
            if (pos.x >= 0 && pos.x < width && pos.y >= 0 && pos.y < height)
            {
                grid[pos.x, pos.y].SetActive(true);
            }
        }
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    public void ClearFires()
    {
        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                grid[x, y].SetActive(false);
            }
        }
    }

    public void SetFire(int x, int y, bool state = true)
    {
        if (x >= 0 && x < width && y >= 0 && y < height)
        {
            grid[x, y].SetActive(state);
        }
    }   


}
