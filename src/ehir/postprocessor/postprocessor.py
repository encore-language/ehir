from ehir.builder import EHIR_Module
from ehir.core.derectives import Derective_struct
from ehir.postprocessor.module import ProcessedModule
from ehir.simplifier.normalizer.norm_fn import Normalized_fn


class Postprocessor:
    def run(self, raw_mod: EHIR_Module) -> ProcessedModule:
        mod = ProcessedModule(id=raw_mod.id, structs=[], funcs=[])
        for derective in raw_mod.ast:
            if isinstance(derective, Derective_struct):
                mod.structs.append(derective)
            elif isinstance(derective, Normalized_fn):
                mod.funcs.append(derective)
            else:
                raise NotImplementedError(f"Unknown derective: {derective}")
        return mod
