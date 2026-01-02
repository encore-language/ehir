from dataclasses import dataclass

from core.instructions.base import Instruction


@dataclass
class Instruction_br(Instruction):
    label: str

    def __str__(self) -> str:
        return f"br {self.label}"
