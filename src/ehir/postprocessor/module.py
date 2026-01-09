from dataclasses import dataclass

from ehir.core.derectives import Derective_struct
from ehir.simplifier.normalizer.norm_fn import Normalized_fn


@dataclass
class ProcessedModule:
    name: str
    structs: list[Derective_struct]
    funcs: list[Normalized_fn]

    def __str__(self) -> str:
        return "\n".join(map(str, self.structs)) + "\n" * 2 + "\n".join(map(str, self.funcs))
