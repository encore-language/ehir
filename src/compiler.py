from src.core.derectives.base import Derective
from src.simplifier.downgrader.downgrader import Downgrader
from src.simplifier.resolver import Resolver


class Compiler:
    def compile(self, ast: list[Derective]):
        resolver = Resolver()
        resolver.resolve_ast(ast)

        downgrader = Downgrader()
        downgrader.run(ast)

        print(*ast, sep="\n")
