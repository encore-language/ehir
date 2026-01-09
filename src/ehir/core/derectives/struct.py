from dataclasses import dataclass

from ehir.core.variable import Parameter

from .base import Derective


@dataclass
class Derective_struct(Derective):
    name: str
    params: list[Parameter]

    def __str__(self) -> str:
        params_repr = "\n  ".join(str(p) for p in self.params)
        return f"struct {self.name} {{\n  {params_repr} \n}}"
