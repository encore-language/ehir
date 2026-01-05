from src.core.derectives import Derective_fn, Derective_struct
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
from src.core.instructions.special import Instruction_comment
from src.core.instructions.special.call import Instruction_call
from src.core.primitives import Usize, Usize_t
from src.core.struct import Struct
from src.core.type import Pointer
from src.core.variable import TypedVariable

SKIPABLE = (
    Instruction_ret,
    Instruction_add,
    Instruction_sub,
    Instruction_mul,
    Instruction_div,
    Instruction_call,
    Instruction_switch,
    Instruction_salloc,
    Instruction_load,
    Instruction_put,
    Instruction_hfree,
    Instruction_getfieldptr,
    Instruction_pcast,
    Instruction_getptr,
)


class Downgrader:
    _structs: dict[str, Derective_struct]
    _structs_to_add: list[Derective_struct]

    def run(self, ast: list[Derective]):
        self._structs = {}
        self._structs_to_add = []
        for derective in ast:
            if isinstance(derective, Derective_struct):
                self._structs[derective.name] = derective

        for derective in ast:
            if isinstance(derective, Derective_fn):
                self._downgrade_function(derective)

        # Add new structs
        ast.extend(self._structs_to_add)

    def _downgrade_function(self, fn: Derective_fn):
        for block in fn.body:
            new_body = []
            for instr in block.body:
                new_body.extend(self._downgrade(instr))
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
        elif isinstance(instr, SKIPABLE):
            return [instr]
        else:
            raise NotImplementedError(f"Downgrading instruction for {type(instr)}:{instr} not implemented")

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
            Instruction_comment(""),
            Instruction_comment(f"{instr}"),
            Instruction_comment(""),
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
            Instruction_comment(""),
            Instruction_comment(f"{instr}"),
            Instruction_comment(""),
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

        return [
            Instruction_comment(""),
            Instruction_comment(f"{instr}"),
            Instruction_comment(""),
        ] + downgrades

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

        return [
            Instruction_comment(""),
            Instruction_comment(f"{instr}"),
            Instruction_comment(""),
        ] + downgrades

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
                    # TypedVariable(name="ref_cnt", type=Usize_t()),
                    # TypedVariable(name="num_in_reach", type=Usize_t(1)),
                    # TypedVariable(name="num_out_reach", type=Usize_t(1)),
                    # TypedVariable(name="out_visited", type=Usize_t(1)),
                ],
            )
            self._structs_to_add.append(self._structs[struct_name])

        ptr = TypedVariable(name=f".{instr.var_out.name}_wrapped_ptr", type=Pointer(instr.struct.as_type()))
        # ref_cnt = TypedVariable(name=f".{instr.var_out.name}_ref_cnt", type=Usize_t())
        # num_in_reach = TypedVariable(name=f".{instr.var_out.name}_num_in_reach", type=Usize_t(1))
        # num_out_reach = TypedVariable(name=f".{instr.var_out.name}_num_out_reach", type=Usize_t(1))
        # out_visited = TypedVariable(name=f".{instr.var_out.name}_out_visited", type=Usize_t(1))

        ptr_init = Instruction_csoh(ptr, instr.struct)
        # ref_cnt_init = Instruction_lcpos(ref_cnt, Usize(val=1))
        # num_in_reach_init = Instruction_lcpos(num_in_reach, Usize(val=0, size=1))
        # num_out_reach_init = Instruction_lcpos(num_out_reach, Usize(val=0, size=1))
        # out_visited_init = Instruction_lcpos(out_visited, Usize(val=0, size=1))

        s = Struct(name=struct_name, args=[ptr])  # , ref_cnt, num_in_reach, num_out_reach, out_visited])
        instr.var_out.type = s.as_type()
        res = Instruction_lcsos(instr.var_out, s)

        return [
            Instruction_comment(""),
            Instruction_comment(f"{instr}"),
            Instruction_comment(""),
            *self._downgrade_csoh(ptr_init),
            # *self._downgrade_lcpos(ref_cnt_init),
            # *self._downgrade_lcpos(num_in_reach_init),
            # *self._downgrade_lcpos(num_out_reach_init),
            # *self._downgrade_lcpos(out_visited_init),
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
            Instruction_comment(""),
            Instruction_comment(f"{instr}"),
            Instruction_comment(""),
            *self._downgrade_cpos(cpos),
            load,
        ]

    def _downgrade_lcsos(self, instr: Instruction_lcsos) -> list[Instruction]:
        assert instr.var_out.type is not None
        out_ptr = TypedVariable(name=f".{instr.var_out.name}_ptr", type=Pointer(instr.var_out.type))
        csos = Instruction_csos(var_out=out_ptr, struct=instr.struct)
        load = Instruction_load(var_out=instr.var_out, var=out_ptr)
        return [
            Instruction_comment(""),
            Instruction_comment(f"{instr}"),
            Instruction_comment(""),
            *self._downgrade_csos(csos),
            load,
        ]

    def _downgrade_getfield(self, instr: Instruction_getfield) -> list[Instruction]:
        assert instr.var_out.type is not None
        out_ptr = TypedVariable(name=f".{instr.var_out.name}_ptr", type=Pointer(instr.var_out.type))
        getfieldptr = Instruction_getfieldptr(var_out=out_ptr, src=instr.src, indexes=instr.indexes)
        load = Instruction_load(var_out=instr.var_out, var=out_ptr)
        return [
            Instruction_comment(""),
            Instruction_comment(f"{instr}"),
            Instruction_comment(""),
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
