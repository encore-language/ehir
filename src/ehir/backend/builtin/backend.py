from pathlib import Path

from ehir.backend import EHIR_Backend
from ehir.format import printfmt
from ehir.postprocessor import ProcessedModule


class EHIR_DirectBackend(EHIR_Backend):
    def compile_module(
        self,
        module: ProcessedModule,
    ) -> Path:
        printfmt(module.__str__())
        return Path(module.id)
