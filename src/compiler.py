from src.core.derectives.base import Derective
from src.simplifier.downgrader import Downgrader
from src.simplifier.normalizer import Normalizer
from src.simplifier.resolver import Resolver


class Compiler:
    def compile(self, ast: list[Derective]):
        resolver = Resolver()
        resolver.run(ast)

        downgrader = Downgrader()
        downgrader.run(ast)

        normalizer = Normalizer()
        normalizer.run(ast)

        print(*ast, sep="\n")
