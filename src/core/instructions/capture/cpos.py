from dataclasses import dataclass

from src.core.instructions.base import Assignable
from src.core.primitives.base import Primitive


@dataclass
class Instruction_cpos(Assignable):
    primitive: Primitive

    def __str__(self) -> str:
        return f"{super().__str__()}cpos {self.primitive}"
