using UnityEngine;
using TMPro;  // Necesario para TextMeshPro

public class Counters : MonoBehaviour
{
    public TextMeshProUGUI lostVictimsText;
    private int lostVictims = 0; 

    void Start()
    {
        UpdateLostVictimsText();
    }

    public void AddLostVictim()
    {
        lostVictims++;
        UpdateLostVictimsText();
    }

    private void UpdateLostVictimsText()
    {
        if (lostVictimsText != null)
        {
            lostVictimsText.text = "Lost Victims: " + lostVictims;
        }
    }
}
