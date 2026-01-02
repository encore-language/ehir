import src.parser.tokens as t


class Lexer:
    def __init__(self):
        self._tokens = []
        self._program = ""
        self._column = 0
        self._line = 0
        self._consumed = 0
        self._string = ""
        self._ignored = (t.WHITESPACE, t.NEWLINE)

    def tokenize(self, source_code: str) -> list[t.Token]:
        self._program = source_code

        while not self._is_at_end():
            curr_char = self._consume()

            match curr_char:
                case " ":
                    self._append_token(t.WHITESPACE)
                case "\n":
                    self._append_token(t.NEWLINE)
                    self._line += 1
                    self._column = 0

                # Parenthesses
                case "(":
                    self._append_token(t.LEFT_PAREN)
                case ")":
                    self._append_token(t.RIGHT_PAREN)
                case "{":
                    self._append_token(t.LEFT_BRACE)
                case "}":
                    self._append_token(t.RIGHT_BRACE)
                case "[":
                    self._append_token(t.LEFT_BRACKET)
                case "]":
                    self._append_token(t.RIGHT_BRACKET)

                # Operators
                case "-":
                    if self._lookup_curr() == ">":
                        self._consume()
                        self._append_token(t.ARROW)
                    else:
                        self._append_token(t.MINUS)

                case "+":
                    self._append_token(t.PLUS)

                case "=":
                    self._append_token(t.EQUAL)

                # Punctuation
                case "$":
                    self._append_token(t.DOLLAR)

                case ".":
                    self._append_token(t.DOT)

                case ",":
                    self._append_token(t.COMMA)

                case ":":
                    self._append_token(t.COLON)

                case ";":
                    self._append_token(t.SEMICOLON)

                case _:
                    if curr_char.isdigit():
                        self._parse_number()
                    elif curr_char.isidentifier():
                        self._parse_identifier()
                    else:
                        raise ValueError(f"Unexpected character '{curr_char}'")

        return self._tokens

    def _parse_number(self):
        while self._lookup_curr().isdigit():
            self._consume()
        self._append_token(t.NUMBER)

    def _parse_identifier(self):
        while self._lookup_curr().isalnum():
            self._consume()

        match self._string:
            case "fn":
                self._append_token(t.FN)
            case "cpos":
                self._append_token(t.CPOS)
            case "call":
                self._append_token(t.CALL)
            case "ret":
                self._append_token(t.RET)
            case "add":
                self._append_token(t.ADD)
            case "sub":
                self._append_token(t.SUB)
            case _:
                self._append_token(t.IDENTIFIER)

    def _append_token(self, token_type: type[t.Token]):
        if token_type not in self._ignored:
            self._tokens.append(token_type(self._string))
        self._string = ""

    def _lookup_curr(self) -> str:
        return "" if self._is_at_end(0) else self._program[self._consumed + 0]

    def _lookup_next(self) -> str:
        return "" if self._is_at_end(1) else self._program[self._consumed + 1]

    def _consume(self) -> str:
        current_char = self._program[self._consumed]
        self._string += current_char
        self._consumed += 1
        return current_char

    def _is_at_end(self, shift: int = 0) -> bool:
        return self._consumed + shift >= len(self._program)
