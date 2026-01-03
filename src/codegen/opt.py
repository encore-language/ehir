from dataclasses import dataclass
from enum import Enum
from typing import Optional

import llvmlite.binding as llvm
from llvmlite import ir


class OptLevel(Enum):
    O0 = "O0"
    O1 = "O1"
    O2 = "O2"
    O3 = "O3"
    Os = "Os"
    Oz = "Oz"


@dataclass
class OptConfig:
    level: OptLevel = OptLevel.O0
    target_triple: str = ""
    debug: bool = False


class Optimizer:
    config: OptConfig

    def __init__(self, config: Optional[OptConfig] = None):
        self.config = config or OptConfig()

        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

    def optimize(self, module: ir.Module) -> llvm.ModuleRef:
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()

        module_llvm = llvm.parse_assembly(str(module))

        speed_level = 0
        size_level = 0
        if self.config.level == OptLevel.O0:
            pass
        elif self.config.level == OptLevel.O1:
            speed_level = 1
        elif self.config.level == OptLevel.O2:
            speed_level = 2
        elif self.config.level == OptLevel.O3:
            speed_level = 3
        elif self.config.level == OptLevel.Os:
            speed_level = 2
            size_level = 1
        elif self.config.level == OptLevel.Oz:
            speed_level = 2
            size_level = 2
        pto = llvm.create_pipeline_tuning_options(speed_level=speed_level, size_level=size_level)
        pto.loop_vectorization = True
        pto.slp_vectorization = True
        pto.loop_unrolling = True
        pass_builder = llvm.create_pass_builder(target_machine, pto)
        mpm = pass_builder.getModulePassManager()
        mpm.run(module_llvm, pass_builder)

        # Function
        fpm = pass_builder.getFunctionPassManager()
        for function in module_llvm.functions:
            fpm.run(function, pass_builder)

        module_llvm.verify()
        return module_llvm
