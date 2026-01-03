from pathlib import Path

from src.codegen.codegen import Codegen
from src.parser.parser import Parser
from src.simplifier.downgrader import Downgrader
from src.simplifier.normalizer import Normalizer
from src.simplifier.resolver import Resolver


class Compiler:
    def compile(self, program_path: Path):
        with program_path.open("r") as f:
            source_code = f.read()

        parser = Parser()
        ast = parser.parse(source_code)

        resolver = Resolver()
        resolver.run(ast)
        # print(*ast, sep="\n")

        downgrader = Downgrader()
        downgrader.run(ast)
        print(*ast, sep="\n")

        normalizer = Normalizer()
        normalizer.run(ast)
        # print(*ast, sep="\n")

        codegen = Codegen()
        codegen.run(ast)
