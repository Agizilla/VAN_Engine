using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using VanEngine.WinForms.Forms;
using VanEngine.WinForms.Services;

namespace VanEngine.WinForms;

static class Program
{
    public static IServiceProvider ServiceProvider { get; private set; } = null!;

    [STAThread]
    static void Main()
    {
        ApplicationConfiguration.Initialize();

        var services = new ServiceCollection();

        services.AddSingleton<BrainBridge>();
        services.AddSingleton<InferenceService>();
        services.AddSingleton<TranscriptParser>();
        services.AddSingleton<PipelineMonitor>();

        services.AddTransient<MainForm>();
        services.AddTransient<ChatPanel>();
        services.AddTransient<InferencePanel>();
        services.AddTransient<TranscriptPanel>();
        services.AddTransient<MonitorPanel>();
        services.AddTransient<SettingsPanel>();

        services.AddLogging(builder =>
        {
            builder.AddConsole();
            builder.SetMinimumLevel(LogLevel.Information);
        });

        ServiceProvider = services.BuildServiceProvider();

        var mainForm = ServiceProvider.GetRequiredService<MainForm>();
        Application.Run(mainForm);
    }
}
