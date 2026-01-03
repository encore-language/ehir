from dataclasses import dataclass

from src.core.instructions.base import Instruction
from src.core.primitives.base import Primitive
from src.core.variable import Variable


@dataclass
class Instruction_put(Instruction):
    primitive: Primitive
    var: Variable

    def __str__(self) -> str:
        return f"put {self.primitive}, {self.var}"
