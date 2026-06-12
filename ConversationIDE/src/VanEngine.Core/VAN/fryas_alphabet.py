from __future__ import annotations

from .juul_mask import JuulMask


class FryasAlphabet:
    _map: dict[str, JuulMask] = {
        # Vowels (7)
        "I": JuulMask.SPOKE0,
        "—": JuulMask.SPOKE180,
        "O": JuulMask.OUTER_RIM,
        "Λ": JuulMask.SPOKE0 | JuulMask.SPOKE60,
        "V": JuulMask.SPOKE120 | JuulMask.SPOKE180,
        "/": JuulMask.SPOKE60,
        "\\": JuulMask.SPOKE300,
        # Core Consonants (16)
        "M": JuulMask.SPOKE0 | JuulMask.SPOKE180,
        "N": JuulMask.SPOKE60 | JuulMask.SPOKE240,
        "T": JuulMask.SPOKE0 | JuulMask.SPOKE60 | JuulMask.SPOKE120,
        "K": JuulMask.SPOKE180 | JuulMask.SPOKE240 | JuulMask.SPOKE300,
        "F": JuulMask.SPOKE0 | JuulMask.SPOKE180 | JuulMask.OUTER_RIM,
        "S": JuulMask.SPOKE0 | JuulMask.SPOKE60 | JuulMask.SPOKE120 | JuulMask.SPOKE180 | JuulMask.SPOKE240 | JuulMask.SPOKE300,
        "R": JuulMask.SPOKE60 | JuulMask.SPOKE180 | JuulMask.SPOKE300,
        "H": JuulMask.SPOKE240 | JuulMask.SPOKE300 | JuulMask.SPOKE0,
        # Remaining 8 consonants
        "B": JuulMask.SPOKE0 | JuulMask.SPOKE60 | JuulMask.OUTER_RIM,
        "D": JuulMask.SPOKE60 | JuulMask.SPOKE180 | JuulMask.OUTER_RIM,
        "G": JuulMask.SPOKE120 | JuulMask.SPOKE240 | JuulMask.SPOKE300,
        "L": JuulMask.SPOKE0 | JuulMask.SPOKE300,
        "P": JuulMask.SPOKE0 | JuulMask.SPOKE60 | JuulMask.SPOKE180,
        "W": JuulMask.SPOKE60 | JuulMask.SPOKE120 | JuulMask.SPOKE240,
        "J": JuulMask.SPOKE120 | JuulMask.SPOKE300,
        "Z": JuulMask.SPOKE0 | JuulMask.SPOKE240 | JuulMask.SPOKE300 | JuulMask.OUTER_RIM,
        # Numerals (5) — all include OUTER_RIM to distinguish from vowels
        "0": JuulMask.OUTER_RIM | JuulMask.SPOKE0 | JuulMask.SPOKE120,
        "1": JuulMask.OUTER_RIM | JuulMask.SPOKE60 | JuulMask.SPOKE300,
        "2": JuulMask.OUTER_RIM | JuulMask.SPOKE0 | JuulMask.SPOKE240,
        "3": JuulMask.OUTER_RIM | JuulMask.SPOKE120 | JuulMask.SPOKE300,
        "4": JuulMask.OUTER_RIM | JuulMask.SPOKE60 | JuulMask.SPOKE180 | JuulMask.SPOKE240,
        # Extended marks (6)
        "Þ": JuulMask.SPOKE0 | JuulMask.SPOKE60 | JuulMask.SPOKE240,
        "Ð": JuulMask.SPOKE60 | JuulMask.SPOKE180 | JuulMask.SPOKE240,
        "Æ": JuulMask.SPOKE0 | JuulMask.SPOKE120 | JuulMask.SPOKE180,
        "Œ": JuulMask.SPOKE60 | JuulMask.SPOKE120 | JuulMask.SPOKE240 | JuulMask.OUTER_RIM,
        "×": JuulMask.SPOKE0 | JuulMask.SPOKE120 | JuulMask.SPOKE240,
        "†": JuulMask.SPOKE60 | JuulMask.SPOKE180 | JuulMask.SPOKE300 | JuulMask.OUTER_RIM,
    }

    @staticmethod
    def get_mask(character: str) -> JuulMask:
        mask = FryasAlphabet._map.get(character)
        if mask is None:
            raise KeyError(f"Character '{character}' is not in the Fryas alphabet.")
        return mask

    @staticmethod
    def get_character(mask: JuulMask) -> str | None:
        for ch, m in FryasAlphabet._map.items():
            if m == mask:
                return ch
        return None
