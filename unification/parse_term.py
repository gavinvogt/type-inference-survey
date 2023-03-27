from terms import Term, Variable, Application, Constant
from typing import Literal
import re

Kind = Literal["NAME", "LPAREN", "RPAREN", "COMMA", "EOF"]


class Token:
    """Token for parsing the lambda calculus"""

    def __init__(self, kind: Kind, value: str):
        self.kind = kind
        self.value = value


TOKEN_SPECIFICATION = (
    ("NAME", r"\w+"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMMA", r","),
    ("IGNORE", r"\s+"),
    ("MISMATCH", r"."),
)
TOKEN_REGEX = re.compile(
    "|".join(f"(?P<{kind}>{value})" for kind, value in TOKEN_SPECIFICATION)
)


class Scanner:
    def __init__(self, term_str: str):
        self._i = 0
        self.tokens: list[Token] = []
        for mo in re.finditer(TOKEN_REGEX, term_str):
            kind: Literal[
                "NAME", "LPAREN", "RPAREN", "COMMA", "IGNORE", "MISMATCH"
            ] = mo.lastgroup
            value = mo.group()
            if kind == "IGNORE":
                continue
            elif kind == "MISMATCH":
                raise Exception(f"Invalid character '{value}'")
            else:
                self.tokens.append(Token(kind, value))
        self.tokens.append(Token("EOF", ""))

    def peek(self):
        return self.tokens[self._i]

    def consume(self):
        token = self.peek()
        self._i += 1
        return token

    def match(self, kind: Kind):
        token = self.peek()
        if token.kind == kind:
            return self.consume()
        else:
            raise Exception(f"Expected {kind} but got {token.kind}")


# --------------------------------------------+
# Lax EBNF for my lambda calculus syntax      |
# --------------------------------------------+
# term ::= app | var | constant               |
# app ::= name "(" [term {"," term}] ")"      |
# var ::= name                                |
# constant ::= Name                           |
# name ::= \w+                                |
# --------------------------------------------+


def parse_term(term_str: str) -> Term:
    """Parses a term of the lambda calculus"""
    s = Scanner(term_str)
    term = _term(s)
    s.match("EOF")
    return term


def _term(s: Scanner) -> Term:
    """Helper function for parsing a term of the lambda calculus"""
    name = s.match("NAME").value
    if s.peek().kind == "LPAREN":
        # Read all the arguments
        s.consume()
        args: list[Term] = []
        if s.peek().kind != "RPAREN":
            # Has 1+ arguments
            args.append(_term(s))
            while s.peek().kind == "COMMA":
                s.consume()
                args.append(_term(s))
        s.match("RPAREN")
        return Application(name, args)
    else:
        # Variable or constant
        # Uses opposite convention as Prolog
        if name[0].isupper():
            # Constant if capitalized
            return Constant(name)
        else:
            # Variable if not capitalized
            return Variable(name)


if __name__ == "__main__":
    t = parse_term("f(x, g(y), A)")
    print(t)
