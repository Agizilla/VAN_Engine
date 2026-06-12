using Raylib_CsLo;
using static Raylib_CsLo.Raylib;

namespace VanEngine.Game.Simulation;

public enum SimulationPhase : byte
{
    Daytime = 0,
    Nighttime = 1
}

public sealed class TimePhaseController
{
    public SimulationPhase CurrentPhase { get; private set; } = SimulationPhase.Daytime;
    public float CalendarYearProgress { get; private set; }
    public const float SecondsPerGameYear = 8f;

    public bool IsTransitioning { get; private set; }
    public float TransitionProgress { get; private set; }
    public const float TransitionDuration = 1.5f;
    public SimulationPhase PreviousPhase { get; private set; } = SimulationPhase.Daytime;
    private float _clockHandAngle;

    public float ClockHandAngle => _clockHandAngle;

    public void TogglePhase()
    {
        if (IsTransitioning) return;
        PreviousPhase = CurrentPhase;
        CurrentPhase = CurrentPhase == SimulationPhase.Daytime
            ? SimulationPhase.Nighttime
            : SimulationPhase.Daytime;
        IsTransitioning = true;
        TransitionProgress = 0f;
    }

    public void UpdateTransition(float delta)
    {
        if (!IsTransitioning) return;
        TransitionProgress += delta / TransitionDuration;
        _clockHandAngle += delta * 180f;

        if (TransitionProgress >= 1f)
        {
            TransitionProgress = 1f;
            IsTransitioning = false;
            _clockHandAngle = CurrentPhase == SimulationPhase.Nighttime ? 180f : 0f;
        }
    }

    public Color LerpColor(Color day, Color night)
    {
        float t = IsTransitioning ? TransitionProgress : (CurrentPhase == SimulationPhase.Nighttime ? 1f : 0f);
        return new Color(
            (byte)(day.r + (night.r - day.r) * t),
            (byte)(day.g + (night.g - day.g) * t),
            (byte)(day.b + (night.b - day.b) * t),
            (byte)(day.a + (night.a - day.a) * t));
    }

    public bool TickEngineClock(float delta, out bool yearChanged)
    {
        yearChanged = false;
        if (CurrentPhase == SimulationPhase.Nighttime) return false;

        CalendarYearProgress += delta;
        if (CalendarYearProgress >= SecondsPerGameYear)
        {
            CalendarYearProgress = 0f;
            yearChanged = true;
            return true;
        }
        return false;
    }
}
