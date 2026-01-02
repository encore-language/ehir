from dataclasses import dataclass

from core.instructions.control_flow.base import ControlFlow
from core.primitives import Usize
from core.variable import Variable


@dataclass
class Instruction_switch(ControlFlow):
    cond_var: Variable
    default_case: str
    cases: list[tuple[Usize, str]]

    def __str__(self) -> str:
        cases_str = ", ".join(f"{case[0]}: {case[1]}" for case in self.cases)
        return f"switch {self.cond_var}, {self.default_case} {{ {cases_str} }}"
