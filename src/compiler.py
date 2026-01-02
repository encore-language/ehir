from src.core.derectives.base import Derective
from src.simplifier.resolver import Resolver


class Compiler:
    def compile(self, ast: list[Derective]):
        resolver = Resolver()
        resolver.resolve_ast(ast)
        print(*ast, sep="\n")
