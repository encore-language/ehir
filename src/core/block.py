from dataclasses import dataclass

from src.core.instructions.base import Instruction


@dataclass
class Block:
    name: str
    body: list[Instruction]

    def __str__(self) -> str:
        instructions = "\n  ".join(str(instr) for instr in self.body)
        return f"${self.name}:\n  {instructions}"


@dataclass
class TerminatedBlock(Block):
    term: Instruction
