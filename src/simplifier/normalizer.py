from src.core.block import TerminatedBlock
from src.core.derectives import Derective_fn
from src.core.derectives.base import Derective
from src.core.instructions.base import Instruction
from src.core.instructions.control_flow.base import ControlFlow


class Normalizer:
    def run(self, ast: list[Derective]):
        for derective in ast:
            if isinstance(derective, Derective_fn):
                self._terminate_blocks(derective)
                self._normalize_fn(derective)

    def _terminate_blocks(self, derective: Derective_fn):
        new_blocks = []
        for block in derective.body:
            observed: list[Instruction] = []
            for instr in block.body:
                if isinstance(instr, ControlFlow):
                    break
                observed.append(instr)
            else:
                raise ValueError("Block must end with a control flow instruction")
            new_blocks.append(TerminatedBlock(name=block.name, body=observed, term=instr))
        derective.body = new_blocks

    def _normalize_fn(self, derective: Derective_fn):
        for block in derective.body:
            if block.name == "entry":
                break
        else:
            raise ValueError("Function must have an entry block")
