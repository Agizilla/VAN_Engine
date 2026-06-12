using VanEngine.Core.VAN;

namespace VanEngine.Core.VAN;

public ref struct JuulLexer
{
    private ReadOnlySpan<char> _input;
    private int _position;

    public JuulLexer(ReadOnlySpan<char> input)
    {
        _input = input;
        _position = 0;
    }

    public JuulMask? ReadNextMask()
    {
        while (_position < _input.Length && char.IsWhiteSpace(_input[_position]))
            _position++;

        if (_position >= _input.Length)
            return null;

        char c = _input[_position];
        _position++;

        return FryasAlphabet.GetMask(c);
    }

    public JuulMask[] ToMaskArray()
    {
        var list = new List<JuulMask>();
        while (ReadNextMask() is { } mask)
            list.Add(mask);
        return list.ToArray();
    }

    public int Position => _position;
    public bool HasMore => _position < _input.Length;
}
