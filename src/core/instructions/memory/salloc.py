from dataclasses import dataclass

from src.core.instructions.base import Assignable
from src.core.type import Type


@dataclass
class Instruction_salloc(Assignable):
    type: Type

    def __str__(self) -> str:
        return f"{str(super())}salloc {self.type}"
