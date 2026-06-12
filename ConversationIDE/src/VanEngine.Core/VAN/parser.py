from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from .enums import VanBlockType
from .lexer import TokenType, VanLexer


@dataclass
class AstEnvelope:
    BlockType: VanBlockType = VanBlockType.Transition
    Header: str = ""
    Carrier: str = ""
    Modulation: str = ""
    QFactor: float = 0.95
    Dither: str = ""
    Data: List[Any] = field(default_factory=list)
    DataTypes: List[str] = field(default_factory=list)
    Executor: Optional[Callable] = None
    LineNumber: int = 0
    SourceFile: str = ""


class VanParser:
    def __init__(self, input_str: str):
        self._lexer = VanLexer(input_str)
        self._current = self._lexer.NextToken()

    def Parse(self) -> List[AstEnvelope]:
        envelopes: List[AstEnvelope] = []
        while self._current.Type != TokenType.EOF:
            if self._current.Type == TokenType.LeftBracket:
                self._current = self._lexer.NextToken()
                if self._current.Type == TokenType.Identifier:
                    label = self._current.Value
                    self._current = self._lexer.NextToken()
                    if label.upper() in ("TRANSITION", "STATE"):
                        env = self._parse_transition(label)
                        if env is not None:
                            envelopes.append(env)
            else:
                self._current = self._lexer.NextToken()
        return envelopes

    def _parse_transition(self, label: str) -> Optional[AstEnvelope]:
        self._consume(TokenType.Colon)
        header = self._consume_identifier_value()
        self._consume(TokenType.RightBracket)

        envelope = AstEnvelope(
            Header=f"{label}:{header}",
            LineNumber=self._current.Line,
            BlockType=VanBlockType.State if label.upper() == "STATE" else VanBlockType.Transition,
        )

        self._consume(TokenType.OpenBrace)

        while self._current.Type not in (TokenType.CloseBrace, TokenType.EOF):
            key = self._consume_identifier_value()
            self._consume(TokenType.Colon)

            if key == "CARRIER":
                envelope.Carrier = self._parse_value()
            elif key == "MODULATION":
                envelope.Modulation = self._parse_value()
            elif key == "Q-FACTOR":
                q_val = self._parse_value()
                try:
                    envelope.QFactor = float(q_val)
                except (ValueError, TypeError):
                    pass
            elif key == "DITHER":
                envelope.Dither = self._parse_value()
            elif key == "DATA":
                envelope.Data = self._parse_array()
            elif key == "DATATYPES":
                envelope.DataTypes = self._parse_string_array()
            else:
                self._skip_value()

            if self._current.Type == TokenType.Semicolon:
                self._current = self._lexer.NextToken()

        self._consume(TokenType.CloseBrace)
        return envelope

    def _parse_value(self) -> str:
        if self._current.Type == TokenType.StringLiteral:
            val = self._current.Value
            self._current = self._lexer.NextToken()
            return val
        if self._current.Type == TokenType.Identifier:
            return self._consume_identifier_value()
        if self._current.Type == TokenType.Number:
            val = self._current.Value
            self._current = self._lexer.NextToken()
            return val
        return ""

    def _skip_value(self) -> None:
        while self._current.Type not in (TokenType.Semicolon, TokenType.CloseBrace, TokenType.EOF):
            self._current = self._lexer.NextToken()

    def _parse_array(self) -> List[Any]:
        items: List[Any] = []
        self._consume(TokenType.LeftBracket)
        while self._current.Type not in (TokenType.RightBracket, TokenType.EOF):
            if self._current.Type == TokenType.StringLiteral:
                items.append(self._current.Value)
                self._current = self._lexer.NextToken()
            elif self._current.Type == TokenType.Number:
                try:
                    items.append(float(self._current.Value))
                except ValueError:
                    items.append(self._current.Value)
                self._current = self._lexer.NextToken()
            if self._current.Type == TokenType.Comma:
                self._current = self._lexer.NextToken()
        self._consume(TokenType.RightBracket)
        return items

    def _parse_string_array(self) -> List[str]:
        items: List[str] = []
        self._consume(TokenType.LeftBracket)
        while self._current.Type not in (TokenType.RightBracket, TokenType.EOF):
            if self._current.Type == TokenType.StringLiteral:
                items.append(self._current.Value)
                self._current = self._lexer.NextToken()
            if self._current.Type == TokenType.Comma:
                self._current = self._lexer.NextToken()
        self._consume(TokenType.RightBracket)
        return items

    def _peek_identifier(self) -> str:
        if self._current.Type == TokenType.Identifier:
            return self._current.Value
        return ""

    def _consume_identifier_value(self) -> str:
        if self._current.Type != TokenType.Identifier:
            raise ValueError(
                f"Expected identifier at line {self._current.Line}, got {self._current.Type}"
            )
        val = self._current.Value
        self._current = self._lexer.NextToken()
        return val

    def _consume(self, expected: TokenType) -> None:
        if self._current.Type != expected:
            raise ValueError(
                f"Expected {expected} at line {self._current.Line}, got {self._current.Type}"
            )
        self._current = self._lexer.NextToken()
