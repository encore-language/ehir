from copy import deepcopy
from dataclasses import dataclass

from ehir.core.type import Type
from ehir.core.variable import Variable


@dataclass
class Struct:
    name: str
    generics: list[Type]
    args: list[Variable]

    def as_type(self) -> Type:
        return Type(self.name, deepcopy(self.generics))

    def __str__(self) -> str:
        generics_repr = ("[" + ", ".join(str(x) for x in self.generics) + "]") if self.generics else ""
        params_repr = ", ".join(str(p) for p in self.args)
        return f"{self.name}{generics_repr}({params_repr})"
