from src.compiler import Compiler
from src.core.block import Block
from src.core.derectives import Derective_fn
from src.core.instructions.capture.cpos import Instruction_cpos
from src.core.instructions.control_flow.ret import Instruction_ret
from src.core.primitives import Usize, Usize_t
from src.core.variable import Variable


def main():
    compiler = Compiler()
    program = [
        Derective_fn(
            name="main",
            params=[],
            ret_type=Usize_t(),
            body=[
                Block(
                    name="entry",
                    body=[
                        Instruction_cpos(var_out=Variable(name="zero"), primitive=Usize(0)),
                        Instruction_ret(var=Variable(name="zero")),
                    ],
                ),
            ],
        ),
    ]
    print(*program, sep="\n")
    print("=" * 64)
    compiler.compile(program)


if __name__ == "__main__":
    main()
