"""
Program: parser.py
Author: Gavin Vogt
This program defines the parser for Micro-ML
"""

from .scanner import Scanner
from .ast import (
    FunctionDefinition,
    CallExpr,
    IfExpr,
    LetExpr,
    FnExpr,
    BinaryExpr,
    UnaryExpr,
    IdExpr,
    UnitExpr,
    IntLiteral,
    RealLiteral,
    BoolLiteral,
    Expression,
)


class Parser:
    def __init__(self):
        self._scanner = Scanner()
        self._statements: list[FunctionDefinition] = []

    def parse(self, code: str) -> list[FunctionDefinition]:
        self._scanner.scan(code)
        self._program()
        self._scanner.match("EOF")
        return self._statements

    def parse_file(self, fp: str):
        with open(fp, "r") as f:
            return self.parse(f.read())

    def _program(self):
        while self._scanner.peek().kind == "fun":
            self._statements.append(self._func_def())
            self._scanner.match("END")

    def _func_def(self) -> FunctionDefinition:
        self._scanner.match("fun")
        func_name = self._scanner.match("ID").value
        params = self._params()
        self._scanner.match("=")
        expr = self._expr()
        return FunctionDefinition(func_name, params, expr)

    def _params(self) -> list[str]:
        parameters: list[str] = []
        while self._scanner.peek().kind == "ID":
            # Match an argument
            tok = self._scanner.match("ID")
            parameters.append(tok.value)
        return parameters

    def _expr(self) -> Expression:
        tok = self._scanner.peek()
        match tok.kind:
            case "if":
                return self._if_expr()
            case "let":
                return self._let_expr()
            case "fn":
                return self._fn_expr()
            case _:
                return self._expr0()

    # "if" expr "then" expr "else" expr
    def _if_expr(self) -> Expression:
        self._scanner.match("if")
        cond_expr = self._expr()
        self._scanner.match("then")
        then_expr = self._expr()
        self._scanner.match("else")
        else_expr = self._expr()
        return IfExpr(cond_expr, then_expr, else_expr)

    # "let" ID "=" expr "in" expr
    def _let_expr(self) -> Expression:
        self._scanner.match("let")
        var_name = self._scanner.match("ID").value
        self._scanner.match("=")
        val_expr = self._expr()
        self._scanner.match("in")
        expr = self._expr()
        return LetExpr(var_name, val_expr, expr)

    # "fn" ID "=>" expr
    def _fn_expr(self) -> Expression:
        self._scanner.match("fn")
        params = self._params()
        self._scanner.match("=>")
        expr = self._expr()
        return FnExpr(params, expr)

    # expr1 { "or" expr1 }
    def _expr0(self) -> Expression:
        left_expr = self._expr1()
        while self._scanner.peek().kind == "or":
            self._scanner.match("or")
            right_expr = self._expr1()
            left_expr = BinaryExpr("or", left_expr, right_expr)
        return left_expr

    # expr2 { "and" expr2 }
    def _expr1(self) -> Expression:
        left_expr = self._expr2()
        while self._scanner.peek().kind == "and":
            self._scanner.match("and")
            right_expr = self._expr2()
            left_expr = BinaryExpr("and", left_expr, right_expr)
        return left_expr

    # expr3 [ comparison_op expr3 ]
    def _expr2(self) -> Expression:
        left_expr = self._expr3()
        if self._scanner.peek().kind in {"!=", "<", "<=", "==", ">", ">="}:
            op = self._scanner.consume().value
            right_expr = self._expr3()
            left_expr = BinaryExpr(op, left_expr, right_expr)
        return left_expr

    # expr4 [ add_op expr4 ]
    def _expr3(self) -> Expression:
        left_expr = self._expr4()
        while self._scanner.peek().kind in {"+", "-"}:
            op = self._scanner.consume().value
            right_expr = self._expr4()
            left_expr = BinaryExpr(op, left_expr, right_expr)
        return left_expr

    # expr5 { mult_op expr5 }
    def _expr4(self) -> Expression:
        left_expr = self._expr5()
        while self._scanner.peek().kind in {"*", "/"}:
            op = self._scanner.consume().value
            right_expr = self._expr5()
            left_expr = BinaryExpr(op, left_expr, right_expr)
        return left_expr

    # { "-" | "not" } expr6
    def _expr5(self) -> Expression:
        # Collect the "-" and "not" operations
        negation_ops: list[str] = []
        while self._scanner.peek().kind in {"-", "not"}:
            op = self._scanner.consume().value
            negation_ops.append(op)

        expr = self._expr6()
        for op in reversed(negation_ops):
            expr = UnaryExpr(op, expr)
        return expr

    # int_literal
    # real_literal
    # bool_literal
    # ID
    # "(" expr ")"
    # expr6 expr6
    def _expr6(self, parse_call: bool = True) -> Expression:
        tok = self._scanner.consume()
        match tok.kind:
            case "INT":
                return IntLiteral(int(tok.value))
            case "REAL":
                return RealLiteral(float(tok.value))
            case "true":
                return BoolLiteral(True)
            case "false":
                return BoolLiteral(False)
            case "ID":
                expr = IdExpr(tok.value)
            case "(":
                if self._scanner.peek().kind == ")":
                    expr = UnitExpr()
                else:
                    expr = self._expr()
                self._scanner.match(")")
            case _:
                raise Exception(f"Syntax error at {tok.coord}")

        if parse_call:
            # In case it is a function call
            # f a b c = FunctionCall(FunctionCall(FunctionCall("f", "a"), "b"), "c")
            while self._scanner.peek().kind in {
                "INT",
                "REAL",
                "true",
                "false",
                "ID",
                "(",
            }:
                arg = self._expr6(parse_call=False)
                expr = CallExpr(expr, arg)

        return expr


def main():
    p = Parser()
    program = p.parse(
        """
    fun product a b c = a * b * c;

    fun f x y = if x then y else 5;
    
    fun g z = let x = z * 2 in x + 4;

    fun isZero val = if val == 0 then true else false;

    fun f x = (fn y => y + 1) x;

    fun fact x = if x == 0 then 1 else x * fact(x - 1);
    """
    )
    for statement in program:
        print(statement)


if __name__ == "__main__":
    main()
