from dataclasses import dataclass

from src.core.instructions.base import Assignable
from src.core.type import Type
from src.core.variable import Variable


@dataclass
class Instruction_cast(Assignable):
    var: Variable
    type: Type

    def __str__(self) -> str:
        return f"{str(super())}cast {self.var}, {self.type}"
