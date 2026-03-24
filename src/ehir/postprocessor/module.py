from dataclasses import dataclass
from pathlib import Path

from ehir.core.derectives import Derective_struct
from ehir.simplifier.normalizer.norm_fn import Normalized_fn


@dataclass
class ProcessedModule:
    id: Path
    structs: list[Derective_struct]
    funcs: list[Normalized_fn]

    def __str__(self) -> str:
        return "\n\n".join(map(str, [*self.structs, *self.funcs]))
