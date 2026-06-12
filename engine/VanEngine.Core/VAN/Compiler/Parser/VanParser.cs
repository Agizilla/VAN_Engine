using VanEngine.Core.VAN.Compiler.Lexer;

namespace VanEngine.Core.VAN.Compiler.Parser;

public ref struct VanParser
{
    private VanLexer _lexer;
    private Token _current;

    public VanParser(ReadOnlySpan<char> input) : this()
    {
        _lexer = new VanLexer(input);
        _current = _lexer.NextToken();
    }

    public List<AstEnvelope> Parse()
    {
        var envelopes = new List<AstEnvelope>();
        while (_current.Type != TokenType.EOF)
        {
            if (_current.Type == TokenType.LeftBracket)
            {
                var label = PeekIdentifier();

                if (label.Equals("TRANSITION", StringComparison.Ordinal) ||
                    label.Equals("STATE", StringComparison.Ordinal))
                {
                    var env = ParseTransition();
                    if (env != null)
                    {
                        if (label.Equals("STATE", StringComparison.Ordinal))
                            env.BlockType = VanBlockType.State;
                        envelopes.Add(env);
                    }
                }
                else
                {
                    _current = _lexer.NextToken();
                }
            }
            else
            {
                _current = _lexer.NextToken();
            }
        }
        return envelopes;
    }

    private AstEnvelope? ParseTransition()
    {
        Consume(TokenType.LeftBracket);
        var label = ConsumeIdentifierValue();
        Consume(TokenType.Colon);
        var header = ConsumeIdentifierValue();
        Consume(TokenType.RightBracket);

        var envelope = new AstEnvelope
        {
            Header = $"{label.ToString()}:{header.ToString()}",
            LineNumber = _current.Line,
            BlockType = label.Equals("STATE", StringComparison.OrdinalIgnoreCase)
                ? VanBlockType.State
                : VanBlockType.Transition
        };

        Consume(TokenType.OpenBrace);

        while (_current.Type != TokenType.CloseBrace && _current.Type != TokenType.EOF)
        {
            var key = ConsumeIdentifierValue().ToString();
            Consume(TokenType.Colon);

            switch (key)
            {
                case "CARRIER":
                    envelope.Carrier = ParseValue();
                    break;
                case "MODULATION":
                    envelope.Modulation = ParseValue();
                    break;
                case "Q-FACTOR":
                    var qVal = ParseValue();
                    if (double.TryParse(qVal, out var q))
                        envelope.QFactor = q;
                    break;
                case "DITHER":
                    envelope.Dither = ParseValue();
                    break;
                case "DATA":
                    envelope.Data = ParseArray();
                    break;
                case "DATATYPES":
                    envelope.DataTypes = ParseStringArray();
                    break;
                default:
                    SkipValue();
                    break;
            }

            if (_current.Type == TokenType.Semicolon)
                _current = _lexer.NextToken();
        }

        Consume(TokenType.CloseBrace);
        return envelope;
    }

    private string ParseValue()
    {
        if (_current.Type == TokenType.StringLiteral)
        {
            var val = _current.Value.ToString();
            _current = _lexer.NextToken();
            return val;
        }
        if (_current.Type == TokenType.Identifier)
            return ConsumeIdentifierValue().ToString();
        if (_current.Type == TokenType.Number)
        {
            var val = _current.Value.ToString();
            _current = _lexer.NextToken();
            return val;
        }
        return string.Empty;
    }

    private void SkipValue()
    {
        while (_current.Type != TokenType.Semicolon && _current.Type != TokenType.CloseBrace && _current.Type != TokenType.EOF)
            _current = _lexer.NextToken();
    }

    private List<object> ParseArray()
    {
        var list = new List<object>();
        Consume(TokenType.LeftBracket);
        while (_current.Type != TokenType.RightBracket && _current.Type != TokenType.EOF)
        {
            if (_current.Type == TokenType.StringLiteral)
            {
                list.Add(_current.Value.ToString());
                _current = _lexer.NextToken();
            }
            else if (_current.Type == TokenType.Number)
            {
                if (double.TryParse(_current.Value, out var num))
                    list.Add(num);
                _current = _lexer.NextToken();
            }
            if (_current.Type == TokenType.Comma)
                _current = _lexer.NextToken();
        }
        Consume(TokenType.RightBracket);
        return list;
    }

    private List<string> ParseStringArray()
    {
        var list = new List<string>();
        Consume(TokenType.LeftBracket);
        while (_current.Type != TokenType.RightBracket && _current.Type != TokenType.EOF)
        {
            if (_current.Type == TokenType.StringLiteral)
            {
                list.Add(_current.Value.ToString());
                _current = _lexer.NextToken();
            }
            if (_current.Type == TokenType.Comma)
                _current = _lexer.NextToken();
        }
        Consume(TokenType.RightBracket);
        return list;
    }

    private ReadOnlySpan<char> PeekIdentifier()
    {
        if (_current.Type == TokenType.Identifier)
            return _current.Value;
        return ReadOnlySpan<char>.Empty;
    }

    private ReadOnlySpan<char> ConsumeIdentifierValue()
    {
        if (_current.Type != TokenType.Identifier)
            throw new InvalidOperationException($"Expected identifier at line {_current.Line}, got {_current.Type}");
        var val = _current.Value;
        _current = _lexer.NextToken();
        return val;
    }

    private void Consume(TokenType type)
    {
        if (_current.Type != type)
            throw new InvalidOperationException($"Expected {type} at line {_current.Line}, got {_current.Type}");
        _current = _lexer.NextToken();
    }
}
