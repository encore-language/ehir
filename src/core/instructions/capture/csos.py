from dataclasses import dataclass

from src.core.instructions.base import Assignable
from src.core.struct import Struct


@dataclass
class Instruction_csos(Assignable):
    struct: Struct

    def __str__(self) -> str:
        return f"{super().__str__()}csos {self.struct}"
