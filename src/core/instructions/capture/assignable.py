from dataclasses import dataclass

from src.core.variable import Variable

from ..base import Instruction


@dataclass
class Assignable(Instruction):
    var_out: Variable

    def __str__(self) -> str:
        return f"{self.var_out} = "
