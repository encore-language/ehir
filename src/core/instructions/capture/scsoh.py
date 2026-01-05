from dataclasses import dataclass

from src.core.instructions.base import Assignable
from src.core.struct import Struct


@dataclass
class Instruction_scsoh(Assignable):
    struct: Struct

    def __str__(self) -> str:
        return f"{super().__str__()}scsoh {self.struct}"
