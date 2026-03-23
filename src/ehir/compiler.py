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
            self._compile_refrain(refrain)
        return result

    def _compile_refrain(self, refrain: Refrain) -> ProcessedModule:
        printfmt(f"[{refrain.name}] Compiling...\n", style=ThemePalette.ACCENT_TEXT)

        suffix = ("lib" if refrain.type == Refrain.TargetType.LIBRARY else "main") + self.frontend.get_file_extension()
        node = self._compile_node_by_id(refrain.path / "src" / suffix)

        node.module.ast = Resolver().run(node.module.ast)
        node.module.ast = Normalizer().run(node.module.ast)
        node.module.ast = Deallocator().run(node.module.ast)
        node.module.ast = Cfree_Simplifier_Pass().run(node.module.ast)
        node.module.ast = Downgrader().run(node.module.ast)
        processed_mod = Postprocessor().run(node.module)

        return processed_mod

    def _compile_node_by_id(self, id: Path) -> TreeNode:
        if node := self.tree.get(id):
            return node

        module = self.frontend.get_module_by_id(id=id)
        node = TreeNode(module)
        self.tree[module.id] = node

        filtered_ast = []
        for derective in module.ast:
            if not isinstance(derective, Derective_import):
                filtered_ast.append(derective)
                continue

            print(id, derective)
            parent_refrain_name = derective.prefix[0]
            if parent_refrain_name in self.refrains:
                parent_id = self.refrains[parent_refrain_name].path / "src" / f"lib{self.frontend.get_file_extension()}"
            else:
                parent_id = (id.parent / Path(*derective.prefix)).with_suffix(self.frontend.get_file_extension())
                if not parent_id.exists():
                    parent_id = parent_id.parent / parent_id.stem / f"mod{self.frontend.get_file_extension()}"

            if not parent_id.exists():
                raise RuntimeError(f"Unable to import: {parent_id}")

            node.dependencies.add(parent_id)
            parent_node = self._compile_node_by_id(parent_id)

            if derective.symbol == "*":
                for parent_derective in parent_node.module.ast:
                    if not isinstance(parent_derective, Derective_import):
                        continue
                    filtered_ast.append(parent_derective)
            else:
                for parent_derective in parent_node.module.ast:
                    if isinstance(parent_derective, Derective_import):
                        continue

                    elif isinstance(parent_derective, (Derective_fn, Derective_struct, Derective_enum)) and (
                        parent_derective.name == derective.symbol or derective.symbol == "*"
                    ):
                        filtered_ast.append(parent_derective)
                        break
                else:
                    raise RuntimeError(f"Unable to import: {derective}")

        module.ast = filtered_ast
        return node
