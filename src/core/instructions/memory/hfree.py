from dataclasses import dataclass

from src.core.instructions.base import Instruction
from src.core.variable import Variable


@dataclass
class Instruction_hfree(Instruction):
    var: Variable

    def __str__(self) -> str:
        return f"hfree {self.var}"
