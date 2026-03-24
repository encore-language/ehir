from pathlib import Path

from ehir.backend import EHIR_Backend
from ehir.postprocessor import ProcessedModule


class EHIR_DirectBackend(EHIR_Backend):
    def compile_module(
        self,
        module: ProcessedModule,
        name: str,
    ) -> Path:
        target = self.profile_path / name
        with target.open("w") as f:
            f.write(module.__str__())
        return target
