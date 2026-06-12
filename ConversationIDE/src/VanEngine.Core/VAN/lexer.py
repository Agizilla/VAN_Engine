from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    Transition = "Transition"
    OpenBrace = "OpenBrace"
    CloseBrace = "CloseBrace"
    Colon = "Colon"
    Semicolon = "Semicolon"
    Identifier = "Identifier"
    StringLiteral = "StringLiteral"
    Number = "Number"
    Comma = "Comma"
    Dot = "Dot"
    LeftBracket = "LeftBracket"
    RightBracket = "RightBracket"
    EOF = "EOF"
    Unknown = "Unknown"


@dataclass
class Token:
    Type: TokenType
    Value: str
    Line: int


class VanLexer:
    def __init__(self, input_str: str):
        self._input = input_str
        self._position = 0
        self._line = 1

    def NextToken(self) -> Token:
        self._skip_whitespace_and_comments()
        if self._position >= len(self._input):
            return Token(TokenType.EOF, "", self._line)

        c = self._input[self._position]

        if c == "[":
            self._position += 1
            return Token(TokenType.LeftBracket, "[", self._line)
        if c == "]":
            self._position += 1
            return Token(TokenType.RightBracket, "]", self._line)
        if c == "{":
            self._position += 1
            return Token(TokenType.OpenBrace, "{", self._line)
        if c == "}":
            self._position += 1
            return Token(TokenType.CloseBrace, "}", self._line)
        if c == ":":
            self._position += 1
            return Token(TokenType.Colon, ":", self._line)
        if c == ";":
            self._position += 1
            return Token(TokenType.Semicolon, ";", self._line)
        if c == ",":
            self._position += 1
            return Token(TokenType.Comma, ",", self._line)
        if c == ".":
            self._position += 1
            return Token(TokenType.Dot, ".", self._line)

        if c == '"':
            return self._read_string()

        if c.isdigit() or c == "-":
            return self._read_number()

        if c.isalpha() or c == "_":
            return self._read_identifier()

        self._position += 1
        return Token(TokenType.Unknown, self._input[self._position - 1], self._line)

    def _read_string(self) -> Token:
        start = self._position
        self._position += 1
        while self._position < len(self._input) and self._input[self._position] != '"':
            if self._input[self._position] == "\\":
                self._position += 1
            self._position += 1
        value = self._input[start + 1 : self._position]
        self._position += 1
        return Token(TokenType.StringLiteral, value, self._line)

    def _read_number(self) -> Token:
        start = self._position
        while self._position < len(self._input) and (
            self._input[self._position].isdigit()
            or self._input[self._position] == "."
            or self._input[self._position] == "-"
        ):
            self._position += 1
        return Token(
            TokenType.Number,
            self._input[start : self._position],
            self._line,
        )

    def _read_identifier(self) -> Token:
        start = self._position
        while self._position < len(self._input) and (
            self._input[self._position].isalnum()
            or self._input[self._position] == "_"
            or self._input[self._position] == "-"
        ):
            self._position += 1
        return Token(
            TokenType.Identifier,
            self._input[start : self._position],
            self._line,
        )

    def _skip_whitespace_and_comments(self) -> None:
        while self._position < len(self._input):
            c = self._input[self._position]

            if c.isspace():
                if c == "\n":
                    self._line += 1
                self._position += 1
                continue

            if (
                c == "/"
                and self._position + 1 < len(self._input)
                and self._input[self._position + 1] == "/"
            ):
                while self._position < len(self._input) and self._input[self._position] != "\n":
                    self._position += 1
                if self._position < len(self._input) and self._input[self._position] == "\n":
                    self._position += 1
                    self._line += 1
                continue

            break
