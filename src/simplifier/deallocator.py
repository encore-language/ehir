from collections import deque

from src.core.block import TerminatedBlock
from src.core.derectives.base import Derective
from src.core.instructions.base import Assignable
from src.core.instructions.capture import Instruction_lcpos, Instruction_scsoh
from src.core.instructions.control_flow.br import Instruction_br
from src.core.instructions.control_flow.cbr import Instruction_cbr
from src.core.instructions.control_flow.ret import Instruction_ret
from src.core.instructions.control_flow.switch import Instruction_switch
from src.core.instructions.memory import Instruction_getptr, Instruction_halloc, Instruction_load, Instruction_store
from src.core.variable import Variable
from src.simplifier.normalizer.norm_fn import Normalized_fn


class Deallocator:
    _usages: dict[str, set[str]]
    _curr_block: str

    def run(self, ast: list[Derective]):
        for derective in ast:
            if isinstance(derective, Normalized_fn):
                self._run_in_function(derective)

    def _run_in_function(self, fn: Normalized_fn):
        self._usages = {}
        cfg: dict[str, list[str]] = {}

        name2block: dict[str, TerminatedBlock] = {}
        for block in fn.get_body():
            assert isinstance(block, TerminatedBlock)
            name2block[block.name] = block

        if "entry" not in name2block:
            raise ValueError(f"Function '{fn.name}' doesn`t contain `entry` block!")

        queue: deque[TerminatedBlock] = deque([name2block["entry"]])
        while queue:
            block = queue.popleft()
            self._collect_variable_usages(block)

            children: list[str] = []
            if isinstance(block.term, Instruction_br):
                children.append(block.term.label)
            elif isinstance(block.term, Instruction_cbr):
                children.append(block.term.true_br_label)
                children.append(block.term.else_br_label)
            elif isinstance(block.term, Instruction_switch):
                children.append(block.term.default_case)
                for case in block.term.cases:
                    children.append(case[1])

            for child in children:
                if child not in cfg.get(block.name, []):
                    cfg[block.name] = cfg.get(block.name, []) + [child]
                if child not in cfg:
                    queue.append(name2block[child])

        print(cfg)
        print(self._usages)

    def _add_variable_usage(self, var: Variable):
        self._usages[var.name] = self._usages.get(var.name, set()) | {self._curr_block}

    def _collect_variable_usages(self, block: TerminatedBlock):
        self._curr_block = block.name
        for instr in [*block.body, block.term]:
            if isinstance(instr, Assignable):
                self._add_variable_usage(instr.var_out)

            if isinstance(instr, (Instruction_br, Instruction_halloc, Instruction_lcpos)):
                pass
            elif isinstance(instr, Instruction_ret):
                self._add_variable_usage(instr.var)
            elif isinstance(instr, Instruction_getptr):
                self._add_variable_usage(instr.var)
            elif isinstance(instr, Instruction_store):
                self._add_variable_usage(instr.var_src)
                self._add_variable_usage(instr.var_dst)
            elif isinstance(instr, Instruction_load):
                self._add_variable_usage(instr.var)
            elif isinstance(instr, Instruction_scsoh):
                for arg in instr.struct.args:
                    self._add_variable_usage(arg)
            else:
                raise NotImplementedError(f"Variable usage not define for {instr}")
