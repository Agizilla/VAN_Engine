using Xunit;
using VanE = VanEngine.Core.VAN;

namespace VanEngine.Core.Tests.VAN;

public sealed class VanEngineTests
{
    private readonly VanE.VanEngine _engine = new();

    [Fact]
    public void SoftKneeExpander_PreservesStrongSignals()
    {
        var signal = new double[] { 100.0, 95.0, 102.0, 98.0 };
        var noiseFloor = 10.0;

        var result = _engine.SoftKneeDownwardExpander(signal, noiseFloor, kneeSlope: 2.0);

        Assert.Equal(signal[0], result[0], 0.1);
    }

    [Fact]
    public void SoftKneeExpander_DucksWeakSignals()
    {
        var signal = new double[] { 100.0, 5.0, 95.0, 3.0 };
        var noiseFloor = 10.0;

        var result = _engine.SoftKneeDownwardExpander(signal, noiseFloor, kneeSlope: 2.0, ditherProfile: new double[] { 0, 0, 0, 0 });

        Assert.True(result[1] < signal[1]);
        Assert.True(result[3] < signal[3]);
    }

    [Fact]
    public void SoftKneeExpander_PreservesDitherTexture()
    {
        var signal = new double[] { 5.0, 6.0, 4.0, 7.0 };
        var noiseFloor = 10.0;
        var dither = new double[] { 0.1, 0.12, 0.09, 0.11 };

        var result = _engine.SoftKneeDownwardExpander(signal, noiseFloor, kneeSlope: 2.0, dither);

        Assert.NotEqual(0.0, result[0], 5);
    }

    [Fact]
    public void SoftKneeExpander2D_ProcessesMatrix()
    {
        var signal = new double[,] { { 100.0, 5.0 }, { 3.0, 95.0 } };
        var noiseFloor = 10.0;
        var zeroDither = new double[,] { { 0, 0 }, { 0, 0 } };

        var result = _engine.SoftKneeDownwardExpander2D(signal, noiseFloor, kneeSlope: 2.0, zeroDither);

        Assert.Equal(100.0, result[0, 0], 0.1);
        Assert.True(result[0, 1] < signal[0, 1]);
    }

    [Fact]
    public void VanParser_DemodulatesValidVanBlock()
    {
        var vanBlock = @"
            [TRANSITION: Test-Block]
            {
              CARRIER: LLM-Attention;
              MODULATION: Soft-Knee-Expander;
              Q-FACTOR: 0.95;
              DITHER: Semantic-Entropy;
              DATA: [""test data 1"", ""test data 2""];
              DATATYPES: [""text/plain"", ""text/plain""];
            }";

        var envelope = _engine.Demodulate(vanBlock);

        Assert.Equal("TRANSITION:Test-Block", envelope.Header);
        Assert.Equal("LLM-Attention", envelope.Carrier);
        Assert.Equal(0.95, envelope.QFactor);
        Assert.Equal(2, envelope.Data.Count);
    }

    [Fact]
    public void ProcessPixelPhase_ReturnsProcessedImage()
    {
        var envelope = new VanE.VanEnvelope
        {
            Header = "Pixel-Test",
            Carrier = "Pixel-Phase",
            QFactor = 0.95,
            Data = new List<object>
            {
                new double[,] { { 100.0, 5.0, 80.0 }, { 3.0, 95.0, 2.0 }, { 70.0, 4.0, 90.0 } }
            }
        };

        var result = _engine.ProcessPixelPhase(envelope);

        Assert.NotNull(result.ProcessedImage);
        Assert.True(result.NoiseFloorPreserved > 0);
    }

    [Fact]
    public void ProcessSteelResonance_FiltersFrequencies()
    {
        var envelope = new VanE.VanEnvelope
        {
            Header = "Steel-Test",
            Carrier = "Steel-Resonance",
            QFactor = 0.95,
            Data = new List<object>
            {
                new double[] { 100.0, 2.0, 95.0, 1.5, 80.0, 3.0 }
            }
        };

        var result = _engine.ProcessSteelResonance(envelope);

        Assert.NotNull(result.FilteredFrequencies);
        Assert.Equal(6, result.FilteredFrequencies.Length);
    }
}
