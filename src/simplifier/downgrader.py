from src.core.block import TerminatedBlock
from src.core.derectives import Derective_struct
from src.core.derectives.base import Derective
from src.core.instructions.base import Instruction
from src.core.instructions.capture import (
    Instruction_cpoh,
    Instruction_cpos,
    Instruction_csoh,
    Instruction_csos,
    Instruction_lcpos,
    Instruction_lcsos,
    Instruction_scpoh,
    Instruction_scpos,
    Instruction_scsoh,
    Instruction_scsos,
)
from src.core.instructions.control_flow.base import ControlFlow
from src.core.instructions.control_flow.br import Instruction_br
from src.core.instructions.control_flow.cbr import Instruction_cbr
from src.core.instructions.control_flow.ret import Instruction_ret
from src.core.instructions.control_flow.switch import Instruction_switch
from src.core.instructions.memory import (
    Instruction_getfield,
    Instruction_getfieldptr,
    Instruction_getptr,
    Instruction_hfree,
    Instruction_pcast,
    Instruction_put,
    Instruction_store,
)
from src.core.instructions.memory.halloc import Instruction_halloc
from src.core.instructions.memory.load import Instruction_load
from src.core.instructions.memory.salloc import Instruction_salloc
from src.core.instructions.operators.arithmetic import (
    Instruction_add,
    Instruction_div,
    Instruction_mul,
    Instruction_sub,
)
from src.core.instructions.operators.logic import Instruction_and, Instruction_ieq, Instruction_neq, Instruction_or
from src.core.instructions.special import Instruction_cfree, Instruction_comment
from src.core.instructions.special.call import Instruction_call
from src.core.primitives import Usize, Usize_t
from src.core.struct import Struct
from src.core.type import Pointer, SmartPointer, Type
from src.core.variable import TypedVariable
from src.simplifier.normalizer.norm_fn import Normalized_fn

SKIPABLE = (
    Instruction_ret,
    Instruction_add,
    Instruction_sub,
    Instruction_mul,
    Instruction_div,
    Instruction_and,
    Instruction_or,
    Instruction_ieq,
    Instruction_neq,
    Instruction_store,
    Instruction_call,
    Instruction_switch,
    Instruction_salloc,
    Instruction_load,
    Instruction_put,
    Instruction_hfree,
    Instruction_getfieldptr,
    Instruction_pcast,
    Instruction_getptr,
    Instruction_comment,
    Instruction_halloc,
)

ENABLE_COMMENTS: bool = True


class Downgrader:
    _structs: dict[str, Derective_struct]
    _structs_to_add: list[Derective_struct]
    _fns: dict[str, Normalized_fn]
    _fns_to_add: list[Normalized_fn]

    def run(self, ast: list[Derective]):
        self._structs = {}
        self._structs_to_add = []
        self._fns = {}
        self._fns_to_add = []

        for derective in ast:
            if isinstance(derective, Derective_struct):
                self._structs[derective.name] = derective

        for derective in ast:
            if isinstance(derective, Normalized_fn):
                self._fns[derective.name] = derective

        for derective in ast:
            if isinstance(derective, Normalized_fn):
                self._downgrade_function(derective)

        # Add new structs
        ast.extend(self._structs_to_add)
        ast.extend(self._fns_to_add)

    def _downgrade_function(self, fn: Normalized_fn):
        for block in fn.get_body():
            assert isinstance(block, TerminatedBlock)
            new_body = []
            for instr in block.get_body():
                new = self._downgrade(instr)
                if not isinstance(instr, ControlFlow):
                    new_body.extend(new)
                else:
                    term = new.pop()
                    assert isinstance(term, ControlFlow)
                    new_body.extend(new)
                    block.term = term

            block.body = new_body

    def _downgrade(self, instr: Instruction) -> list[Instruction]:
        if isinstance(instr, Instruction_cpos):
            return self._downgrade_cpos(instr)
        elif isinstance(instr, Instruction_cpoh):
            return self._downgrade_cpoh(instr)
        elif isinstance(instr, Instruction_csos):
            return self._downgrade_csos(instr)
        elif isinstance(instr, Instruction_csoh):
            return self._downgrade_csoh(instr)
        elif isinstance(instr, Instruction_scpos):
            return self._downgrade_scpos(instr)
        elif isinstance(instr, Instruction_scpoh):
            return self._downgrade_scpoh(instr)
        elif isinstance(instr, Instruction_scsos):
            return self._downgrade_scsos(instr)
        elif isinstance(instr, Instruction_scsoh):
            return self._downgrade_scsoh(instr)
        elif isinstance(instr, Instruction_lcpos):
            return self._downgrade_lcpos(instr)
        elif isinstance(instr, Instruction_lcsos):
            return self._downgrade_lcsos(instr)
        elif isinstance(instr, Instruction_getfield):
            return self._downgrade_getfield(instr)
        elif isinstance(instr, Instruction_cbr):
            return self._downgrade_cbr(instr)
        elif isinstance(instr, Instruction_br):
            return self._downgrade_br(instr)
        elif isinstance(instr, Instruction_cfree):
            return self._downgrade_cfree(instr)
        elif isinstance(instr, SKIPABLE):
            return [instr]
        else:
            raise NotImplementedError(f"Downgrading instruction for {type(instr)}:{instr} not implemented")

    def _downgrade_cfree(self, instr: Instruction_cfree) -> list[Instruction]:
        assert instr.var.type
        fn_call = self._generate_cfree(instr.var.type)
        var_out = TypedVariable(name=".cfree_out", type=fn_call.ret_type)
        var_ini = TypedVariable(name=".cfree_ini", type=Usize_t())
        return [
            *self._downgrade_lcpos(Instruction_lcpos(var_out=var_ini, primitive=Usize(0))),
            Instruction_call(var_out=var_out, fn_name=fn_call.name, args=[instr.var, var_ini]),
        ]

    def _downgrade_cpos(self, instr: Instruction_cpos) -> list[Instruction]:
        assert instr.var_out.type is not None
        assert isinstance(instr.var_out.type, Pointer)

        salloc = Instruction_salloc(
            var_out=instr.var_out,
            type=instr.var_out.type.pointee,
        )
        put = Instruction_put(
            primitive=instr.primitive,
            var=instr.var_out,
        )
        return [
            salloc,
            put,
        ]

    def _downgrade_cpoh(self, instr: Instruction_cpoh) -> list[Instruction]:
        assert instr.var_out.type is not None
        assert isinstance(instr.var_out.type, Pointer)

        halloc = Instruction_halloc(
            var_out=instr.var_out,
            type=instr.var_out.type.pointee,
        )
        put = Instruction_put(
            primitive=instr.primitive,
            var=instr.var_out,
        )
        return [
            halloc,
            put,
        ]

    def _downgrade_csos(self, instr: Instruction_csos) -> list[Instruction]:
        assert instr.var_out.type is not None
        assert isinstance(instr.var_out.type, Pointer)

        salloc = Instruction_salloc(
            var_out=instr.var_out,
            type=instr.struct.as_type(),
        )
        downgrades = [salloc]
        for i, arg in enumerate(instr.struct.args):
            field_arg = TypedVariable(name=f".{instr.var_out.name}.{arg.name}", type=Pointer(arg.type))
            field_ptr = Instruction_getfieldptr(
                var_out=field_arg, src=instr.var_out, indexes=[TypedVariable(name=str(i), type=arg.type)]
            )

            store = Instruction_store(
                var_src=arg,
                var_dst=field_arg,
            )
            downgrades.append(field_ptr)
            downgrades.append(store)

        return downgrades

    def _downgrade_csoh(self, instr: Instruction_csoh) -> list[Instruction]:
        assert instr.var_out.type is not None
        assert isinstance(instr.var_out.type, Pointer)

        halloc = Instruction_halloc(
            var_out=instr.var_out,
            type=instr.struct.as_type(),
        )
        downgrades = [halloc]
        for i, arg in enumerate(instr.struct.args):
            field_arg = TypedVariable(name=f".{instr.var_out.name}.{arg.name}", type=Pointer(arg.type))
            field_ptr = Instruction_getfieldptr(
                var_out=field_arg, src=instr.var_out, indexes=[TypedVariable(name=str(i), type=arg.type)]
            )

            store = Instruction_store(
                var_src=arg,
                var_dst=field_arg,
            )
            downgrades.append(field_ptr)
            downgrades.append(store)

        return downgrades

    def _downgrade_scpos(self, instr: Instruction_scpos) -> list[Instruction]:
        raise NotImplementedError

    def _downgrade_scpoh(self, instr: Instruction_scpoh) -> list[Instruction]:
        raise NotImplementedError

    def _downgrade_scsos(self, instr: Instruction_scsos) -> list[Instruction]:
        raise NotImplementedError

    def _downgrade_scsoh(self, instr: Instruction_scsoh) -> list[Instruction]:
        assert instr.var_out.type is not None

        struct_name = f"{instr.struct.name}_SHP"
        if struct_name not in self._structs:
            self._structs[struct_name] = Derective_struct(
                name=struct_name,
                params=[
                    TypedVariable(name="ptr", type=Pointer(instr.struct.as_type())),
                    TypedVariable(name="ref_cnt", type=Usize_t()),
                    TypedVariable(name="in_reachable", type=Usize_t(1)),
                    TypedVariable(name="out_reachable", type=Usize_t(1)),
                    TypedVariable(name="out_visited", type=Usize_t(1)),
                    TypedVariable(name="deallocate", type=Usize_t(1)),
                ],
            )
            self._structs_to_add.append(self._structs[struct_name])

        ptr = TypedVariable(name=f".{instr.var_out.name}_wrapped_ptr", type=Pointer(instr.struct.as_type()))
        ref_cnt = TypedVariable(name=f".{instr.var_out.name}_ref_cnt", type=Usize_t())
        in_reachable = TypedVariable(name=f".{instr.var_out.name}_in_reachable", type=Usize_t(1))
        out_reachable = TypedVariable(name=f".{instr.var_out.name}_out_reachable", type=Usize_t(1))
        out_visited = TypedVariable(name=f".{instr.var_out.name}_out_visited", type=Usize_t(1))
        deallocate = TypedVariable(name=f".{instr.var_out.name}_deallocate", type=Usize_t(1))

        ptr_init = Instruction_csoh(ptr, instr.struct)
        ref_cnt_init = Instruction_lcpos(ref_cnt, Usize(val=1))
        in_reachable_init = Instruction_lcpos(in_reachable, Usize(val=1, size=1))
        out_reachable_init = Instruction_lcpos(out_reachable, Usize(val=0, size=1))
        out_visited_init = Instruction_lcpos(out_visited, Usize(val=0, size=1))
        deallocate_init = Instruction_lcpos(deallocate, Usize(val=0, size=1))

        s = Struct(name=struct_name, args=[ptr])
        instr.var_out.type = s.as_type()
        res = Instruction_lcsos(instr.var_out, s)

        return [
            *self._downgrade_csoh(ptr_init),
            *self._downgrade_lcpos(ref_cnt_init),
            *self._downgrade_lcpos(in_reachable_init),
            *self._downgrade_lcpos(out_reachable_init),
            *self._downgrade_lcpos(out_visited_init),
            *self._downgrade_lcpos(deallocate_init),
            *self._downgrade_lcsos(res),
        ]

    def _downgrade_lcpos(self, instr: Instruction_lcpos) -> list[Instruction]:
        assert instr.var_out.type is not None
        out_ptr = TypedVariable(name=f".{instr.var_out.name}_ptr", type=Pointer(instr.var_out.type))
        cpos = Instruction_cpos(
            var_out=out_ptr,
            primitive=instr.primitive,
        )
        load = Instruction_load(var_out=instr.var_out, var=out_ptr)
        return [
            *self._downgrade_cpos(cpos),
            load,
        ]

    def _downgrade_lcsos(self, instr: Instruction_lcsos) -> list[Instruction]:
        assert instr.var_out.type is not None
        out_ptr = TypedVariable(name=f".{instr.var_out.name}_ptr", type=Pointer(instr.var_out.type))
        csos = Instruction_csos(var_out=out_ptr, struct=instr.struct)
        load = Instruction_load(var_out=instr.var_out, var=out_ptr)
        return [
            *self._downgrade_csos(csos),
            load,
        ]

    def _downgrade_getfield(self, instr: Instruction_getfield) -> list[Instruction]:
        assert instr.var_out.type is not None
        out_ptr = TypedVariable(name=f".{instr.var_out.name}_ptr", type=Pointer(instr.var_out.type))
        getfieldptr = Instruction_getfieldptr(var_out=out_ptr, src=instr.src, indexes=instr.indexes)
        load = Instruction_load(var_out=instr.var_out, var=out_ptr)
        return [
            getfieldptr,
            load,
        ]

    def _downgrade_cbr(self, instr: Instruction_cbr) -> list[Instruction]:
        assert instr.cond_var.type is not None
        assert isinstance(instr.cond_var.type, Usize_t)

        switch = Instruction_switch(
            cond_var=instr.cond_var,
            default_case=instr.else_br_label,
            cases=[(Usize(1, size=instr.cond_var.type.size), instr.true_br_label)],
        )
        return [switch]

    def _downgrade_br(self, instr: Instruction_br) -> list[Instruction]:
        zero_ptr = TypedVariable(name=".br_zero_ptr", type=Pointer(Usize_t(1)))
        zero = TypedVariable(name=".br_zero", type=Usize_t(1))
        cpos = Instruction_cpos(var_out=zero_ptr, primitive=Usize(0, size=1))
        load = Instruction_load(
            var_out=zero,
            var=zero_ptr,
        )
        switch = Instruction_switch(
            cond_var=zero,
            default_case=instr.label,
            cases=[],
        )
        return [*self._downgrade_cpos(cpos), load, switch]

    def _generate_cfree(self, typ: Type) -> Normalized_fn:
        name = f"cfree_{typ.name}"
        if name in self._fns:
            return self._fns[name]

        self_param = TypedVariable(name="self", type=typ)
        mode_param = TypedVariable(name="mode", type=Usize_t())

        var_0 = TypedVariable("zero", Usize_t())
        var_1 = TypedVariable("one", Usize_t())
        var_2 = TypedVariable("two", Usize_t())
        var_3 = TypedVariable("tree", Usize_t())

        exit_var = TypedVariable(name="ok", type=Usize_t())
        exit_block = TerminatedBlock(
            name="exit",
            body=[
                Instruction_lcpos(var_out=exit_var, primitive=Usize(0)),
            ],
            term=Instruction_ret(var=exit_var),
        )

        unk_var = TypedVariable(name="unk", type=Usize_t())
        unknown_block = TerminatedBlock(
            name="unknown",
            body=[
                Instruction_lcpos(var_out=unk_var, primitive=Usize(1)),
            ],
            term=Instruction_ret(var=unk_var),
        )

        struct = self._structs[typ.name]
        struct_wrapped = self._structs[struct.params[0].type.name]
        # ============
        # Pass 1
        # ============
        in_reachable_ptr = TypedVariable(
            name="in_reachable_field_ptr",
            type=Pointer(struct.params[2].type),
        )
        in_reachable_var = TypedVariable(
            name="in_reachable_field",
            type=struct.params[2].type,
        )

        pass_1_block = TerminatedBlock(
            name="pass_1",
            body=[
                Instruction_getfieldptr(
                    in_reachable_ptr,
                    self_param,
                    indexes=[TypedVariable(name="2", type=Usize_t(1))],
                ),
                Instruction_load(
                    var_out=in_reachable_var,
                    var=in_reachable_ptr,
                ),
            ],
            term=Instruction_cbr(cond_var=in_reachable_var, true_br_label=exit_block.name, else_br_label="pass_1v1"),
        )
        pass_1v1_block = TerminatedBlock(
            name="pass_1v1",
            body=[Instruction_put(primitive=Usize(val=1, size=1), var=in_reachable_ptr)],
            term=Instruction_br(exit_block.name),
        )

        for i, field in enumerate(struct_wrapped.params):
            if isinstance(field.type, SmartPointer):
                ref_cnt_ptr = TypedVariable(
                    name=f".{field.name}_ref_cnt_ptr", type=Pointer(struct_wrapped.params[i].type)
                )
                ref_cnt = TypedVariable(name=f".{field.name}_ref_cnt", type=struct_wrapped.params[i].type)

                pass_1v1_block.body.append(Instruction_load(var_out=ref_cnt, var=ref_cnt_ptr))

                ref_cnt_new = TypedVariable(name=f".{field.name}_ref_cnt_new", type=struct_wrapped.params[i].type)
                ref_cnt_new_ptr = TypedVariable(
                    name=f".{field.name}_ref_cnt_new_ptr", type=Pointer(struct_wrapped.params[i].type)
                )
                pass_1v1_block.body.extend(
                    [
                        Instruction_sub(var_out=ref_cnt_new, lhs=ref_cnt, rhs=var_1),
                        Instruction_getptr(var_out=ref_cnt_new_ptr, var=ref_cnt_new),
                        Instruction_store(var_src=ref_cnt_new_ptr, var_dst=ref_cnt_ptr),
                        Instruction_call(
                            var_out=TypedVariable(name=f".pass1_{field}", type=Usize_t()),
                            fn_name=f"cfree_{struct_wrapped.params[i].type.name}",
                            args=[self_param, var_1],
                        ),
                    ]
                )

        # ============
        # Pass 2
        # ============
        out_reachable_ptr = TypedVariable(
            name="out_reachable_field_ptr",
            type=Pointer(struct.params[2].type),
        )
        out_reachable_var = TypedVariable(
            name="out_reachable_field",
            type=struct.params[2].type,
        )
        pass_2_block = TerminatedBlock(
            name="pass_2",
            body=[
                Instruction_getfieldptr(
                    out_reachable_ptr,
                    self_param,
                    indexes=[TypedVariable(name="3", type=Usize_t(1))],
                ),
                Instruction_load(
                    var_out=out_reachable_var,
                    var=out_reachable_ptr,
                ),
            ],
            term=Instruction_cbr(cond_var=in_reachable_var, true_br_label=exit_block.name, else_br_label="pass_2v1"),
        )

        out_reachable_2_ptr = TypedVariable(name=".pass_2_out_reachable_ptr", type=Pointer(Usize_t(1)))
        out_reachable_2 = TypedVariable(name=".pass_2_out_reachable", type=Usize_t(1))
        out_visited_2_ptr = TypedVariable(name=".pass_2_out_visited_ptr", type=Pointer(Usize_t(1)))
        out_visited_2 = TypedVariable(name=".pass_2_out_visited", type=Usize_t(1))
        # out_reachable_new_ptr = TypedVariable(name=".pass_2_out_reachable_new_ptr", type=Pointer(Usize_t(1)))
        out_reachable_new = TypedVariable(name=".pass_2_out_reachable_new", type=Usize_t(1))
        ref_cnt = TypedVariable(name=".pass_2_ref_cnt", type=Usize_t())
        ref_cnt_not_zero = TypedVariable(name=".pass_2_ref_cnt_not_zero", type=Usize_t(1))
        pass_2v1_block = TerminatedBlock(
            name="pass_2v1",
            body=[
                Instruction_getfieldptr(
                    var_out=out_reachable_2_ptr,
                    src=self_param,
                    indexes=[TypedVariable(name="3", type=Usize_t(1))],
                ),
                Instruction_load(
                    var_out=out_reachable_2,
                    var=out_reachable_2_ptr,
                ),
                Instruction_getfieldptr(
                    var_out=out_visited_2_ptr,
                    src=self_param,
                    indexes=[TypedVariable(name="4", type=Usize_t(1))],
                ),
                Instruction_load(
                    var_out=out_visited_2,
                    var=out_visited_2_ptr,
                ),
                Instruction_getfield(
                    var_out=ref_cnt, src=self_param, indexes=[TypedVariable(name="1", type=Usize_t())]
                ),
                Instruction_neq(
                    var_out=ref_cnt_not_zero,
                    lhs=ref_cnt,
                    rhs=var_0,
                ),
                Instruction_or(
                    var_out=out_reachable_new,
                    lhs=out_reachable_2,
                    rhs=ref_cnt_not_zero,
                ),
                Instruction_store(
                    var_src=out_reachable_new,
                    var_dst=out_reachable_2_ptr,
                ),
                Instruction_put(
                    primitive=Usize(val=1, size=1),
                    var=out_visited_2_ptr,
                ),
            ],
            term=Instruction_cbr(cond_var=out_reachable_new, true_br_label="pass_2v2", else_br_label="pass_2v3"),
        )

        pass_2v2_block = TerminatedBlock(
            name="pass_2v2",
            body=[],
            term=Instruction_br("pass_2v3"),
        )
        for i, field in enumerate(struct_wrapped.params):
            if isinstance(field.type, SmartPointer):
                pass_2v2_block.body.append(Instruction_comment("Not implemented logic"))

        pass_2v3_block = TerminatedBlock(
            name="pass_2v3",
            body=[],
            term=Instruction_br(exit_block.name),
        )
        for i, field in enumerate(struct_wrapped.params):
            if isinstance(field.type, SmartPointer):
                pass_2v2_block.body.append(
                    Instruction_call(
                        var_out=TypedVariable(name=f".pass2_{field}", type=Usize_t()),
                        fn_name=f"cfree_{struct_wrapped.params[i].type.name}",
                        args=[self_param, var_2],
                    ),
                )

        # ============
        # Pass 3
        # ============
        deallocate_3_ptr = TypedVariable(name=".pass_3_deallocate_ptr", type=Pointer(Usize_t(1)))
        deallocate_3 = TypedVariable(name=".pass_3_deallocate", type=Usize_t(1))
        pass_3_block = TerminatedBlock(
            name="pass_3",
            body=[
                Instruction_getfieldptr(
                    var_out=deallocate_3_ptr,
                    src=self_param,
                    indexes=[TypedVariable(name="5", type=Usize_t(1))],
                ),
                Instruction_load(
                    var_out=deallocate_3,
                    var=deallocate_3_ptr,
                ),
            ],
            term=Instruction_cbr(cond_var=deallocate_3, true_br_label=exit_block.name, else_br_label="pass_3v1"),
        )

        cond2 = TypedVariable(name=".pass_3_cond2", type=Usize_t(1))
        pass_3v1_block = TerminatedBlock(
            name="pass_3v1",
            body=[
                Instruction_put(primitive=Usize(val=1, size=1), var=deallocate_3_ptr),
            ],
            term=Instruction_cbr(cond_var=cond2, true_br_label="pass_3v2", else_br_label=exit_block.name),
        )
        for i, field in enumerate(struct_wrapped.params):
            if isinstance(field.type, SmartPointer):
                pass_3v1_block.body.append(
                    Instruction_call(
                        var_out=TypedVariable(name=f".pass3_{field}", type=Usize_t()),
                        fn_name=f"cfree_{struct_wrapped.params[i].type.name}",
                        args=[self_param, var_3],
                    ),
                )
        ref_cnt = TypedVariable(name=".pass_3_ref_cnt", type=Usize_t())
        pass_3v1_block.body.append(
            Instruction_getfield(
                var_out=ref_cnt,
                src=self_param,
                indexes=[TypedVariable(name="1", type=Usize_t())],
            )
        )
        ref_cnt_is_zero = TypedVariable(name=".pass_3_ref_cnt_is_zero", type=Usize_t(1))
        zero_1_bit = TypedVariable(".pass_3_zero_1_bit", type=Usize_t(1))
        one_1_bit = TypedVariable(".pass_3_one_1_bit", type=Usize_t(1))
        pass_3v1_block.body.extend(
            [
                Instruction_pcast(var_out=zero_1_bit, var=var_0, type=Usize_t(1)),
                Instruction_pcast(var_out=one_1_bit, var=var_1, type=Usize_t(1)),
                Instruction_ieq(var_out=ref_cnt_is_zero, lhs=ref_cnt, rhs=var_0),
            ]
        )

        inner_reach = TypedVariable(name=".pass_3_inner_reach", type=Usize_t(1))
        pass_3v1_block.body.append(
            Instruction_getfield(
                var_out=inner_reach,
                src=self_param,
                indexes=[TypedVariable(name="2", type=Usize_t(1))],
            )
        )
        outer_reach = TypedVariable(name=".pass_3_outer_reach", type=Usize_t(1))
        pass_3v1_block.body.append(
            Instruction_getfield(
                var_out=outer_reach,
                src=self_param,
                indexes=[TypedVariable(name="3", type=Usize_t(1))],
            )
        )
        inner_reach_is_one = TypedVariable(name=".pass_3_inner_reach_is_one", type=Usize_t(1))
        pass_3v1_block.body.append(Instruction_ieq(var_out=inner_reach_is_one, lhs=inner_reach, rhs=one_1_bit))

        outer_reach_is_zero = TypedVariable(name=".pass_3_outer_reach_is_zero", type=Usize_t(1))
        pass_3v1_block.body.append(Instruction_ieq(var_out=outer_reach_is_zero, lhs=outer_reach, rhs=zero_1_bit))

        cond1 = TypedVariable(name=".pass_3_cond1", type=Usize_t(1))
        pass_3v1_block.body.append(Instruction_and(var_out=cond1, lhs=ref_cnt_is_zero, rhs=inner_reach_is_one))

        pass_3v1_block.body.append(Instruction_and(var_out=cond2, lhs=cond1, rhs=outer_reach_is_zero))

        wrap_struct_ptr = TypedVariable(name=".pass3_wrapped_struct_ptr", type=struct.params[0].type)
        pass_3v2_block = TerminatedBlock(
            name="pass_3v2",
            body=[
                Instruction_getfield(
                    var_out=wrap_struct_ptr,
                    src=self_param,
                    indexes=[TypedVariable(name="0", type=struct.params[0].type)],
                ),
                Instruction_hfree(var=wrap_struct_ptr),
            ],
            term=Instruction_br(label=exit_block.name),
        )

        initiator_block = TerminatedBlock(
            name="initiator",
            body=[
                Instruction_lcpos(var_out=var_0, primitive=Usize(0)),
                Instruction_lcpos(var_out=var_1, primitive=Usize(1)),
                Instruction_lcpos(var_out=var_2, primitive=Usize(2)),
                Instruction_lcpos(var_out=var_3, primitive=Usize(3)),
                Instruction_call(
                    var_out=TypedVariable(name=".pass_1", type=Usize_t()), fn_name=name, args=[self_param, var_1]
                ),
                Instruction_call(
                    var_out=TypedVariable(name=".pass_2", type=Usize_t()), fn_name=name, args=[self_param, var_2]
                ),
                Instruction_call(
                    var_out=TypedVariable(name=".pass_3", type=Usize_t()), fn_name=name, args=[self_param, var_3]
                ),
            ],
            term=Instruction_br(label=exit_block.name),
        )
        entry_block = TerminatedBlock(
            name="entry",
            body=[],
            term=Instruction_switch(
                cond_var=mode_param,
                default_case="unknown",
                cases=[
                    (Usize(0), initiator_block.name),
                    (Usize(1), pass_1_block.name),
                    (Usize(2), pass_2_block.name),
                    (Usize(3), pass_3_block.name),
                ],
            ),
        )

        derective = Normalized_fn(
            name=name,
            params=[self_param, mode_param],
            ret_type=Usize_t(),
            entry_block=entry_block,
            body=[
                initiator_block,
                pass_1_block,
                pass_1v1_block,
                pass_2_block,
                pass_2v1_block,
                pass_2v2_block,
                pass_2v3_block,
                pass_3_block,
                pass_3v1_block,
                pass_3v2_block,
                unknown_block,
            ],
            exit_block=exit_block,
        )
        self._downgrade_function(derective)
        self._fns[name] = derective
        self._fns_to_add.append(derective)
        return derective
