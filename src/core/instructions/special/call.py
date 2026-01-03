from dataclasses import dataclass

from src.core.instructions.base import Assignable
from src.core.variable import Variable


@dataclass
class Instruction_call(Assignable):
    fn_name: str
    args: list[Variable]

    def __str__(self) -> str:
        return f"{super().__str__()}call {self.fn_name}({', '.join(str(arg) for arg in self.args)})"
