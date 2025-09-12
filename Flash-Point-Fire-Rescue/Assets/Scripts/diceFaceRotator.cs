using System.Collections;
using UnityEngine;

public class DiceFaceRotator : MonoBehaviour
{
    [Header("Faces setup")]
    public Preset preset = Preset.None;
    
    public enum Preset { None, D6, D8 }
    public Vector3[] faceEulerAngles;
    public float settleDuration = 0.8f;
    public AnimationCurve settleEase = AnimationCurve.EaseInOut(0, 0, 1, 1);
    public float preRollTotalDuration = 1.3f;
    public float spinStartSpeed = 1080f; // deg/s
    public float spinEndSpeed   = 240f;  // deg/s
    public AnimationCurve preRollSpeedCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);
    public float spinAxisJitter = 0.15f;

    Coroutine spinCR;

    void Awake()
    {
        if (preset == Preset.D6)
        {
            faceEulerAngles = new Vector3[]
            {
                new Vector3(270,   0,   0),  // 1
                new Vector3(  0,   0,   0),  // 2
                new Vector3(360,   0, -90),  // 3
                new Vector3(360,   0,  90),  // 4
                new Vector3(180,   0,   0),  // 5
                new Vector3( 90,   0,   0),  // 6
            };
        }
        else if (preset == Preset.D8)
        {
            faceEulerAngles = new Vector3[]
            {
                new Vector3(202, 96, 158),    // 1+
                new Vector3(153, -83, 111),     // 2+
                new Vector3(206, -258, 72),   // 3+
                new Vector3(153, -83, 202),    // 4+
                new Vector3(202, 96, 339),     // 5+
                new Vector3(153, -83, 288),   // 6+
                new Vector3(202, 96, 247),    // 7+
                new Vector3(153, -83, 25),     // 8+
            };
        }
    }

    public void ShowFace(int face, bool instantly = false)
    {
        if (!Valid(face)) return;
        if (spinCR != null) StopCoroutine(spinCR);
        spinCR = StartCoroutine(RotateTo(GetTarget(face), instantly ? 0f : settleDuration, settleEase));
    }

    public void ShowFaceWithRoll(int face)
    {
        if (!Valid(face)) return;
        if (spinCR != null) StopCoroutine(spinCR);
        spinCR = StartCoroutine(PreRollSpinThenSettle(face));
    }

    bool Valid(int face)
    {
        if (faceEulerAngles == null || faceEulerAngles.Length == 0)
        {
            Debug.LogWarning("No hay rotaciones definidas para este dado.");
            return false;
        }
        if (face < 1 || face > faceEulerAngles.Length)
        {
            Debug.LogWarning($"Cara fuera de rango: 1..{faceEulerAngles.Length}");
            return false;
        }
        return true;
    }

    Quaternion GetTarget(int face) => Quaternion.Euler(faceEulerAngles[face - 1]);

    IEnumerator PreRollSpinThenSettle(int targetFace)
    {
        float t = 0f;
        Vector3 axis = Random.onUnitSphere.normalized;

        while (t < preRollTotalDuration)
        {
            float u = Mathf.Clamp01(t / preRollTotalDuration);
            float speed = Mathf.Lerp(spinStartSpeed, spinEndSpeed, preRollSpeedCurve.Evaluate(u));

            if (spinAxisJitter > 0f)
            {
                Vector3 jitter = Random.insideUnitSphere * spinAxisJitter;
                Vector3 newAxis = (axis + jitter).normalized;
                axis = Vector3.Slerp(axis, newAxis, 0.2f);
            }

            transform.rotation = Quaternion.AngleAxis(speed * Time.deltaTime, axis) * transform.rotation;
            t += Time.deltaTime;
            yield return null;
        }

        yield return RotateTo(GetTarget(targetFace), settleDuration, settleEase);
        spinCR = null;
    }

    IEnumerator RotateTo(Quaternion targetRot, float duration, AnimationCurve curve)
    {
        if (duration <= 0f) { transform.rotation = targetRot; yield break; }

        Quaternion from = transform.rotation;
        float t = 0f;
        while (t < duration)
        {
            t += Time.deltaTime;
            float u = Mathf.Clamp01(t / duration);
            transform.rotation = Quaternion.Slerp(from, targetRot, curve.Evaluate(u));
            yield return null;
        }
        transform.rotation = targetRot;
    }
}
