from dataclasses import dataclass

from .base import Derective


@dataclass
class Derective_import(Derective):
    is_cross: bool
    module_path: list[str]
    symbol: str

    def __str__(self) -> str:
        cmd = "cimp" if self.is_cross else "imp"
        return f"{cmd} {'::'.join([*self.module_path, self.symbol])}"
