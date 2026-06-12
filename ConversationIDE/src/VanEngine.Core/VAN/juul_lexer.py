from __future__ import annotations

from .fryas_alphabet import FryasAlphabet
from .juul_mask import JuulMask


class JuulLexer:
    def __init__(self, input_text: str):
        self._input = input_text
        self._position = 0

    def read_next_mask(self) -> JuulMask | None:
        while self._position < len(self._input) and self._input[self._position].isspace():
            self._position += 1

        if self._position >= len(self._input):
            return None

        ch = self._input[self._position]
        self._position += 1
        return FryasAlphabet.get_mask(ch)

    def to_mask_array(self) -> list[JuulMask]:
        masks: list[JuulMask] = []
        while True:
            m = self.read_next_mask()
            if m is None:
                break
            masks.append(m)
        return masks

    @property
    def position(self) -> int:
        return self._position

    @property
    def has_more(self) -> bool:
        return self._position < len(self._input)
