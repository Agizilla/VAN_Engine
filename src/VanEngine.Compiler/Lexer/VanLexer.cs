namespace VanEngine.Compiler.Lexer;

public ref struct VanLexer
{
    private ReadOnlySpan<char> _input;
    private int _position;
    private int _line;

    public VanLexer(ReadOnlySpan<char> input)
    {
        _input = input;
        _position = 0;
        _line = 1;
    }

    public Token NextToken()
    {
        SkipWhitespaceAndComments();
        if (_position >= _input.Length)
            return new Token(TokenType.EOF, ReadOnlySpan<char>.Empty, _line);

        char c = _input[_position];

        if (c == '[') { _position++; return new Token(TokenType.LeftBracket, "[..]", _line); }
        if (c == ']') { _position++; return new Token(TokenType.RightBracket, "]", _line); }
        if (c == '{') { _position++; return new Token(TokenType.OpenBrace, "{", _line); }
        if (c == '}') { _position++; return new Token(TokenType.CloseBrace, "}", _line); }
        if (c == ':') { _position++; return new Token(TokenType.Colon, ":", _line); }
        if (c == ';') { _position++; return new Token(TokenType.Semicolon, ";", _line); }
        if (c == ',') { _position++; return new Token(TokenType.Comma, ",", _line); }
        if (c == '.') { _position++; return new Token(TokenType.Dot, ".", _line); }

        if (c == '"')
            return ReadString();

        if (char.IsDigit(c) || c == '-')
            return ReadNumber();

        if (char.IsLetter(c) || c == '_')
            return ReadIdentifier();

        _position++;
        return new Token(TokenType.Unknown, _input.Slice(_position - 1, 1), _line);
    }

    private Token ReadString()
    {
        int start = _position++;
        while (_position < _input.Length && _input[_position] != '"')
        {
            if (_input[_position] == '\\') _position++;
            _position++;
        }
        var value = _input.Slice(start + 1, _position - start - 1);
        _position++;
        return new Token(TokenType.StringLiteral, value, _line);
    }

    private Token ReadNumber()
    {
        int start = _position;
        while (_position < _input.Length && (char.IsDigit(_input[_position]) || _input[_position] == '.' || _input[_position] == '-'))
            _position++;
        return new Token(TokenType.Number, _input.Slice(start, _position - start), _line);
    }

    private Token ReadIdentifier()
    {
        int start = _position;
        while (_position < _input.Length && (char.IsLetterOrDigit(_input[_position]) || _input[_position] == '_' || _input[_position] == '-'))
            _position++;
        return new Token(TokenType.Identifier, _input.Slice(start, _position - start), _line);
    }

    private void SkipWhitespaceAndComments()
    {
        while (_position < _input.Length)
        {
            char c = _input[_position];

            if (char.IsWhiteSpace(c))
            {
                if (c == '\n') _line++;
                _position++;
                continue;
            }

            if (c == '/' && _position + 1 < _input.Length && _input[_position + 1] == '/')
            {
                while (_position < _input.Length && _input[_position] != '\n')
                    _position++;
                continue;
            }

            break;
        }
    }
}
