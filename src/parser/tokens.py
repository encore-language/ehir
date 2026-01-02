from dataclasses import dataclass


@dataclass
class Token:
    string: str


class IDENTIFIER(Token): ...


class NUMBER(Token): ...


class ARROW(Token): ...


class EOF(Token): ...


# Keywords
class FN(Token): ...


class CPOS(Token): ...


class RET(Token): ...


# Operators
class PLUS(Token): ...


class MINUS(Token): ...


class EQUAL(Token): ...


# Punctuation
class COMMA(Token): ...


class SEMICOLON(Token): ...


class COLON(Token): ...


class DOT(Token): ...


class DOLLAR(Token): ...


# Parentheses


class LEFT_PAREN(Token): ...


class RIGHT_PAREN(Token): ...


class LEFT_BRACE(Token): ...


class RIGHT_BRACE(Token): ...


class LEFT_BRACKET(Token): ...


class RIGHT_BRACKET(Token): ...


# Whitespace


class WHITESPACE(Token): ...


class NEWLINE(Token): ...


class TAB(Token): ...
