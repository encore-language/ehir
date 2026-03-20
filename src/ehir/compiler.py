from ehir.parser.parser import Parser
from ehir.postprocessor import Postprocessor, ProcessedModule
from ehir.simplifier import Deallocator, Downgrader, Normalizer, Resolver
from ehir.simplifier.cfree import Cfree_Simplifier_Pass


class Compiler:
    def __init__(self):
        self._parser = Parser()
        self._resolver = Resolver()
        self._normalizer = Normalizer()
        self._deallocator = Deallocator()
        self._cfree_pass = Cfree_Simplifier_Pass()
        self._downgrader = Downgrader()
        self._postprocessor = Postprocessor()

    def compile(self, source_code: str, name: str) -> ProcessedModule:
        ast = self._parser.parse(source_code)
        print(*ast, sep="\n")

        ast = self._resolver.run(ast)
        print(*ast, sep="\n")

        ast = self._normalizer.run(ast)
        # print(*ast, sep="\n")

        self._deallocator.run(ast)
        # print(*ast, sep="\n")

        ast = self._cfree_pass.run(ast)
        # print(*ast, sep="\n")

        self._downgrader.run(ast)
        # print(*ast, sep="\n")

        mod = self._postprocessor.run(ast, name)
        # print(mod)
        return mod
