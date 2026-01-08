from pathlib import Path

from src.codegen.codegen import Codegen
from src.parser.parser import Parser
from src.simplifier import Deallocator, Downgrader, Normalizer, Resolver


class Compiler:
    def compile(self, program_path: Path):
        with program_path.open("r") as f:
            source_code = f.read()

        parser = Parser()
        ast = parser.parse(source_code)
        # print(*ast, sep="\n")

        resolver = Resolver()
        resolver.run(ast)
        # print(*ast, sep="\n")

        normalizer = Normalizer()
        ast = normalizer.run(ast)
        # print(*ast, sep="\n")

        deallocator = Deallocator()
        deallocator.run(ast)
        # print(*ast, sep="\n")

        downgrader = Downgrader()
        downgrader.run(ast)
        print(*ast, sep="\n")

        codegen = Codegen()
        codegen.run(ast)
