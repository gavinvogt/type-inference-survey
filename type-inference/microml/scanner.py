"""
File: scanner.py
Author: Gavin Vogt
This program defines the scanner (lexer) for the micro-ML syntax.
"""

from typing import NamedTuple, Final
import re

KEYWORDS: Final = {
    "fun",
    "fn",
    "if",
    "then",
    "else",
    "let",
    "in",
    "true",
    "false",
    "and",
    "or",
    "not",
}

PUNCTUATION: Final = (
    "(",
    ")",
    "+",
    "-",
    "*",
    "/",
    "=>",
    "<=",
    ">=",
    "==",
    "!=",
    "=",
    "<",
    ">",
)


class Coord(NamedTuple):
    line: int
    col: int

    def __str__(self):
        return f"line {self.line}, column {self.col}"


class Token(NamedTuple):
    kind: str
    value: str
    coord: Coord


TOKEN_SPECIFICATION: Final = (
    ("REAL", r"\d+\.\d+"),  # Real (float) number
    ("INT", r"\d+"),  # Integer number
    ("PUNC", f"({'|'.join(re.escape(punc) for punc in PUNCTUATION)})"),
    ("ID", r"[a-zA-Z]\w*"),  # Identifiers
    ("END", r";"),  # End of a statement
    ("COMMENT", r"#.*\n"),  # Comment
    ("NEWLINE", r"\n"),  # Newline (for tracking line number)
    ("SKIP", r"[ \t]+"),  # Skip over whitespace
    ("MISMATCH", r"."),  # Anything else does not match
)
TOK_REGEX: Final = re.compile(
    "|".join(f"(?P<{kind}>{regex})" for kind, regex in TOKEN_SPECIFICATION)
)


class Scanner:
    def __init__(self):
        self._i = 0
        self._tokens: list[Token] = []

    def scan(self, code: str):
        line_num = 1
        # line_start = 0
        column = 1
        for mo in re.finditer(TOK_REGEX, code):
            kind: str = mo.lastgroup  # type: ignore
            value: str = mo.group()
            if kind in ("COMMENT", "NEWLINE"):
                line_num += 1
                column = 1
            else:
                column += len(value)
                if kind == "PUNC" or (kind == "ID" and value in KEYWORDS):
                    # Token is a keyword or punctuation rather than an identifier
                    kind = value
                elif kind == "SKIP":
                    continue
                elif kind == "MISMATCH":
                    raise RuntimeError(f"{value!r} unexpected on line {line_num}")
                self._tokens.append(
                    Token(kind, value, Coord(line_num, column - len(value)))
                )
        self._tokens.append(Token("EOF", "", Coord(line_num, column)))

    def peek(self):
        return self._tokens[self._i]

    def consume(self):
        tok = self._tokens[self._i]
        self._i += 1
        return tok

    def match(self, kind: str):
        tok = self.peek()
        if tok.kind == kind:
            return self.consume()
        else:
            raise Exception(f"Invalid token '{tok.value}' at {tok.coord}")


def main():
    s = Scanner()
    s.scan(
        """
    # Comment
    fun f x y = if x then y else 5;
    
    fun g z = let x = z * 2 in x + 4;

    fun isZero val = if val == 0 then true else false;  # In-line comment

    fun f x = (fn y => y + 1) x;
    """
    )
    tok = s.consume()
    while tok.kind != "EOF":
        print(tok)
        tok = s.consume()


if __name__ == "__main__":
    main()
