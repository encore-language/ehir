from copy import deepcopy
from dataclasses import fields, is_dataclass

from ehir.core.derectives import Derective_enum, Derective_fn, Derective_struct
from ehir.core.derectives.base import Derective
from ehir.core.enum import Enum
from ehir.core.instructions.base import Assignable
from ehir.core.instructions.capture import (
    Instruction_ceoh,
    Instruction_ceos,
    Instruction_cpoh,
    Instruction_csoh,
    Instruction_csos,
    Instruction_lceos,
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
    Instruction_halloc,
    Instruction_hfree,
    Instruction_pcast,
    Instruction_put,
    Instruction_sgetfield,
    Instruction_sgetfieldptr,
    Instruction_store,
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
from ehir.core.type import HeapSmartPointer, Pointer, StackSmartPointer, Type
from ehir.core.variable import Parameter, TypedVariable, Variable

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
    enums: dict[str, Derective_enum]
    structs: dict[str, Derective_struct]

    def run(self, ast: list[Derective]) -> list[Derective]:
        self.fn = {}
        self.enums = {}
        self.structs = {}

        for derective in ast:
            if isinstance(derective, Derective_fn):
                self.fn[derective.name] = derective
            elif isinstance(derective, Derective_enum):
                self.enums[derective.name] = derective
            elif isinstance(derective, Derective_struct):
                self.structs[derective.name] = derective

        base_fns = list(self.fn.values())
        for fn in base_fns:
            self._resolve(fn)

        # drop generics
        base_function_names = {x.name for x in base_fns}
        base_enum_names = {x.name for x in self.enums.values() if x.generics}
        base_struct_names = {x.name for x in self.structs.values() if x.generics}
        new_enums = [e for e in self.enums if e not in {x.name for x in ast if isinstance(x, Derective_enum)}]
        new_structs = [s for s in self.structs if s not in {x.name for x in ast if isinstance(x, Derective_struct)}]
        new_functions = [f for f in self.fn if f not in base_function_names]
        new_ast = []

        for derective in new_enums:
            new_ast.append(self.enums[derective])
        for derective in new_structs:
            new_ast.append(self.structs[derective])
        for derective in new_functions:
            new_ast.append(self.fn[derective])

        for derective in ast[::-1]:
            if isinstance(derective, Derective_enum) and derective.name in base_enum_names:
                continue
            if isinstance(derective, Derective_struct) and derective.name in base_struct_names:
                continue
            if isinstance(derective, Derective_fn) and derective.generics:
                continue
            new_ast.append(derective)

        return new_ast

    def _resolve(self, fn: Derective_fn):
        variables: dict[str, Variable] = {}

        def add_variable(var: Variable) -> Variable:
            if var.type is not None:
                var.type = self._resolve_type(var.type)

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
            if param.type is not None:
                param.type = self._resolve_type(param.type)
            add_variable(param)

        for block in fn.body:
            for instr in block.body:
                if isinstance(instr, Assignable) and instr.var_out.type is not None:
                    instr.var_out.type = self._resolve_type(instr.var_out.type)

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

                elif isinstance(instr, (Instruction_ceoh, Instruction_ceos)):
                    instr.enum = self._resolve_enum(instr.enum)
                    if isinstance(instr, Instruction_ceoh):
                        expected_type = Pointer(instr.enum.as_type())
                    else:
                        expected_type = Pointer(instr.enum.as_type())

                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)
                    self._resolve_enum_payload(instr.enum)
                    if instr.enum.payload is not None:
                        for arg in instr.enum.payload.args:
                            add_variable(arg)

                elif isinstance(instr, (Instruction_csos, Instruction_csoh, Instruction_scsos, Instruction_scsoh)):
                    instr.struct = self._resolve_struct(instr.struct)
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

                    struct_params = self._get_struct_params(instr.struct.name, instr.struct.generics)
                    for i, arg in enumerate(instr.struct.args):
                        expected_type = struct_params[i].type

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

                elif isinstance(instr, Instruction_lceos):
                    instr.enum = self._resolve_enum(instr.enum)
                    expected_type = instr.enum.as_type()

                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)
                    self._resolve_enum_payload(instr.enum)
                    if instr.enum.payload is not None:
                        for arg in instr.enum.payload.args:
                            add_variable(arg)

                elif isinstance(instr, Instruction_lcsos):
                    instr.struct = self._resolve_struct(instr.struct)
                    expected_type = instr.struct.as_type()

                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)
                    struct_params = self._get_struct_params(instr.struct.name, instr.struct.generics)
                    for i, arg in enumerate(instr.struct.args):
                        expected_type = struct_params[i].type

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
                    instr.src.type = self._resolve_type(instr.src.type)

                    if isinstance(instr.src.type, PrimitiveType):
                        raise TypeError(f"Cannot access field of primitive type '{instr.src.type}'")

                    resolved_params = self._get_composite_params(instr.src.type.name, instr.src.type.generics)
                    for i, param in enumerate(resolved_params):
                        if param.name == instr.field.name or str(i) == instr.field.name:
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
                    fn.ret_type = self._resolve_type(fn.ret_type)
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
                    instr.args = [add_variable(arg) for arg in instr.args]
                    target_fn = self.fn[instr.fn_name]
                    if target_fn.generics:
                        instr.generics = [self._resolve_type(generic) for generic in instr.generics]
                        concrete_name = target_fn.get_conrete_name(instr.generics)
                        if concrete_name not in self.fn:
                            target_fn = self._concrete_fn(target_fn, instr.generics)
                        instr.generics.clear()
                        instr.fn_name = concrete_name
                        target_fn = self.fn[concrete_name]
                    expected_type = target_fn.ret_type
                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)

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
                    instr.type = self._resolve_type(instr.type)
                    expected_type = Pointer(instr.type)
                    if instr.var_out.type and instr.var_out.type != expected_type:
                        raise TypeError(
                            f"Type mismatch for variable '{instr.var_out.name}': {instr.var_out.type} != {expected_type}"
                        )
                    instr.var_out.type = expected_type
                    instr.var_out = add_variable(instr.var_out)
                elif isinstance(instr, Instruction_halloc):
                    instr.type = self._resolve_type(instr.type)
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
                elif isinstance(instr, Instruction_store):
                    instr.var_src = add_variable(instr.var_src)
                    instr.var_dst = add_variable(instr.var_dst)
                    if instr.var_dst.type is not None:
                        assert isinstance(instr.var_dst.type, Pointer)
                        expected_type = instr.var_dst.type.pointee
                        if instr.var_src.type is not None and instr.var_src.type != expected_type:
                            raise TypeError(
                                f"Type mismatch for variable '{instr.var_src.name}': {instr.var_src.type} != {expected_type}"
                            )
                        instr.var_src.type = expected_type
                        instr.var_src = add_variable(instr.var_src)
                elif isinstance(instr, Instruction_hfree):
                    instr.var = add_variable(instr.var)
                elif isinstance(instr, Instruction_pcast):
                    instr.var = add_variable(instr.var)
                    instr.type = self._resolve_type(instr.type)

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

    def _concrete_fn(self, fn: Derective_fn, types: list[Type]) -> "Derective_fn":
        assert len(fn.generics) == len(types)
        generic_mapping = {a.name: b for a, b in zip(fn.generics, types)}

        base = deepcopy(fn)
        self._rewrite_types(base, generic_mapping)
        base.generics.clear()
        base.name = base.get_conrete_name(types)
        self.fn[base.name] = base
        self._resolve(base)

        return base

    def _concrete_struct(self, struct: Derective_struct, types: list[Type]) -> Derective_struct:
        assert len(struct.generics) == len(types)
        generic_mapping = {a.name: b for a, b in zip(struct.generics, types)}
        concrete_name = struct.get_conrete_name(types)
        if concrete_name in self.structs:
            return self.structs[concrete_name]

        base = deepcopy(struct)
        base.generics.clear()
        base.name = concrete_name
        self.structs[base.name] = base
        self._rewrite_types(base, generic_mapping)
        return base

    def _concrete_enum(self, enum: Derective_enum, types: list[Type]) -> Derective_enum:
        assert len(enum.generics) == len(types)
        generic_mapping = {a.name: b for a, b in zip(enum.generics, types)}
        concrete_name = enum.get_conrete_name(types)
        if concrete_name in self.enums:
            return self.enums[concrete_name]

        base = deepcopy(enum)
        base.generics.clear()
        base.name = concrete_name
        self.enums[base.name] = base
        self._rewrite_types(base, generic_mapping)
        return base

    def _resolve_struct(self, struct):
        self._rewrite_types(struct, {})
        target_struct = self.structs.get(struct.name)
        if target_struct is None or not target_struct.generics:
            return struct

        concrete_name = target_struct.get_conrete_name(struct.generics)
        if concrete_name not in self.structs:
            self._concrete_struct(target_struct, struct.generics)

        struct.name = concrete_name
        struct.generics.clear()
        return struct

    def _resolve_enum(self, enum: Enum) -> Enum:
        self._rewrite_types(enum, {})
        target_enum = self.enums.get(enum.name)
        if target_enum is None or not target_enum.generics:
            return enum

        concrete_name = target_enum.get_conrete_name(enum.generics)
        if concrete_name not in self.enums:
            self._concrete_enum(target_enum, enum.generics)

        enum.name = concrete_name
        enum.generics.clear()
        return enum

    def _get_struct_params(self, struct_name: str, generics: list[Type]):
        struct = self.structs[struct_name]
        if not struct.generics:
            return struct.params

        if len(struct.generics) != len(generics):
            return struct.params

        params = deepcopy(struct.params)
        self._rewrite_types(params, {a.name: b for a, b in zip(struct.generics, generics)})
        return params

    def _get_enum_variants(self, enum_name: str, generics: list[Type]):
        enum = self.enums[enum_name]
        if not enum.generics:
            return enum.variants

        variants = deepcopy(enum.variants)
        self._rewrite_types(variants, {a.name: b for a, b in zip(enum.generics, generics)})
        return variants

    def _get_composite_params(self, type_name: str, generics: list[Type]) -> list[Parameter]:
        if type_name in self.structs:
            return self._get_struct_params(type_name, generics)
        if type_name in self.enums:
            params: list[Parameter] = [Parameter(name="tag", type=Usize_t(8))]
            for variant in self._get_enum_variants(type_name, generics):
                assert variant.type is not None
                params.append(Parameter(name=variant.name, type=Pointer(variant.type)))
            return params
        raise TypeError(f"Unknown composite type '{type_name}'")

    def _resolve_enum_payload(self, enum: Enum):
        variants = self._get_enum_variants(enum.name, enum.generics)
        for variant_index, variant in enumerate(variants):
            if variant.name != enum.variant:
                continue

            if enum.payload is None:
                if variant.type is not None:
                    raise TypeError(f"Enum variant '{enum.variant}' expects payload")
                return

            enum.payload = self._resolve_struct(enum.payload)
            if variant.type is None:
                raise TypeError(f"Enum variant '{enum.variant}' must not have payload")
            if enum.payload.as_type() != variant.type:
                raise TypeError(
                    f"Type mismatch for enum variant '{enum.variant}': {enum.payload.as_type()} != {variant.type}"
                )

            struct_params = self._get_struct_params(enum.payload.name, enum.payload.generics)
            for i, arg in enumerate(enum.payload.args):
                expected_type = struct_params[i].type
                if arg.type is not None and arg.type != expected_type:
                    raise TypeError(
                        f"Type mismatch for argument {i} of struct '{enum.payload.name}': {arg.type} != {expected_type}"
                    )
                arg.type = expected_type
            return

        raise TypeError(f"Unknown enum variant '{enum.variant}' in '{enum.name}'")

    def _resolve_type(self, typ: Type) -> Type:
        return self._replace_type(typ, {})

    def _replace_type(self, typ: Type, generic_mapping: dict[str, Type]) -> Type:
        if isinstance(typ, HeapSmartPointer):
            return HeapSmartPointer(self._replace_type(typ.pointee, generic_mapping))
        if isinstance(typ, StackSmartPointer):
            return StackSmartPointer(self._replace_type(typ.pointee, generic_mapping))
        if isinstance(typ, Pointer):
            return Pointer(self._replace_type(typ.pointee, generic_mapping))

        if not typ.generics and typ.name in generic_mapping:
            return deepcopy(generic_mapping[typ.name])

        resolved = deepcopy(typ)
        resolved.generics = [self._replace_type(generic, generic_mapping) for generic in typ.generics]

        target_struct = self.structs.get(resolved.name)
        if (
            target_struct is not None
            and target_struct.generics
            and all(self._is_concrete_type(generic) for generic in resolved.generics)
        ):
            concrete_name = target_struct.get_conrete_name(resolved.generics)
            if concrete_name not in self.structs:
                self._concrete_struct(target_struct, resolved.generics)
            return Type(concrete_name)

        target_enum = self.enums.get(resolved.name)
        if (
            target_enum is not None
            and target_enum.generics
            and all(self._is_concrete_type(generic) for generic in resolved.generics)
        ):
            concrete_name = target_enum.get_conrete_name(resolved.generics)
            if concrete_name not in self.enums:
                self._concrete_enum(target_enum, resolved.generics)
            return Type(concrete_name)

        return resolved

    def _is_concrete_type(self, typ: Type) -> bool:
        if isinstance(typ, (HeapSmartPointer, StackSmartPointer, Pointer)):
            return self._is_concrete_type(typ.pointee)

        if isinstance(typ, PrimitiveType):
            return True

        if typ.generics and not all(self._is_concrete_type(generic) for generic in typ.generics):
            return False

        return (
            typ.name in self.structs
            or typ.name in self.enums
            or not typ.name.isidentifier()
            or typ.name.startswith("u")
        )

    def _rewrite_types(self, value, generic_mapping: dict[str, Type]):
        if isinstance(value, Type):
            return self._replace_type(value, generic_mapping)

        if isinstance(value, list):
            for i, item in enumerate(value):
                value[i] = self._rewrite_types(item, generic_mapping)
            return value

        if not is_dataclass(value):
            return value

        for field in fields(value):
            setattr(value, field.name, self._rewrite_types(getattr(value, field.name), generic_mapping))
        return value
