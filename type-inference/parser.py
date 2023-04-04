"""
File: parser.py
Author: Gavin Vogt
Parser for the type unification grammar
"""

from json import load
from ast import *
import re
from typing import Literal


AST_TYPE_FIELD = "type"


def load_program(fp: str) -> list[AST]:
    with open(fp, "r") as f:
        program = load(f)
    return [generate_ast(statement) for statement in program]


def generate_ast(data):
    match data:
        case bool():
            return BoolLiteral(data)
        case int():
            return IntLiteral(data)
        case float():
            return FloatLiteral(data)
        case str():
            return IdExpr(data)
        case dict():
            # Figure out the type of AST
            ast_type: str = data[AST_TYPE_FIELD]
            match ast_type:
                case "FuncDecl":
                    return FunctionDefinition(
                        data["name"], data["params"], generate_ast(data["body"])
                    )
                case "FuncCall":
                    return FunctionCall(
                        generate_ast(data["expr"]),
                        [generate_ast(arg) for arg in data["args"]],
                    )

                case "If":
                    return IfExpr(
                        generate_ast(data["condition"]),
                        generate_ast(data["then"]),
                        generate_ast(data["else"]),
                    )

                case "Let":
                    return LetExpr(
                        data["var"],
                        generate_ast(data["val"]),
                        generate_ast(data["expr"]),
                    )

                case _:
                    if "left" in data and "right" in data:
                        return BinaryOp(
                            ast_type,
                            generate_ast(data["left"]),
                            generate_ast(data["right"]),
                        )
                    raise Exception(f"Unknown AST type {ast_type}")
        case _:
            raise Exception("Failed to process JSON for AST")


TYPE_ANNOTATION_REGEX = "|".join(
    "(?P<%s>%s)" % pair
    for pair in [
        ("LP", r"("),
        ("RP", r")"),
        ("COMMA", r","),
        ("ARROW", r"->"),
        ("CONSTANT", r"[A-Z]\w*"),
        ("VARIABLE", r"[a-z]\w*"),
        ("LIST", r"\[]"),
        ("IGNORE", r"\s+"),
        ("MISMATCH", r"."),
    ]
)

# func_type : type -> type
# type : constant | variable | type[]
# constant :


def parse_type_annotation(type_annotation: str):
    """Parses the type annotation, such as (a, b) -> Int"""
    for mo in re.finditer(TYPE_ANNOTATION_REGEX, type_annotation):
        kind: Literal[
            "LP",
            "RP",
            "COMMA",
            "ARROW",
            "CONSTANT",
            "VARIABLE",
            "LIST",
            "IGNORE",
            "MISMATCH",
        ] = mo.lastgroup
        value = mo.group()

        if kind == "MISMATCH":
            raise Exception(f"Unexpected character {value}")


def main():
    pass


if __name__ == "__main__":
    main()
