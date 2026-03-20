from dataclasses import dataclass

from ehir.core.type import Type
from ehir.core.variable import Parameter

from .base import Derective


@dataclass
class Derective_struct(Derective):
    name: str
    generics: list[Type]
    params: list[Parameter]

    def __str__(self) -> str:
        generics_repr = ("[" + ", ".join(str(x) for x in self.generics) + "]") if self.generics else ""
        params_repr = "\n  ".join(str(p) for p in self.params)
        return f"struct {self.name}{generics_repr} {{\n  {params_repr} \n}}"
