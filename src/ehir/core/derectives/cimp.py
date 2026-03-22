from dataclasses import dataclass

from .base import Derective


@dataclass
class Derective_cimp(Derective):
    prefix: list[str]
    symbol: str

    def __post_init__(self):
        assert len(self.prefix) > 0

    def __str__(self) -> str:
        return f"cimp {'::'.join(self.prefix + [self.symbol])}"
