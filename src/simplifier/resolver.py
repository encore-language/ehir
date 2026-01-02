from src.core.derectives import Derective_fn
from src.core.derectives.base import Derective
from src.core.instructions.capture.cpos import Instruction_cpos
from src.core.instructions.control_flow.ret import Instruction_ret
from src.core.instructions.operators.arithmetic import Instruction_add
from src.core.variable import Variable


class Resolver:
    def run(self, ast: list[Derective]):
        for derective in ast:
            if isinstance(derective, Derective_fn):
                self._resolve(derective)

    def _resolve(self, fn: Derective_fn):
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
        for param in fn.params:
            add_variable(param)

        for block in fn.body:
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
                    expected_type = fn.ret_type
                    if instr.var.type and instr.var.type != expected_type:
                        raise TypeError(f"Type mismatch for return value: {instr.var.type} != {expected_type}")
                    instr.var.type = expected_type
                    instr.var = add_variable(instr.var)
                elif isinstance(instr, Instruction_add):
                    instr.var_out = add_variable(instr.var_out)
                    instr.lhs = add_variable(instr.lhs)
                    instr.rhs = add_variable(instr.rhs)

                else:
                    raise ValueError(f"Unexpected instruction: {instr}")

        # step 1: Check variables
        for name, val in variables.items():
            if val.type is None:
                raise TypeError(f"Type not specified for variable '{name}'")
