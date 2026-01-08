from dataclasses import dataclass

from src.core.block import Block, TerminatedBlock
from src.core.derectives import Derective_fn


@dataclass
class Normalized_fn(Derective_fn):
    entry_block: TerminatedBlock
    body: list[TerminatedBlock]
    exit_block: TerminatedBlock

    def __post_init__(self):
        assert self.entry_block.name == "entry"

    def get_body(self) -> list[Block]:
        return [self.entry_block, *self.body, self.exit_block]
