from dataclasses import dataclass

from ehir.core.block import Block
from ehir.core.type import Type
from ehir.core.variable import Parameter

from .base import Derective


@dataclass
class Derective_fn(Derective):
    name: str
    generics: list[Type]
    params: list[Parameter]
    body: list[Block]
    ret_type: Type

    def get_body(self) -> list[Block]:
        return self.body

    def get_conrete_name(self, types: list[Type]) -> str:
        types_repr = "_".join(str(x) for x in types)
        return f"{self.name}_{types_repr}"

    def __str__(self) -> str:
        params_repr = ", ".join(str(p) for p in self.params)
        body_repr = "\n".join("\n".join(f"  {line}" for line in str(b).splitlines()) for b in self.get_body())
        generics_repr = ("[" + ", ".join(str(x) for x in self.generics) + "]") if self.generics else ""
        return f"fn {self.name}{generics_repr}({params_repr}) -> {self.ret_type}" + " {\n" + body_repr + "\n}"
