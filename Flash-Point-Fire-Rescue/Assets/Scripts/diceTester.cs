using UnityEngine;
using UnityEngine.InputSystem;

public class DiceTester : MonoBehaviour
{
    [Header("Arrastra aquí tus dados")]
    public DiceFaceRotator dice8; // x (d8)
    public DiceFaceRotator dice6; // y (d6)

    /// x = cara del d8, y = cara del d6
    public void RollBoth(int x, int y)
    {
        if (dice8 != null) dice8.ShowFaceWithRoll(y);
        if (dice6 != null) dice6.ShowFaceWithRoll(x);
    }

    // void Update()
    // {
    //     var kb = Keyboard.current;
    //     if (kb == null) return;

    //     // d8: 3, d6: 5
    //     if (kb.digit1Key.wasPressedThisFrame || kb.numpad1Key.wasPressedThisFrame)
    //         RollBoth(1, 1);

    //     // d8: 8, d6: 6
    //     if (kb.digit2Key.wasPressedThisFrame || kb.numpad2Key.wasPressedThisFrame)
    //         RollBoth(2, 2);

    //     // d8: 1, d6: 2
    //     if (kb.digit3Key.wasPressedThisFrame || kb.numpad3Key.wasPressedThisFrame)
    //         RollBoth(3, 3);

    //     if (kb.rKey.wasPressedThisFrame)
    //     {
    //         int x = Random.Range(1, 8); // d8: 1..8
    //         int y = Random.Range(1, 7); // d6: 1..6
    //         Debug.Log($"Rolling random: d8={x}, d6={y}");
    //         RollBoth(x, y);
    //     }
    // }
}
