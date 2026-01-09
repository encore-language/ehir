from pathlib import Path

from ehir.parser.parser import Parser
from ehir.postprocessor import Postprocessor, ProcessedModule
from ehir.simplifier import Deallocator, Downgrader, Normalizer, Resolver


class Compiler:
    def __init__(self):
        self._parser = Parser()
        self._resolver = Resolver()
        self._normalizer = Normalizer()
        self._deallocator = Deallocator()
        self._downgrader = Downgrader()
        self._postprocessor = Postprocessor()

    def compile(self, program_path: Path) -> ProcessedModule:
        with program_path.open("r") as f:
            source_code = f.read()

        ast = self._parser.parse(source_code)
        # print(*ast, sep="\n")

        self._resolver.run(ast)
        # print(*ast, sep="\n")

        ast = self._normalizer.run(ast)
        # print(*ast, sep="\n")

        self._deallocator.run(ast)
        # print(*ast, sep="\n")

        self._downgrader.run(ast)
        # print(*ast, sep="\n")

        mod = self._postprocessor.run(ast, program_path.stem)
        # print(mod)
        return mod
