from ehir.core.derectives import Derective_fn, Derective_struct
from ehir.core.derectives.base import Derective
from ehir.core.instructions.capture import (
    Instruction_cpoh,
    Instruction_csoh,
    Instruction_csos,
    Instruction_lcpos,
    Instruction_lcsos,
    Instruction_scpoh,
    Instruction_scpos,
    Instruction_scsoh,
    Instruction_scsos,
)
from ehir.core.instructions.capture.cpos import Instruction_cpos
from ehir.core.instructions.control_flow import (
    Instruction_br,
    Instruction_call,
    Instruction_cbr,
    Instruction_phi,
    Instruction_ret,
    Instruction_switch,
)
from ehir.core.instructions.memory import (
    Instruction_getfield,
    Instruction_getfieldptr,
    Instruction_getptr,
    Instruction_hfree,
    Instruction_pcast,
    Instruction_put,
    Instruction_sgetfield,
    Instruction_sgetfieldptr,
)
from ehir.core.instructions.memory.load import Instruction_load
from ehir.core.instructions.memory.salloc import Instruction_salloc
from ehir.core.instructions.operators.base import BinOp
from ehir.core.instructions.operators.comparison import (
    Instruction_geq,
    Instruction_grt,
    Instruction_leq,
    Instruction_les,
)
from ehir.core.instructions.operators.logic import Instruction_and, Instruction_ieq, Instruction_neq, Instruction_or
from ehir.core.primitives import Usize_t
from ehir.core.primitives.base import PrimitiveType
from ehir.core.type import HeapSmartPointer, Pointer, StackSmartPointer
from ehir.core.variable import TypedVariable, Variable

_BOOLEAN_INSTRUCTS = (
    # Comparison
    Instruction_les,
    Instruction_grt,
    Instruction_leq,
    Instruction_geq,
    # Logic
    Instruction_and,
    Instruction_or,
    Instruction_ieq,  # todo:
    Instruction_neq,  # why it is logic?
)


class Resolver:
    fn: dict[str, Derective_fn]
    structs: dict[str, Derective_struct]

    def run(self, ast: list[Derective]):
        self.fn = {}
        self.structs = {}

        for derective in ast:
            if isinstance(derective, Derective_fn):
                self.fn[derective.name] = derective
            elif isinstance(derective, Derective_struct):
                self.structs[derective.name] = derective

        for fn in self.fn.values():
            self._resolve(fn)

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
                if isinstance(instr, (Instruction_cpos, Instruction_cpoh, Instruction_scpos, Instruction_scpoh)):
                    if isinstance(instr, (Instruction_cpos, Instruction_cpoh)):
                        pointer_t = Pointer
                    elif isinstance(instr, Instruction_scpos):
                        pointer_t = StackSmartPointer
                    else:
                        pointer_t = HeapSmartPointer
                    expected_type = pointer_t(instr.primitive.type)
                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)

                elif isinstance(instr, (Instruction_csos, Instruction_csoh, Instruction_scsos, Instruction_scsoh)):
                    if isinstance(instr, (Instruction_csos, Instruction_csoh)):
                        pointer_t = Pointer
                    elif isinstance(instr, Instruction_scsos):
                        pointer_t = StackSmartPointer
                    else:
                        pointer_t = HeapSmartPointer
                    expected_type = pointer_t(instr.struct.as_type())
                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)

                    for i, arg in enumerate(instr.struct.args):
                        expected_type = self.structs[instr.struct.name].params[i].type

                        if arg.type is not None and arg.type != expected_type:
                            raise TypeError(
                                f"Type mismatch for argument {i} of struct '{instr.struct.name}': {arg.type} != {expected_type}"
                            )
                        arg.type = expected_type
                        add_variable(arg)

                elif isinstance(instr, Instruction_lcpos):
                    expected_type = instr.primitive.type

                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)

                elif isinstance(instr, Instruction_lcsos):
                    expected_type = instr.struct.as_type()

                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)
                    for i, arg in enumerate(instr.struct.args):
                        expected_type = self.structs[instr.struct.name].params[i].type

                        if arg.type is not None and arg.type != expected_type:
                            raise TypeError(
                                f"Type mismatch for argument {i} of struct '{instr.struct.name}': {arg.type} != {expected_type}"
                            )
                        arg.type = expected_type
                        add_variable(arg)

                elif isinstance(
                    instr,
                    (Instruction_getfield, Instruction_getfieldptr, Instruction_sgetfield, Instruction_sgetfieldptr),
                ):
                    instr.src = add_variable(instr.src)
                    assert instr.src.type

                    if isinstance(instr.src.type, PrimitiveType):
                        raise TypeError(f"Cannot access field of primitive type '{instr.src.type}'")

                    if (corresponding_struct := self.structs.get(instr.src.type.name, None)) is None:
                        raise TypeError(f"Unknown struct '{instr.src.type.name}'")

                    for i, param in enumerate(corresponding_struct.params):
                        if param.name == instr.field.name:
                            if instr.field.type and instr.field.type != param.type:
                                raise TypeError(
                                    f"Type mismatch for field '{instr.field.name}' in struct '{instr.src.type.name}': {instr.field.type} != {param.type}"
                                )
                            instr.field.type = param.type
                            instr.field.name = str(i)
                            break
                    else:
                        raise TypeError(f"Unknown field '{instr.field.name}' in struct '{instr.src.type.name}'")

                    expected_type = (
                        instr.field.type
                        if isinstance(instr, (Instruction_getfield, Instruction_sgetfield))
                        else Pointer(instr.field.type)
                    )
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

                elif isinstance(instr, BinOp):
                    instr.lhs = add_variable(instr.lhs)
                    instr.rhs = add_variable(instr.rhs)

                    lhs_t = instr.lhs.type
                    rhs_t = instr.rhs.type
                    if lhs_t and rhs_t:
                        if lhs_t == rhs_t:
                            expected_t = Usize_t(size=1) if isinstance(instr, _BOOLEAN_INSTRUCTS) else lhs_t
                            if instr.var_out.type and instr.var_out.type != expected_t:
                                raise TypeError(f"Type mismatch for binop: {instr.var_out.type} != {expected_t}")
                            instr.var_out.type = expected_t

                    elif lhs_t is not None or rhs_t is not None:
                        expected_t = lhs_t if lhs_t is not None else rhs_t
                        assert expected_t is not None

                        instr.lhs = add_variable(TypedVariable(instr.lhs.name, expected_t))
                        instr.rhs = add_variable(TypedVariable(instr.rhs.name, expected_t))

                        if isinstance(instr, _BOOLEAN_INSTRUCTS):
                            expected_t = Usize_t(size=1)  # aka bool

                        if instr.var_out.type and instr.var_out.type != expected_t:
                            raise TypeError(f"Type mismatch for binop: {instr.var_out.type} != {expected_t}")
                        instr.var_out.type = expected_t

                    instr.var_out = add_variable(instr.var_out)

                elif isinstance(instr, Instruction_call):
                    target_fn = self.fn[instr.fn_name]
                    expected_type = target_fn.ret_type
                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)

                    instr.args = [add_variable(arg) for arg in instr.args]
                elif isinstance(instr, Instruction_phi):
                    if _t := instr.var_out.type:
                        expected_type = _t
                    else:
                        for arg in instr.args:
                            if _t := arg.var.type:
                                expected_type = _t
                                break
                        else:
                            raise TypeError(f"Unable to determine expected type for phi instruction: {instr}")

                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)

                    for arg in instr.args:
                        if arg.var.type and arg.var.type != expected_type:
                            raise TypeError(
                                f"Type mismatch for arg '{arg.var.name}': {arg.var.type} != {expected_type}"
                            )
                        arg.var.type = expected_type
                        arg.var = add_variable(arg.var)

                elif isinstance(instr, Instruction_br):
                    pass
                elif isinstance(instr, Instruction_cbr):
                    instr.cond_var = add_variable(instr.cond_var)
                elif isinstance(instr, Instruction_switch):
                    instr.cond_var = add_variable(instr.cond_var)
                elif isinstance(instr, Instruction_salloc):
                    expected_type = Pointer(instr.type)
                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)
                elif isinstance(instr, Instruction_put):
                    expected_type = Pointer(instr.primitive.type)
                    if instr.var.type and instr.var.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var.name}': {instr.var.type} != {expected_type}"
                        )
                    instr.var.type = expected_type
                    instr.var = add_variable(instr.var)
                elif isinstance(instr, Instruction_load):
                    instr.var = add_variable(instr.var)
                    if instr.var.type is not None:
                        if instr.var_out.type is not None and instr.var_out.type != Pointer(instr.var.type):
                            raise TypeError(
                                f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {Pointer(instr.var.type)}"
                            )
                        assert isinstance(instr.var.type, Pointer)
                        instr.var_out.type = instr.var.type.pointee
                    instr.var_out = add_variable(instr.var_out)
                elif isinstance(instr, Instruction_hfree):
                    instr.var = add_variable(instr.var)
                elif isinstance(instr, Instruction_pcast):
                    instr.var = add_variable(instr.var)

                    expected_type = instr.type
                    if instr.var_out.type is not None:
                        if instr.var_out.type != expected_type:
                            raise TypeError(
                                f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                            )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)

                elif isinstance(instr, Instruction_getptr):
                    instr.var = add_variable(instr.var)
                    if instr.var.type is not None:
                        expected_type = Pointer(instr.var.type)

                        if instr.var_out.type and instr.var.type != expected_type:
                            raise TypeError(
                                f"Type mismatch for variable '{instr.var.name}': {instr.var.type} != {expected_type}"
                            )
                        instr.var_out.type = expected_type

                    instr.var_out = add_variable(instr.var_out)
                else:
                    raise ValueError(f"Unexpected instruction: {instr}")

        # step 1: Check variables
        for name, val in variables.items():
            if val.type is None:
                raise TypeError(f"Type not specified for variable '{name}'")
