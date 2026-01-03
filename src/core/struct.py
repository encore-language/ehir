from dataclasses import dataclass

from src.core.type import Type
from src.core.variable import Parameter


@dataclass
class Struct:
    name: str
    args: list[Parameter]

    def as_type(self) -> Type:
        return Type(self.name)

    def __str__(self) -> str:
        params_repr = ", ".join(str(p) for p in self.args)
        return f"{self.name}({params_repr})"
