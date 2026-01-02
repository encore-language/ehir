from dataclasses import dataclass

from src.core.primitives.base import Primitive

from .assignable import Assignable


@dataclass
class Instruction_cpos(Assignable):
    primitive: Primitive

    def __str__(self) -> str:
        return f"{super().__str__()}cpos {self.primitive}"
