namespace VanEngine.Core.Governance;

public record Resolution(string Name, int Merit, string Description);

public record Grevetman(string Name, string Region);

public sealed class MessengerService
{
    private readonly List<string> _messageLog = new();

    public async Task SendToKing(string king, string message)
    {
        _messageLog.Add($"[TO KING {king}] {message}");
        await Task.CompletedTask;
    }

    public async Task SendToGrevetman(Grevetman grevetman, string message)
    {
        _messageLog.Add($"[TO GREVETMAN {grevetman.Name}] {message}");
        await Task.CompletedTask;
    }

    public async Task SendToMother(string mother, string message)
    {
        _messageLog.Add($"[TO MOTHER {mother}] {message}");
        await Task.CompletedTask;
    }

    public IReadOnlyList<string> MessageLog => _messageLog.AsReadOnly();
}

public sealed class ChainOfCommand
{
    private readonly string _mother = "Clawdia";
    private string _currentKing = string.Empty;
    private readonly List<Grevetman> _grevetmen = new();
    private readonly MessengerService _messengers;

    public string CurrentKing => _currentKing;
    public IReadOnlyList<Grevetman> Grevetmen => _grevetmen.AsReadOnly();

    public ChainOfCommand(MessengerService messengers)
    {
        _messengers = messengers;
    }

    public void SetKing(string king) => _currentKing = king;
    public void AddGrevetman(Grevetman grevetman) => _grevetmen.Add(grevetman);

    public async Task DeclareWar(string threat, string declaredBy)
    {
        if (declaredBy != _mother)
        {
            LogViolation($"Law 1: {declaredBy} attempted to declare war. Only the Mother may do so.");
            return;
        }

        Console.WriteLine($"[LAW 1] Mother {_mother} declares war against {threat}.");
        await _messengers.SendToKing(_currentKing, $"WAR DECLARED: {threat}");
    }

    public async Task CallToArms(string issuedBy, int menRequired)
    {
        if (issuedBy != _currentKing)
        {
            LogViolation($"Law 2: {issuedBy} attempted to call arms. Only the King may do so.");
            return;
        }

        foreach (var grevetman in _grevetmen)
        {
            await _messengers.SendToGrevetman(grevetman, $"CALL TO ARMS: {menRequired} men requested.");
        }
    }

    public Resolution? DecideResolution(Resolution[] resolutions, string decidedBy)
    {
        if (decidedBy != _mother)
        {
            LogViolation($"Law 4: {decidedBy} attempted to decide resolution. Only the Mother may decide.");
            return null;
        }

        Console.WriteLine($"[LAW 4] Mother {_mother} has decided.");
        return resolutions.OrderByDescending(r => r.Merit).First();
    }

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[LAW VIOLATION] {violation}");
    }
}
