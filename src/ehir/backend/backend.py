from abc import ABC, abstractmethod
from enum import StrEnum, auto
from pathlib import Path

from ehir.postprocessor import ProcessedModule


class EHIR_Backend(ABC):
    class OptProfile(StrEnum):
        debug = auto()
        release = auto()
        extreme = auto()

    target_dir: Path
    opt_profile: OptProfile = OptProfile.debug

    @abstractmethod
    def compile_module(self, module: ProcessedModule) -> Path:
        raise NotImplementedError
