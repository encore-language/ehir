import llvmlite.ir as ir

from src.core.derectives.base import Derective


class Codegen:
    def __init__(self):
        self.module = ir.Module()
        self.builder = ir.IRBuilder()

    def run(self, ast: list[Derective]):
        for derective in ast:
            self._codegen_derective(derective)

    def _codegen_derective(self, derective: Derective):
        pass
