using Xunit;
using VanE = VanEngine.Core.VAN;

namespace VanEngine.Core.Tests.VAN;

public sealed class VanEngineEdgeCaseTests
{
    private readonly VanE.VanEngine _engine;

    public VanEngineEdgeCaseTests()
    {
        _engine = new VanE.VanEngine();
    }

    [Fact]
    public void SoftKneeExpander_HandlesPerfectlyUniformSignal()
    {
        var uniformSignal = new double[] { 128.0, 128.0, 128.0, 128.0 };
        var noiseFloor = 0.0;

        var result = _engine.SoftKneeDownwardExpander(uniformSignal, noiseFloor);

        Assert.NotNull(result);
        Assert.Equal(uniformSignal.Length, result.Length);
    }

    [Fact]
    public void SoftKneeExpander_HandlesQFactorOne()
    {
        var signal = new double[] { 100.0, 50.0, 25.0, 10.0 };
        var noiseFloor = 20.0;

        var result = _engine.SoftKneeDownwardExpander(signal, noiseFloor, kneeSlope: 1000.0);

        Assert.NotNull(result);
    }

    [Fact]
    public void QToKneeSlope_NeverReturnsInfinity()
    {
        var kneeSlope1 = _engine.QToKneeSlope(0.99999);
        var kneeSlope2 = _engine.QToKneeSlope(1.0);
        var kneeSlope3 = _engine.QToKneeSlope(-1.0);

        Assert.False(double.IsInfinity(kneeSlope1));
        Assert.False(double.IsInfinity(kneeSlope2));
        Assert.False(double.IsInfinity(kneeSlope3));
        Assert.True(kneeSlope1 > 0);
        Assert.True(kneeSlope2 > 0);
        Assert.True(kneeSlope3 > 0);
    }

    [Fact]
    public void SoftKneeExpander_HandlesEmptySignal()
    {
        var emptySignal = Array.Empty<double>();
        var result = _engine.SoftKneeDownwardExpander(emptySignal, 10.0);

        Assert.NotNull(result);
        Assert.Empty(result);
    }

    [Fact]
    public void SoftKneeExpander2D_HandlesNullMatrix()
    {
        var result = _engine.SoftKneeDownwardExpander2D(null!, 10.0);

        Assert.NotNull(result);
        Assert.Empty(result);
    }

    [Fact]
    public void NoiseFloor_WithUniformSignal_DoesNotThrow()
    {
        var uniformSignal = new double[,] { { 5.0, 5.0 }, { 5.0, 5.0 } };
        var envelope = new VanE.VanEnvelope
        {
            Header = "Uniform-Test",
            Carrier = "Pixel-Phase",
            QFactor = 0.95,
            Data = new List<object> { uniformSignal }
        };

        var result = _engine.ProcessPixelPhase(envelope);

        Assert.NotNull(result.ProcessedImage);
        Assert.True(result.NoiseFloorPreserved > 0);
    }

    [Fact]
    public void Demodulate_HandlesEmptyString()
    {
        var envelope = _engine.Demodulate("");

        Assert.NotNull(envelope);
        Assert.Empty(envelope.Header);
    }

    [Fact]
    public void Demodulate_ClampsQFactorToSafeRange()
    {
        var vanBlock = @"
            [TRANSITION: Q-Clamp-Test]
            {
              CARRIER: Pixel-Phase;
              MODULATION: Soft-Knee;
              Q-FACTOR: 1.5;
              DITHER: Texture;
              DATA: [""test""];
              DATATYPES: [""text/plain""];
            }";

        var envelope = _engine.Demodulate(vanBlock);

        Assert.True(envelope.QFactor < 1.0);
        Assert.True(envelope.QFactor > 0);
    }

    [Fact]
    public void SoftKneeExpander_HandlesNegativeSignalValues()
    {
        var signal = new double[] { -100.0, -5.0, -95.0, -3.0 };
        var noiseFloor = 10.0;

        var result = _engine.SoftKneeDownwardExpander(signal, noiseFloor, kneeSlope: 2.0,
            ditherProfile: new double[] { 0, 0, 0, 0 });

        Assert.Equal(-100.0, result[0], 0.1);
        Assert.True(Math.Abs(result[1]) < Math.Abs(signal[1]));
    }

    [Fact]
    public void ProcessSteelResonance_HandlesEmptyFrequencies()
    {
        var envelope = new VanE.VanEnvelope
        {
            Header = "Empty-Steel",
            Carrier = "Steel-Resonance",
            QFactor = 0.95,
            Data = new List<object> { Array.Empty<double>() }
        };

        var result = _engine.ProcessSteelResonance(envelope);

        Assert.NotNull(result.FilteredFrequencies);
        Assert.Empty(result.FilteredFrequencies);
    }

    [Fact]
    public void QToKneeSlope_ReturnsReasonableValues()
    {
        // Q=0 is clamped to MinQ=0.001, so slope ≈ 1.001
        var slopeLow = _engine.QToKneeSlope(0.0);
        var slopeMid = _engine.QToKneeSlope(0.5);
        var slopeHigh = _engine.QToKneeSlope(0.95);

        Assert.True(slopeLow >= 1.0 && slopeLow < 1.01);
        Assert.Equal(2.0, slopeMid, 5);
        Assert.True(slopeHigh > slopeMid);
    }
}
