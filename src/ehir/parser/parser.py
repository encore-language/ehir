from ehir.core.block import Block
from ehir.core.derectives import Derective_fn, Derective_struct
from ehir.core.derectives.base import Derective
from ehir.core.instructions.base import Instruction
from ehir.core.instructions.capture import (
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
from ehir.core.instructions.control_flow.br import Instruction_br
from ehir.core.instructions.control_flow.cbr import Instruction_cbr
from ehir.core.instructions.control_flow.ret import Instruction_ret
from ehir.core.instructions.control_flow.switch import Instruction_switch
from ehir.core.instructions.memory import (
    Instruction_getfield,
    Instruction_getfieldptr,
    Instruction_getptr,
    Instruction_hfree,
    Instruction_pcast,
    Instruction_put,
)
from ehir.core.instructions.memory.halloc import Instruction_halloc
from ehir.core.instructions.memory.load import Instruction_load
from ehir.core.instructions.memory.salloc import Instruction_salloc
from ehir.core.instructions.operators.arithmetic import (
    Instruction_add,
    Instruction_div,
    Instruction_mul,
    Instruction_sub,
)
from ehir.core.instructions.special.call import Instruction_call
from ehir.core.primitives import Usize, Usize_t
from ehir.core.primitives.base import Primitive, PrimitiveType
from ehir.core.struct import Struct
from ehir.core.type import HeapSmartPointer, Pointer, StackSmartPointer, Type
from ehir.core.variable import Parameter, Variable
from ehir.parser import tokens as t
from ehir.parser.lexer import Lexer


class Parser:
    _ast: list[Derective]

    def __init__(self):
        self._lexer = Lexer()
        self._tokens = []
        self._ast = []
        self._consumed = 0

    def parse(self, source_code: str) -> list[Derective]:
        self._ast.clear()
        self._tokens = self._lexer.tokenize(source_code)
        # print(*self._tokens, sep="\n")
        while not self._is_at_end():
            current_token = self._lookup_curr()

            if isinstance(current_token, t.FN):
                self._ast.append(self._parse_fn())
            elif isinstance(current_token, t.STRUCT):
                self._ast.append(self._parse_struct())
            else:
                raise ValueError(f"Unexpected token {current_token}")

        return self._ast

    def _parse_struct(self) -> Derective_struct:
        self._safe_consume(t.STRUCT)
        name = self._safe_consume(t.IDENTIFIER).string

        params = []
        self._safe_consume(t.LEFT_BRACE)
        while not isinstance(self._lookup_curr(), t.RIGHT_BRACE):
            params.append(self._parse_param())
        self._safe_consume(t.RIGHT_BRACE)

        return Derective_struct(name=name, params=params)

    def _parse_fn(self) -> Derective_fn:
        self._safe_consume(t.FN)
        name = self._safe_consume(t.IDENTIFIER).string

        params = []
        self._safe_consume(t.LEFT_PAREN)
        if not isinstance(self._lookup_curr(), t.RIGHT_PAREN):
            params.append(self._parse_param())

            while not isinstance(self._lookup_curr(), t.RIGHT_PAREN):
                self._safe_consume(t.COMMA)
                params.append(self._parse_param())
        self._safe_consume(t.RIGHT_PAREN)

        self._safe_consume(t.ARROW)
        ret_type = self._parse_type()

        self._safe_consume(t.LEFT_BRACE)

        body = []
        while not isinstance(self._lookup_curr(), t.RIGHT_BRACE):
            body.append(self._parse_block())
        self._safe_consume(t.RIGHT_BRACE)

        return Derective_fn(name=name, params=params, ret_type=ret_type, body=body)

    def _parse_block(self) -> Block:
        name = self._parse_block_label()
        self._safe_consume(t.COLON)

        body: list[Instruction] = []

        while instr := self._parse_instruction():
            body.append(instr)

        return Block(name=name, body=body)

    def _parse_instruction(self) -> Instruction | None:
        curr_token = self._lookup_curr()
        if isinstance(curr_token, t.RET):
            return self._parse_ret()
        elif isinstance(curr_token, t.BR):
            return self._parse_br()
        elif isinstance(curr_token, t.CBR):
            return self._parse_cbr()
        elif isinstance(curr_token, t.SWITCH):
            return self._parse_switch()
        elif isinstance(curr_token, t.PUT):
            return self._parse_put()
        elif isinstance(curr_token, t.HFREE):
            return self._parse_hfree()

        next_token = self._lookup_next()
        # Assign with typed / untyped variable
        if isinstance(next_token, (t.COLON, t.EQUAL)):
            return self._parse_assignable()

    def _parse_hfree(self) -> Instruction_hfree:
        self._safe_consume(t.HFREE)
        var = self._parse_variable()
        return Instruction_hfree(var=var)

    def _parse_put(self) -> Instruction_put:
        self._safe_consume(t.PUT)
        prim = self._parse_primitive()
        self._safe_consume(t.COMMA)
        var = self._parse_variable()
        return Instruction_put(var=var, primitive=prim)

    def _parse_br(self) -> Instruction_br:
        self._safe_consume(t.BR)
        label = self._parse_block_label()
        return Instruction_br(label)

    def _parse_cbr(self) -> Instruction_cbr:
        self._safe_consume(t.CBR)
        cond = self._parse_variable()
        self._safe_consume(t.COMMA)
        true_br = self._parse_block_label()
        self._safe_consume(t.COMMA)
        else_br = self._parse_block_label()

        return Instruction_cbr(cond_var=cond, true_br_label=true_br, else_br_label=else_br)

    def _parse_switch(self) -> Instruction_switch:
        self._safe_consume(t.SWITCH)
        cond_var = self._parse_variable()
        self._safe_consume(t.COMMA)
        default_label = self._parse_block_label()

        cases = []
        self._safe_consume(t.LEFT_BRACE)
        while not isinstance(self._lookup_curr(), t.RIGHT_BRACE):
            val = self._parse_primitive()
            assert isinstance(val, Usize), "Switch case value must be a usize"
            self._safe_consume(t.BOLD_ARROW)
            label = self._parse_block_label()
            cases.append((val, label))
        self._safe_consume(t.RIGHT_BRACE)
        return Instruction_switch(cond_var=cond_var, default_case=default_label, cases=cases)

    def _parse_ret(self) -> Instruction_ret:
        self._safe_consume(t.RET)
        var = self._parse_variable()
        return Instruction_ret(var)

    def _parse_block_label(self) -> str:
        self._safe_consume(t.DOLLAR)
        return self._safe_consume(t.IDENTIFIER).string

    def _parse_assignable(self) -> Instruction:
        var = self._parse_variable()
        self._safe_consume(t.EQUAL)

        curr_token = self._consume()
        if isinstance(curr_token, t.CPOS):
            primitive = self._parse_primitive()
            return Instruction_cpos(var_out=var, primitive=primitive)

        elif isinstance(curr_token, t.CPOH):
            primitive = self._parse_primitive()
            return Instruction_cpoh(var_out=var, primitive=primitive)

        elif isinstance(curr_token, t.CSOS):
            struct = self._parse_struct_init()
            return Instruction_csos(var_out=var, struct=struct)

        elif isinstance(curr_token, t.CSOH):
            struct = self._parse_struct_init()
            return Instruction_csoh(var_out=var, struct=struct)

        elif isinstance(curr_token, t.SCPOS):
            primitive = self._parse_primitive()
            return Instruction_scpos(var_out=var, primitive=primitive)

        elif isinstance(curr_token, t.SCPOH):
            primitive = self._parse_primitive()
            return Instruction_scpoh(var_out=var, primitive=primitive)

        elif isinstance(curr_token, t.SCSOS):
            struct = self._parse_struct_init()
            return Instruction_scsos(var_out=var, struct=struct)

        elif isinstance(curr_token, t.SCSOH):
            struct = self._parse_struct_init()
            return Instruction_scsoh(var_out=var, struct=struct)

        elif isinstance(curr_token, t.LCPOS):
            primitive = self._parse_primitive()
            return Instruction_lcpos(var_out=var, primitive=primitive)

        elif isinstance(curr_token, t.LCSOS):
            struct = self._parse_struct_init()
            return Instruction_lcsos(var_out=var, struct=struct)

        elif isinstance(curr_token, t.CALL):
            fn_name = self._safe_consume(t.IDENTIFIER).string
            args = []
            self._safe_consume(t.LEFT_PAREN)
            if not isinstance(self._lookup_curr(), t.RIGHT_PAREN):
                args.append(self._parse_variable())
                while not isinstance(self._lookup_curr(), t.RIGHT_PAREN):
                    self._safe_consume(t.COMMA)
                    args.append(self._parse_variable())
            self._safe_consume(t.RIGHT_PAREN)
            return Instruction_call(var_out=var, fn_name=fn_name, args=args)

        elif isinstance(curr_token, t.ADD):
            lhs = self._parse_variable()
            self._safe_consume(t.COMMA)
            rhs = self._parse_variable()
            return Instruction_add(var_out=var, lhs=lhs, rhs=rhs)

        elif isinstance(curr_token, t.SUB):
            lhs = self._parse_variable()
            self._safe_consume(t.COMMA)
            rhs = self._parse_variable()
            return Instruction_sub(var_out=var, lhs=lhs, rhs=rhs)

        elif isinstance(curr_token, t.MUL):
            lhs = self._parse_variable()
            self._safe_consume(t.COMMA)
            rhs = self._parse_variable()
            return Instruction_mul(var_out=var, lhs=lhs, rhs=rhs)

        elif isinstance(curr_token, t.DIV):
            lhs = self._parse_variable()
            self._safe_consume(t.COMMA)
            rhs = self._parse_variable()
            return Instruction_div(var_out=var, lhs=lhs, rhs=rhs)

        elif isinstance(curr_token, t.SALLOC):
            type = self._parse_type()
            return Instruction_salloc(var_out=var, type=type)

        elif isinstance(curr_token, t.HALLOC):
            type = self._parse_type()
            return Instruction_halloc(var_out=var, type=type)

        elif isinstance(curr_token, t.LOAD):
            var_src = self._parse_variable()
            return Instruction_load(var_out=var, var=var_src)

        elif isinstance(curr_token, t.PCAST):
            var_src = self._parse_variable()
            self._safe_consume(t.COMMA)
            type = self._parse_type()
            assert isinstance(type, PrimitiveType)
            return Instruction_pcast(var_out=var, var=var_src, type=type)

        elif isinstance(curr_token, t.GETPTR):
            var_src = self._parse_variable()
            return Instruction_getptr(var_out=var, var=var_src)

        elif isinstance(curr_token, t.GETFIELD):
            var_src = self._parse_variable()
            indexes = self._parse_index_list()
            return Instruction_getfield(var_out=var, src=var_src, indexes=indexes)

        elif isinstance(curr_token, t.GETFIELDPTR):
            var_src = self._parse_variable()
            indexes = self._parse_index_list()
            return Instruction_getfieldptr(var_out=var, src=var_src, indexes=indexes)

        else:
            raise ValueError(f"Unexpected token {curr_token}")

    def _parse_index_list(self) -> list[Variable]:
        indexes = []
        while isinstance(self._lookup_curr(), t.GREATER):
            self._safe_consume(t.GREATER)
            indexes.append(self._parse_variable())
        return indexes

    def _parse_struct_init(self) -> Struct:
        name = self._safe_consume(t.IDENTIFIER).string
        params = []
        self._safe_consume(t.LEFT_PAREN)
        if not isinstance(self._lookup_curr(), t.RIGHT_PAREN):
            params.append(self._parse_variable())
            while not isinstance(self._lookup_curr(), t.RIGHT_PAREN):
                self._safe_consume(t.COMMA)
                params.append(self._parse_variable())
        self._safe_consume(t.RIGHT_PAREN)
        return Struct(name, params)

    def _parse_variable(self) -> Variable:
        name = self._safe_consume(t.IDENTIFIER)
        type = None
        if isinstance(self._lookup_curr(), t.COLON):
            self._safe_consume(t.COLON)
            type = self._parse_type()
        return Variable(name.string, type)

    def _parse_param(self) -> Parameter:
        var = self._parse_variable()
        if var.type is not None:
            return Parameter(var.name, var.type)
        else:
            raise ValueError(f"Parameter {var.name} must have a type")

    def _parse_type(self) -> Type | PrimitiveType | Pointer:
        name = self._safe_consume(t.IDENTIFIER).string
        type = Type(name)
        if name.startswith("u") and name[1:].isdigit():
            size = int(name[1:])
            type = Usize_t(size=size)

        if isinstance(self._lookup_curr(), t.STAR):
            self._safe_consume(t.STAR)
            type = Pointer(type)
        elif isinstance(self._lookup_curr(), t.LESS):
            # Smart pointer
            self._safe_consume(t.LESS)
            pointer_t = self._safe_consume(t.IDENTIFIER).string
            if pointer_t == "H":
                type = HeapSmartPointer(type)
            elif pointer_t == "S":
                type = StackSmartPointer(type)
            else:
                raise ValueError(f"Invalid smart pointer type: {pointer_t}")
            self._safe_consume(t.GREATER)

        return type

    def _parse_primitive(self) -> Primitive:
        curr_token = self._consume()
        if isinstance(curr_token, t.NUMBER):
            suffix = self._safe_consume(t.IDENTIFIER).string
            if suffix.startswith("_u"):
                size = int(suffix[2:])
                return Usize(val=int(curr_token.string), size=size)
            else:
                raise ValueError(f"Invalid primitive suffix: {suffix}")
        raise ValueError(f"Expected number, got {curr_token}")

    def _lookup_curr(self) -> t.Token:
        return t.EOF("", 0, 0) if self._is_at_end(0) else self._tokens[self._consumed + 0]

    def _lookup_next(self) -> t.Token:
        return t.EOF("", 0, 0) if self._is_at_end(1) else self._tokens[self._consumed + 1]

    def _safe_consume(self, expected: type[t.Token]) -> t.Token:
        current_token = self._consume()
        if not isinstance(current_token, expected):
            self._trace_unexpected_token(current_token, expected)
        return current_token

    def _consume(self) -> t.Token:
        current_token = self._lookup_curr()
        self._consumed += 1
        return current_token

    def _is_at_end(self, n: int = 0) -> bool:
        return self._consumed + n >= len(self._tokens)

    def _trace_unexpected_token(self, token: t.Token, expected_t: type[t.Token]):
        raise ValueError(f"Unexpected token: {token}")
