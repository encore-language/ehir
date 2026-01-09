from dataclasses import dataclass

from ehir.core.derectives import Derective_struct
from ehir.simplifier.normalizer.norm_fn import Normalized_fn


@dataclass
class ProcessedModule:
    name: str
    structs: list[Derective_struct]
    funcs: list[Normalized_fn]
