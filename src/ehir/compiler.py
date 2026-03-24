from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path

from ehir.backend import EHIR_Backend
from ehir.builder import EHIR_Module
from ehir.core.derectives import Derective_enum, Derective_fn, Derective_import, Derective_struct
from ehir.format import ThemePalette, printfmt
from ehir.frontend import EHIR_Frontend
from ehir.postprocessor import Postprocessor, ProcessedModule
from ehir.simplifier import Deallocator, Downgrader, Normalizer, Resolver
from ehir.simplifier.cfree import Cfree_Simplifier_Pass


@dataclass
class Refrain:
    class TargetType(StrEnum):
        BINARY = auto()
        LIBRARY = auto()

    name: str
    path: Path
    type: TargetType = TargetType.BINARY


@dataclass
class TreeNode:
    module: EHIR_Module
    dependencies: set[Path] = field(default_factory=set)


@dataclass
class EHIR_ProjectCompiler:
    frontend: EHIR_Frontend
    backend: EHIR_Backend
    refrains: dict[str, Refrain] = field(default_factory=dict)
    tree: dict[Path, TreeNode] = field(default_factory=dict)

    def add_refrain_to_build(self, refrain: Refrain):
        if refrain.name in self.refrains:
            return
        self.refrains[refrain.name] = refrain

    def compile_all(self) -> list[tuple[str, Path]]:
        result = []
        for refrain in self.refrains.values():
            mod = self._compile_refrain(refrain)
            self.backend.compile_module(mod, name=refrain.name)
        return result

    def _compile_refrain(self, refrain: Refrain) -> ProcessedModule:
        printfmt(f"[{refrain.name}] Compiling...\n", style=ThemePalette.ACCENT_TEXT)

        suffix = ("lib" if refrain.type == Refrain.TargetType.LIBRARY else "main") + self.frontend.get_file_extension()
        node = self._compile_node_by_id(refrain.path / "src" / suffix)
        module = EHIR_Module(
            id=node.module.id,
            ast=deepcopy(node.module.ast),
        )

        module.ast = Resolver().run(module.ast)
        module.ast = Normalizer().run(module.ast)
        module.ast = Deallocator().run(module.ast)
        module.ast = Cfree_Simplifier_Pass().run(module.ast)
        module.ast = Downgrader().run(module.ast)
        processed_mod = Postprocessor().run(module)

        return processed_mod

    def _compile_node_by_id(self, id: Path) -> TreeNode:
        if node := self.tree.get(id):
            return node

        original_module = self.frontend.get_module_by_id(id=id)

        module = EHIR_Module(
            id=original_module.id,
            ast=list(original_module.ast),
        )

        node = TreeNode(module)
        self.tree[id] = node

        resolved_ast = []

        for directive in module.ast:
            if not isinstance(directive, Derective_import):
                resolved_ast.append(directive)
                continue

            parent_refrain_name = directive.prefix[0]

            if parent_refrain_name in self.refrains:
                parent_id = self.refrains[parent_refrain_name].path / "src" / f"lib{self.frontend.get_file_extension()}"
            else:
                parent_id = (id.parent / Path(*directive.prefix)).with_suffix(self.frontend.get_file_extension())
                if not parent_id.exists():
                    parent_id = parent_id.parent / parent_id.stem / f"mod{self.frontend.get_file_extension()}"

            if not parent_id.exists():
                raise RuntimeError(f"Unable to find import path: {parent_id}")

            node.dependencies.add(parent_id)

            parent_node = self._compile_node_by_id(parent_id)
            parent_ast = parent_node.module.ast

            if directive.symbol == "*":
                for d in parent_ast:
                    if isinstance(d, Derective_import):
                        continue
                    resolved_ast.append(d)

            else:
                for d in parent_ast:
                    if isinstance(d, Derective_import):
                        continue

                    if isinstance(d, (Derective_fn, Derective_struct, Derective_enum)) and d.name == directive.symbol:
                        resolved_ast.append(d)
                        break
                else:
                    raise RuntimeError(f"Unable to import: {directive}")

        node.module.ast = resolved_ast
        return node
