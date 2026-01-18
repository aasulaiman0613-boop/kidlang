from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    kind: str
    lexeme: str
    line: int
    col: int
