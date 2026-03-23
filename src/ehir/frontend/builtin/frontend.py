from pathlib import Path

from ehir.builder import EHIR_Module
from ehir.core.derectives import Derective_import
from ehir.frontend import EHIR_Frontend
from ehir.frontend.builtin.parser import Parser


class EHIR_DirectFrontend(EHIR_Frontend):
    """
    Module id is relative path to module
    """

    _cache: dict[str, EHIR_Module]

    def __init__(self):
        self._cache = {}

    def get_module_by_id(self, id: str) -> EHIR_Module:
        if id in self._cache:
            return self._cache[id]

        parser = Parser()

        with Path(id).resolve().open("r") as f:
            ast = parser.parse(f.read())

        mod = EHIR_Module(id, ast)
        self._cache[id] = mod
        return mod

    def get_parent_id_of(self, id: str, derective: Derective_import) -> str | None:
        child_path = Path(id).resolve()
        target_id = child_path.parent / Path(*derective.prefix)

        if target_id.is_dir():
            target_id /= "mod.ehir"
            return target_id.__str__() if target_id.exists() else None

        target_id_file = target_id.with_suffix(".ehir")
        if target_id_file.exists():
            return target_id_file.__str__()
