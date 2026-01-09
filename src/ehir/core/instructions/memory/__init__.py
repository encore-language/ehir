from .getfield import Instruction_getfield
from .getfieldptr import Instruction_getfieldptr
from .getptr import Instruction_getptr
from .halloc import Instruction_halloc
from .hfree import Instruction_hfree
from .load import Instruction_load
from .pcast import Instruction_pcast
from .put import Instruction_put
from .salloc import Instruction_salloc
from .store import Instruction_store

__all__ = [
    "Instruction_pcast",
    "Instruction_getfield",
    "Instruction_getfieldptr",
    "Instruction_getptr",
    "Instruction_hfree",
    "Instruction_halloc",
    "Instruction_salloc",
    "Instruction_load",
    "Instruction_store",
    "Instruction_put",
]
