from src.core.block import Block
from src.core.derectives import Derective_fn
from src.core.derectives.base import Derective
from src.core.instructions.base import Instruction
from src.core.instructions.capture import Instruction_cpos
from src.core.instructions.control_flow.ret import Instruction_ret
from src.core.primitives import Usize, Usize_t
from src.core.primitives.base import Primitive, PrimitiveType
from src.core.type import Type
from src.core.variable import Variable
from src.parser import tokens as t
from src.parser.lexer import Lexer


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
        while not self._is_at_end():
            current_token = self._lookup_curr()

            if isinstance(current_token, t.FN):
                self._ast.append(self._parse_fn())
            else:
                raise ValueError(f"Unexpected token {current_token}")

        return self._ast

    def _parse_fn(self) -> Derective_fn:
        self._safe_consume(t.FN)
        name = self._safe_consume(t.IDENTIFIER).string
        self._safe_consume(t.LEFT_PAREN)
        self._safe_consume(t.RIGHT_PAREN)
        self._safe_consume(t.ARROW)
        ret_type = self._parse_type()
        self._safe_consume(t.LEFT_BRACE)

        body = []
        while not isinstance(self._lookup_curr(), t.RIGHT_BRACE):
            body.append(self._parse_block())
        self._safe_consume(t.RIGHT_BRACE)

        return Derective_fn(name=name, params=[], ret_type=ret_type, body=body)

    def _parse_block(self) -> Block:
        self._safe_consume(t.DOLLAR)
        name = self._safe_consume(t.IDENTIFIER).string
        self._safe_consume(t.COLON)

        body: list[Instruction] = []

        while instr := self._parse_instruction():
            body.append(instr)

        return Block(name=name, body=body)

    def _parse_instruction(self) -> Instruction | None:
        next_token = self._lookup_next()
        if isinstance(next_token, t.EQUAL):
            return self._parse_assignable()

        curr_token = self._lookup_curr()
        if isinstance(curr_token, t.RET):
            return self._parse_ret()

    def _parse_ret(self) -> Instruction_ret:
        self._safe_consume(t.RET)
        var = self._parse_variable()
        return Instruction_ret(var)

    def _parse_assignable(self) -> Instruction:
        var = self._parse_variable()
        self._safe_consume(t.EQUAL)

        curr_token = self._consume()
        if isinstance(curr_token, t.CPOS):
            primitive = self._parse_primitive()
            return Instruction_cpos(var_out=var, primitive=primitive)
        else:
            raise ValueError(f"Unexpected token {curr_token}")

    def _parse_variable(self) -> Variable:
        name = self._safe_consume(t.IDENTIFIER)
        type = None
        if isinstance(self._lookup_curr(), t.COLON):
            self._safe_consume(t.COLON)
            type = self._parse_type()
        return Variable(name.string, type)

    def _parse_type(self) -> Type | PrimitiveType:
        name = self._safe_consume(t.IDENTIFIER).string

        if name.startswith("u") and name[1:].isdigit():
            size = int(name[1:])
            return Usize_t(size=size)

        return Type(name)

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
        return t.EOF("") if self._is_at_end(0) else self._tokens[self._consumed + 0]

    def _lookup_next(self) -> t.Token:
        return t.EOF("") if self._is_at_end(1) else self._tokens[self._consumed + 1]

    def _safe_consume(self, expected: type[t.Token]) -> t.Token:
        current_token = self._consume()
        if not isinstance(current_token, expected):
            raise ValueError(f"Expected {expected}, got {current_token}")
        return current_token

    def _consume(self) -> t.Token:
        current_token = self._lookup_curr()
        self._consumed += 1
        return current_token

    def _is_at_end(self, n: int = 0) -> bool:
        return self._consumed + n >= len(self._tokens)
