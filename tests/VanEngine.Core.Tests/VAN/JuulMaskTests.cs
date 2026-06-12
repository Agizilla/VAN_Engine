using Xunit;
using VanEngine.Core.VAN;

namespace VanEngine.Core.Tests.VAN;

public sealed class JuulMaskTests
{
    [Fact]
    public void FryasAlphabet_HasExactly34Entries()
    {
        Assert.Equal(34, FryasAlphabet.Map.Count);
    }

    [Fact]
    public void GetMask_ReturnsCorrectMaskForVerticalSpoke()
    {
        var mask = FryasAlphabet.GetMask('I');
        Assert.Equal(JuulMask.Spoke0, mask);
    }

    [Fact]
    public void GetMask_ReturnsCorrectMaskForHorizontalSpoke()
    {
        var mask = FryasAlphabet.GetMask('—');
        Assert.Equal(JuulMask.Spoke180, mask);
    }

    [Fact]
    public void GetMask_ReturnsCorrectMaskForOuterRim()
    {
        var mask = FryasAlphabet.GetMask('O');
        Assert.Equal(JuulMask.OuterRim, mask);
    }

    [Fact]
    public void GetMask_ThrowsForInvalidCharacter()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => FryasAlphabet.GetMask('@'));
    }

    [Fact]
    public void JuulLexer_ConvertsTextToMaskStream()
    {
        const string fryasText = "I—O";
        var lexer = new JuulLexer(fryasText);
        var masks = lexer.ToMaskArray();
        Assert.Equal(3, masks.Length);
        Assert.Equal(JuulMask.Spoke0, masks[0]);
        Assert.Equal(JuulMask.Spoke180, masks[1]);
        Assert.Equal(JuulMask.OuterRim, masks[2]);
    }

    [Fact]
    public void JuulLexer_SkipsWhitespace()
    {
        const string fryasText = "I — O";
        var lexer = new JuulLexer(fryasText);
        var masks = lexer.ToMaskArray();
        Assert.Equal(3, masks.Length);
    }

    [Fact]
    public void JuulLexer_ReturnsEmptyForEmptyInput()
    {
        var lexer = new JuulLexer(string.Empty);
        var masks = lexer.ToMaskArray();
        Assert.Empty(masks);
    }

    [Fact]
    public void JuulLexer_StreamingWorks()
    {
        var lexer = new JuulLexer("I—O");
        Assert.Equal(JuulMask.Spoke0, lexer.ReadNextMask());
        Assert.Equal(JuulMask.Spoke180, lexer.ReadNextMask());
        Assert.Equal(JuulMask.OuterRim, lexer.ReadNextMask());
        Assert.Null(lexer.ReadNextMask());
    }

    [Fact]
    public void GetCharacter_RoundTrip()
    {
        var ch = FryasAlphabet.GetCharacter(JuulMask.Spoke0);
        Assert.Equal('I', ch);

        var mask = FryasAlphabet.GetMask('I');
        Assert.Equal(JuulMask.Spoke0, mask);
    }

    [Fact]
    public void AllMasksAreDistinct()
    {
        var masks = new HashSet<JuulMask>();
        foreach (var kv in FryasAlphabet.Map)
        {
            bool added = masks.Add(kv.Value);
            Assert.True(added, $"Duplicate JuulMask {kv.Value} for character '{kv.Key}'");
        }
    }

    [Fact]
    public void JuulMask_FlagsWork()
    {
        var combined = JuulMask.Spoke0 | JuulMask.Spoke60;
        Assert.True(combined.HasFlag(JuulMask.Spoke0));
        Assert.True(combined.HasFlag(JuulMask.Spoke60));
        Assert.False(combined.HasFlag(JuulMask.Spoke120));
    }

    [Fact]
    public void VanEngine_TokenizeToJuul()
    {
        var engine = new VanEngine.Core.VAN.VanEngine();
        var masks = engine.TokenizeToJuul("I—O");
        Assert.Equal(3, masks.Length);
        Assert.Equal(JuulMask.Spoke0, masks[0]);
        Assert.Equal(JuulMask.Spoke180, masks[1]);
    }
}
