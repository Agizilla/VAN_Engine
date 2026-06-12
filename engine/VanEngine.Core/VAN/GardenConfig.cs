namespace VanEngine.Core.VAN;

public sealed class GardenConfig
{
    public string StateRoot { get; set; } = string.Empty;
    public string SchemaRoot { get; set; } = string.Empty;
    public string RegistryRoot { get; set; } = string.Empty;
    public string PolicyRoot { get; set; } = string.Empty;

    public bool IsComplete =>
        !string.IsNullOrEmpty(StateRoot) &&
        !string.IsNullOrEmpty(SchemaRoot) &&
        !string.IsNullOrEmpty(RegistryRoot) &&
        !string.IsNullOrEmpty(PolicyRoot);

    public static GardenConfig FromDirectory(string dir)
    {
        return new GardenConfig
        {
            StateRoot = Path.Combine(dir, "garden_one_state.json"),
            SchemaRoot = Path.Combine(dir, "garden_two_schema.json"),
            RegistryRoot = Path.Combine(dir, "garden_three_registry.json"),
            PolicyRoot = Path.Combine(dir, "garden_four_network_policy.json")
        };
    }

    public string[] AllPaths() =>
        new[] { StateRoot, SchemaRoot, RegistryRoot, PolicyRoot };
}
