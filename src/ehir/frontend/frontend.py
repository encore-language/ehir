from abc import ABC, abstractmethod

from ehir.builder import EHIR_Module
from ehir.core.derectives import Derective_import


class EHIR_Frontend(ABC):
    @abstractmethod
    def get_module_by_id(self, id: str) -> EHIR_Module:
        raise NotImplementedError

    @abstractmethod
    def get_parent_id_of(self, id: str, derective: Derective_import) -> str:
        raise NotImplementedError
