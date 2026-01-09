from ehir.core.derectives import Derective_struct
from ehir.core.derectives.base import Derective
from ehir.postprocessor.module import ProcessedModule
from ehir.simplifier.normalizer.norm_fn import Normalized_fn


class Postprocessor:
    def run(self, ast: list[Derective], mod_name: str) -> ProcessedModule:
        mod = ProcessedModule(name=mod_name, structs=[], funcs=[])
        for derective in ast:
            if isinstance(derective, Derective_struct):
                mod.structs.append(derective)
            elif isinstance(derective, Normalized_fn):
                mod.funcs.append(derective)
            else:
                raise NotImplementedError(f"Unknown derective: {derective}")
        return mod
