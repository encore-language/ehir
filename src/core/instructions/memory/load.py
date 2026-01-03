from dataclasses import dataclass

from src.core.instructions.base import Assignable
from src.core.variable import Variable


@dataclass
class Instruction_load(Assignable):
    var: Variable

    def __str__(self) -> str:
        return f"{super().__str__()}load {self.var}"
