from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path

from ehir.backend import EHIR_Backend
from ehir.builder import EHIR_Module
from ehir.core.derectives import Derective_enum, Derective_fn, Derective_import, Derective_struct
from ehir.format import ThemePalette, printfmt
from ehir.frontend import EHIR_Frontend
from ehir.postprocessor import Postprocessor
from ehir.simplifier import Deallocator, Downgrader, Normalizer, Resolver
from ehir.simplifier.cfree import Cfree_Simplifier_Pass


@dataclass
class Target:
    class TargetType(StrEnum):
        BINARY = auto()
        RAW = auto()

    module_id: str
    type: TargetType = TargetType.BINARY


@dataclass
class TreeNode:
    module: EHIR_Module
    dependencies: set[str] = field(default_factory=set)


@dataclass
class EHIR_ProjectCompiler:
    frontend: EHIR_Frontend
    backend: EHIR_Backend
    targets: dict[str, Target] = field(default_factory=dict)
    tree: dict[str, TreeNode] = field(default_factory=dict)

    def add_target_to_build(self, target: Target):
        if target.module_id in self.targets:
            return
        self.targets[target.module_id] = target

    def compile_all_targets(self) -> list[tuple[str, Path]]:
        result = []
        for target_name, target in self.targets.items():
            printfmt(f"[{target_name}] Compiling...\n", style=ThemePalette.ACCENT_TEXT)
            node = self._compile_node_by_id(target.module_id)

            node.module.ast = Resolver().run(node.module.ast)
            node.module.ast = Normalizer().run(node.module.ast)
            node.module.ast = Deallocator().run(node.module.ast)
            node.module.ast = Cfree_Simplifier_Pass().run(node.module.ast)
            node.module.ast = Downgrader().run(node.module.ast)
            processed_mod = Postprocessor().run(node.module)

            artifact_path = self.backend.compile_module(processed_mod)
            result.append((target_name, artifact_path))
        return result

    def _compile_node_by_id(self, id: str) -> TreeNode:
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

            parent_id = self.frontend.get_parent_id_of(id, derective)
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
