from src.core.derectives import Derective_fdecl, Derective_fdefi
from src.core.derectives.base import Derective
from src.core.instructions.capture.cpos import Instruction_cpos
from src.core.instructions.control_flow.ret import Instruction_ret
from src.core.variable import Variable


class Resolver:
    def resolve_ast(self, ast: list[Derective]):
        fdefis: dict[str, Derective_fdefi] = {}
        fdecls: dict[str, Derective_fdecl] = {}

        for derective in ast:
            if isinstance(derective, Derective_fdefi):
                assert derective.name not in fdefis, f"Duplicate function definition: {derective.name}"
                fdefis[derective.name] = derective
            elif isinstance(derective, Derective_fdecl):
                assert derective.name not in fdecls, f"Duplicate function declaration: {derective.name}"
                fdecls[derective.name] = derective

        assert set(fdefis.keys()) == set(fdecls.keys())

        for name in fdecls.keys():
            self._resolve(fdecls[name], fdefis[name])

    def _resolve(self, fdecl: Derective_fdecl, fdefi: Derective_fdefi):
        variables: dict[str, Variable] = {}

        def add_variable(var: Variable) -> Variable:
            if var.name not in variables:
                variables[var.name] = var
                return var

            old_var = variables[var.name]
            if old_var.type and var.type:
                if old_var.type != var.type:
                    raise TypeError(f"Type mismatch for variable '{var.name}': {old_var.type} != {var.type}")
                return old_var
            elif old_var.type:
                return old_var
            else:
                old_var.type = var.type
                return old_var

        # step 0: Collect all variables
        for param in fdecl.params:
            add_variable(param)

        for block in fdefi.body:
            for instr in block.body:
                if isinstance(instr, Instruction_cpos):
                    expected_type = instr.primitive.type
                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)
                elif isinstance(instr, Instruction_ret):
                    expected_type = fdecl.ret_type
                    if instr.var.type and instr.var.type != expected_type:
                        raise TypeError(f"Type mismatch for return value: {instr.var.type} != {expected_type}")
                    instr.var.type = expected_type
                    instr.var = add_variable(instr.var)
                else:
                    raise ValueError(f"Unexpected instruction: {instr}")

        # step 1: Check variables
        for name, val in variables.items():
            if val.type is None:
                raise TypeError(f"Type not specified for variable '{name}'")
