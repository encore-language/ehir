from .cast import Instruction_cast
from .halloc import Instruction_halloc
from .hfree import Instruction_hfree
from .load import Instruction_load
from .put import Instruction_put
from .salloc import Instruction_salloc
from .store import Instruction_store

__all__ = [
    "Instruction_cast",
    "Instruction_hfree",
    "Instruction_halloc",
    "Instruction_salloc",
    "Instruction_load",
    "Instruction_store",
    "Instruction_put",
]
