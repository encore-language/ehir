from dataclasses import dataclass

from src.core.block import Block
from src.core.type import Type
from src.core.variable import Parameter

from .base import Derective


@dataclass
class Derective_fn(Derective):
    name: str
    params: list[Parameter]
    body: list[Block]
    ret_type: Type

    def __str__(self) -> str:
        params_repr = ", ".join(str(p) for p in self.params)
        body_repr = "\n".join("\n".join(f"  {line}" for line in str(b).splitlines()) for b in self.body)
        return f"fn {self.name}({params_repr}) -> {self.ret_type}" + " {\n" + body_repr + "\n}"
