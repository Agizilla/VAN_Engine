namespace VanEngine.Core.VAN.Compiler.Lexer;

public readonly ref struct Token
{
    public TokenType Type { get; }
    public ReadOnlySpan<char> Value { get; }
    public int Line { get; }

    public Token(TokenType type, ReadOnlySpan<char> value, int line)
    {
        Type = type;
        Value = value;
        Line = line;
    }
}

public enum TokenType
{
    Transition, OpenBrace, CloseBrace, Colon, Semicolon,
    Identifier, StringLiteral, Number, Comma, Dot,
    LeftBracket, RightBracket, EOF, Unknown
}
