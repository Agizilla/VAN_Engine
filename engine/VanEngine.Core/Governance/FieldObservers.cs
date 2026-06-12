namespace VanEngine.Core.Governance;

public record Citizen(string Name, string Module);

public sealed class FieldObserver
{
    public Citizen Citizen { get; }
    private readonly FieldObservers _parent;

    public FieldObserver(Citizen citizen, FieldObservers parent)
    {
        Citizen = citizen;
        _parent = parent;
    }

    public async Task RecordAndReport(string observation)
    {
        await _parent.SendDailyReport($"{Citizen.Name} observes: {observation}");
    }
}

public sealed class FieldObservers
{
    public const int MaxObservers = 3;
    private readonly List<FieldObserver> _observers = new();
    private readonly MessengerService _messengers;
    private readonly string _mother = "Clawdia";

    public IReadOnlyList<FieldObserver> Observers => _observers.AsReadOnly();

    public FieldObservers(MessengerService messengers)
    {
        _messengers = messengers;
    }

    public void AssignObservers(IEnumerable<Citizen> citizens)
    {
        _observers.Clear();
        foreach (var citizen in citizens.Take(MaxObservers))
        {
            _observers.Add(new FieldObserver(citizen, this));
        }
        Console.WriteLine($"[LAW 5] {_observers.Count} citizen observers assigned to the field.");
    }

    public async Task SendDailyReport(string report)
    {
        foreach (var observer in _observers)
        {
            await _messengers.SendToMother(_mother, $"[OBSERVER REPORT] {report}");
        }
    }
}
