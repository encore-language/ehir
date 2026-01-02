from dataclasses import dataclass

from src.core.instructions.base import Assignable
from src.core.primitives.base import PrimitiveType
from src.core.variable import Variable


@dataclass
class Instruction_pcast(Assignable):
    var: Variable
    type: PrimitiveType

    def __str__(self) -> str:
        return f"{str(super())}pcast {self.var}, {self.type}"
