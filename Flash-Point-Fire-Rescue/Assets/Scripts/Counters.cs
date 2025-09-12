using UnityEngine;
using TMPro;  // Necesario para TextMeshPro

public class Counters : MonoBehaviour
{
    public TextMeshProUGUI lostVictimsText;
    public TextMeshProUGUI savedVictimsText;

    private int lostVictims = 0; 
    private int savedVictims = 0;

    void Start()
    {
        UpdateLostVictimsText();
        UpdateSavedVictimsText();
    }

    public void AddLostVictim()
    {
        lostVictims++;
        UpdateLostVictimsText();
    }

    public void AddSavedVictim()
    {
        savedVictims++;
        UpdateSavedVictimsText();
    }

    private void UpdateLostVictimsText()
    {
        if (lostVictimsText != null)
        {
            lostVictimsText.text = "Lost Victims: " + lostVictims;
        }
    }

    private void UpdateSavedVictimsText()
    {
        if (savedVictimsText != null)
        {
            savedVictimsText.text = "Saved Victims: " + savedVictims;
        }
    }
}
