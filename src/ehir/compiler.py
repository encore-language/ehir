from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

from ehir.core.derectives import (
    Derective_enum,
    Derective_fn,
    Derective_impl,
    Derective_import,
    Derective_struct,
    Derective_trait,
)
from ehir.core.derectives.base import Derective
from ehir.parser.parser import Parser
from ehir.postprocessor import Postprocessor, ProcessedModule
from ehir.simplifier import Deallocator, Downgrader, Normalizer, Resolver
from ehir.simplifier.cfree import Cfree_Simplifier_Pass


def _derective_symbol_name(derective: Derective) -> str | None:
    if isinstance(derective, (Derective_fn, Derective_struct, Derective_enum, Derective_trait)):
        return derective.name
    return None


def _is_public_derective(derective: Derective) -> bool:
    if isinstance(derective, Derective_impl):
        return True
    return bool(getattr(derective, "is_public", False))


def _impl_key(derective: Derective_impl) -> str:
    methods_repr = ",".join(method.name for method in derective.methods)
    return f"{derective.trait_name}|{derective.for_type}|{methods_repr}"


def _merge_impls(target: list[Derective_impl], source: list[Derective_impl]):
    seen = {_impl_key(impl) for impl in target}
    for impl in source:
        key = _impl_key(impl)
        if key in seen:
            continue
        target.append(impl)
        seen.add(key)


@dataclass
class _ImportEdge:
    derective: Derective_import
    path: Path


@dataclass
class _ProjectNode:
    path: Path
    local_derectives: list[Derective]
    local_symbols: dict[str, Derective]
    local_impls: list[Derective_impl]
    imports: list[_ImportEdge] = field(default_factory=list)
    exported_symbols: dict[str, Derective] = field(default_factory=dict)
    exported_impls: list[Derective_impl] = field(default_factory=list)


class ProjectTree:
    def __init__(self, entry_file: Path, parser: Parser):
        self.entry_file = entry_file.resolve()
        self._parser = parser
        self._nodes: dict[Path, _ProjectNode] = {}
        self._loading_stack: list[Path] = []
        self._project_root = self.entry_file.parent.resolve()
        self._workspace_root = Path(__file__).resolve().parents[2]
        self._std_root = self._workspace_root / "std"

    def build_flat_ast(self) -> list[Derective]:
        self._load_module(self.entry_file)
        order = self._build_topological_order(self.entry_file)
        for path in order:
            self._resolve_exports(self._nodes[path])

        # Keep compilation order deterministic: dependencies first.
        flat_ast: list[Derective] = []
        for path in order:
            flat_ast.extend(deepcopy(self._nodes[path].local_derectives))
        return flat_ast

    def _build_topological_order(self, start: Path) -> list[Path]:
        visited: set[Path] = set()
        order: list[Path] = []

        def visit(path: Path):
            if path in visited:
                return
            visited.add(path)
            node = self._nodes[path]
            for edge in node.imports:
                visit(edge.path)
            order.append(path)

        visit(start)
        return order

    def _resolve_exports(self, node: _ProjectNode):
        exported_symbols: dict[str, Derective] = {
            name: derective for name, derective in node.local_symbols.items() if _is_public_derective(derective)
        }
        exported_impls: list[Derective_impl] = list(node.local_impls)

        for edge in node.imports:
            dep_node = self._nodes[edge.path]
            imported_symbol_name = edge.derective.symbol

            if imported_symbol_name not in dep_node.exported_symbols:
                raise ValueError(
                    f"Symbol '{imported_symbol_name}' is not public in module "
                    f"'{edge.path}'. Use pub/cimp in the source module."
                )

            if edge.derective.is_cross:
                imported_symbol = dep_node.exported_symbols[imported_symbol_name]
                existing = exported_symbols.get(imported_symbol_name)
                if existing is not None and existing is not imported_symbol:
                    raise ValueError(
                        f"Export conflict in module '{node.path}': symbol '{imported_symbol_name}' is already defined."
                    )
                exported_symbols[imported_symbol_name] = imported_symbol
                _merge_impls(exported_impls, dep_node.exported_impls)

        node.exported_symbols = exported_symbols
        node.exported_impls = exported_impls

    def _load_module(self, module_path: Path):
        module_path = module_path.resolve()
        if module_path in self._nodes:
            return
        if module_path in self._loading_stack:
            cycle = " -> ".join(str(path) for path in [*self._loading_stack, module_path])
            raise ValueError(f"Import cycle detected: {cycle}")
        if not module_path.exists():
            raise FileNotFoundError(f"Imported module does not exist: {module_path}")

        self._loading_stack.append(module_path)
        source_code = module_path.read_text(encoding="utf-8")
        ast = self._parser.parse(source_code)
        imports = [d for d in ast if isinstance(d, Derective_import)]
        local_derectives = [d for d in ast if not isinstance(d, Derective_import)]
        local_symbols: dict[str, Derective] = {}
        local_impls: list[Derective_impl] = []

        for derective in local_derectives:
            if isinstance(derective, Derective_impl):
                local_impls.append(derective)
                continue
            symbol_name = _derective_symbol_name(derective)
            if symbol_name is None:
                continue
            if symbol_name in local_symbols:
                raise ValueError(f"Duplicate symbol '{symbol_name}' in file '{module_path}'.")
            local_symbols[symbol_name] = derective

        node = _ProjectNode(
            path=module_path,
            local_derectives=local_derectives,
            local_symbols=local_symbols,
            local_impls=local_impls,
        )
        self._nodes[module_path] = node

        for import_derective in imports:
            dep_path = self._resolve_import_file(import_derective, module_path)
            node.imports.append(_ImportEdge(derective=import_derective, path=dep_path))
            self._load_module(dep_path)

        self._loading_stack.pop()

    def _resolve_import_file(self, imp: Derective_import, importer_file: Path) -> Path:
        module_rel = Path(*imp.module_path)
        search_roots = [importer_file.parent, self._project_root, self._workspace_root, self._std_root]

        unique_roots: list[Path] = []
        seen_roots: set[Path] = set()
        for root in search_roots:
            root = root.resolve()
            if root in seen_roots:
                continue
            seen_roots.add(root)
            unique_roots.append(root)

        candidates: list[Path] = []
        for root in unique_roots:
            module_file = root.joinpath(*module_rel.parts).with_suffix(".ehir")
            module_main = root.joinpath(*module_rel.parts) / "main.ehir"
            candidates.extend([module_file, module_main])

        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

        candidates_repr = "\n".join(f" - {candidate}" for candidate in candidates)
        raise FileNotFoundError(
            f"Could not resolve import module path '{'::'.join(imp.module_path)}' "
            f"for symbol '{imp.symbol}' in '{importer_file}'.\nCandidates:\n{candidates_repr}"
        )


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
        ast = [derective for derective in ast if not isinstance(derective, Derective_import)]
        return self._compile_ast(ast, name)

    def compile_file(self, input_file: Path) -> ProcessedModule:
        input_file = input_file.resolve()
        tree = ProjectTree(entry_file=input_file, parser=self._parser)
        ast = tree.build_flat_ast()
        return self._compile_ast(ast, input_file.stem)

    def _compile_ast(self, ast: list[Derective], name: str) -> ProcessedModule:
        ast = self._resolver.run(ast)
        ast = self._normalizer.run(ast)
        self._deallocator.run(ast)
        ast = self._cfree_pass.run(ast)
        self._downgrader.run(ast)
        return self._postprocessor.run(ast, name)
