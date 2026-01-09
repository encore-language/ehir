from dataclasses import dataclass

from ehir.core.instructions.base import Assignable
from ehir.core.variable import Variable


@dataclass
class Instruction_getfield(Assignable):
    src: Variable
    indexes: list[Variable]

    def __str__(self) -> str:
        body = [self.src, *self.indexes]
        return f"{super().__str__()}getfield {' > '.join(map(str, body))}"
