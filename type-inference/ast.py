"""
Author: Gavin Vogt
File: ast.py
This program defines the classes for an AST
"""

from typing import Iterable
from constructs import Type


class TypeSymbol:
    def __init__(self):
        self._type = None

    @property
    def type(self) -> Type:
        if self._type is None:
            raise Exception("Error: accessing type symbol with no type")
        return self._type

    @type.setter
    def type(self, new_type: Type):
        self._type = new_type


# class Id:
#     def __init__(self, id: str):
#         self._id = id

#     def __str__(self):
#         return f"Id('{self._id}')"


class AST:
    """Represents an abstract syntax tree"""

    def __init__(self):
        self.type: Type | None = None

    def gen_type_equations(self) -> Iterable[tuple[Type, Type]]:
        raise NotImplementedError


class Expression(AST):
    def __init__(self):
        """Initialized every expression with a symbol to track its type"""
        self.symbol = TypeSymbol()


class FunctionDefinition(AST):
    def __init__(self, func_name: str, params: list[str], body: Expression):
        self.func_name = func_name
        self.params = params
        self.body = body


class FunctionCall(Expression):
    def __init__(self, func_expr: Expression, args: list[Expression]):
        super().__init__()
        self.func_expr = func_expr
        self.args = args


class IfExpr(Expression):
    def __init__(
        self, condition: Expression, then_expr: Expression, else_expr: Expression
    ):
        super().__init__()
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr


class LetExpr(Expression):
    def __init__(self, var: str, val: Expression, expr: Expression):
        # let var = val in expr
        super().__init__()
        self.var = var
        self.val = val
        self.expr = expr


class BinaryOp(Expression):
    def __init__(self, op: str, left: Expression, right: Expression):
        super().__init__()
        self.op = op
        self.left_expr = left
        self.right_expr = right


class IdExpr(Expression):
    """Special expression since its type comes from the symbol table"""

    def __init__(self, id: str):
        # Note: does not call super because its type comes from looking up the identifier in the scope
        self.id = id


class IntLiteral(Expression):
    """Integer literal"""

    def __init__(self, val: int):
        super().__init__()
        self._val = val


class FloatLiteral(Expression):
    """Float literal"""

    def __init__(self, val: float):
        super().__init__()
        self._val = val


class BoolLiteral(Expression):
    """Boolean literal"""

    def __init__(self, val: bool):
        super().__init__()
        self._val = val
