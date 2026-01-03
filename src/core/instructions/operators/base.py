from dataclasses import dataclass

from src.core.instructions.base import Assignable
from src.core.variable import Variable


@dataclass
class BinOp(Assignable):
    lhs: Variable
    rhs: Variable
