from dataclasses import dataclass

from src.core.type import Type
from src.core.variable import Parameter

from .base import Derective


@dataclass
class Derective_fdecl(Derective):
    name: str
    params: list[Parameter]
    ret_type: Type

    def __str__(self) -> str:
        return f"fdecl {self.name}({', '.join(str(param) for param in self.params)}) -> {self.ret_type}"
