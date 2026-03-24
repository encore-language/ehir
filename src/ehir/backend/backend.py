from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path

from ehir.postprocessor import ProcessedModule


@dataclass
class EHIR_Backend(ABC):
    class OptProfile(StrEnum):
        debug = auto()
        release = auto()
        extreme = auto()

    target_dir: Path
    opt_profile: OptProfile = OptProfile.debug

    @property
    def profile_path(self) -> Path:
        return self.target_dir / self.opt_profile

    def __post_init__(self):
        self.profile_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def compile_module(self, module: ProcessedModule, name: str) -> Path:
        raise NotImplementedError
