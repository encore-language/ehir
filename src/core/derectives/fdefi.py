from dataclasses import dataclass

from src.core.block import Block

from .base import Derective


@dataclass
class Derective_fdefi(Derective):
    name: str
    body: list[Block]

    def __str__(self) -> str:
        body_repr = "\n".join("\n".join(f"  {line}" for line in str(b).splitlines()) for b in self.body)
        return f"fdefi {self.name}" + " {\n" + body_repr + "\n}"
