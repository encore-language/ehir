from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from ehir.postprocessor import ProcessedModule


class OptProfile(Enum):
    debug = "debug"
    release = "release"
    extreme = "extreme"


class EHIR_Backend(ABC):
    @abstractmethod
    def compile(
        self,
        module: ProcessedModule,
        output_object_path: Path,
        output_file_path: Path,
        opt_level: OptProfile = OptProfile.debug,
    ) -> Path:
        raise NotImplementedError
