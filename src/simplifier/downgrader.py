from src.core.derectives import Derective_fn
from src.core.derectives.base import Derective
from src.core.instructions.base import Instruction
from src.core.instructions.capture import Instruction_cpoh, Instruction_cpos
from src.core.instructions.control_flow.br import Instruction_br
from src.core.instructions.control_flow.cbr import Instruction_cbr
from src.core.instructions.control_flow.ret import Instruction_ret
from src.core.instructions.control_flow.switch import Instruction_switch
from src.core.instructions.memory import Instruction_hfree, Instruction_put
from src.core.instructions.memory.halloc import Instruction_halloc
from src.core.instructions.memory.load import Instruction_load
from src.core.instructions.memory.salloc import Instruction_salloc
from src.core.instructions.operators.arithmetic import Instruction_add
from src.core.instructions.special.call import Instruction_call
from src.core.primitives import Usize, Usize_t
from src.core.type import Pointer
from src.core.variable import TypedVariable

SKIPABLE = (
    Instruction_ret,
    Instruction_add,
    Instruction_call,
    Instruction_switch,
    Instruction_salloc,
    Instruction_load,
    Instruction_put,
    Instruction_hfree,
)


class Downgrader:
    def run(self, ast: list[Derective]):
        for derective in ast:
            if isinstance(derective, Derective_fn):
                self._downgrade_function(derective)

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
        return [salloc, put]

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
        return [halloc, put]

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
        zero = TypedVariable(name=".zero", type=Usize_t(1))
        cpos = Instruction_cpos(var_out=zero, primitive=Usize(0, size=1))

        switch = Instruction_switch(
            cond_var=zero,
            default_case=instr.label,
            cases=[],
        )
        return [*self._downgrade_cpos(cpos), switch]
