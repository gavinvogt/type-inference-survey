"""
Author: Gavin Vogt
File: ast.py
This program defines the classes for an AST
"""

from typing import Any, Optional
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

    def __repr__(self):
        return f"{self.__class__.__name__}({self._type})"


class AST:
    """Represents an abstract syntax tree"""

    def __init__(self):
        # TODO: do I need this??
        self.type: Optional[Type] = None


class Expression(AST):
    def __init__(self):
        """Initialized every expression with a symbol to track its type"""
        self.symbol = TypeSymbol()


class FunctionDefinition(AST):
    def __init__(self, func_name: str, params: list[str], body: Expression):
        # NOTE: parameters are in curried form
        # f x y z = FunctionDefinition("f", ["x", "y", "z"], ...)
        self.func_name = func_name
        self.params = params
        self.body = body

    def __repr__(self):
        return " -> ".join(self.params) + f" -> {self.body}"


class CallExpr(Expression):
    def __init__(self, func_expr: Expression, arg: Expression):
        super().__init__()
        self.func_expr = func_expr
        self.arg = arg

    def __repr__(self):
        return f"{self.__class__.__name__}({self.func_expr}, {self.arg})"


class IfExpr(Expression):
    def __init__(
        self, condition: Expression, then_expr: Expression, else_expr: Expression
    ):
        super().__init__()
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr

    def __repr__(self):
        return (
            f"( if ({self.condition}) then ({self.then_expr}) else ({self.else_expr}) )"
        )


class LetExpr(Expression):
    def __init__(self, var: str, val: Expression, expr: Expression):
        # let var = val in expr
        super().__init__()
        self.var = var
        self.val = val
        self.expr = expr

    def __repr__(self):
        return f"( let {self.var} = ({self.val}) in ({self.expr}) )"


class FnExpr(Expression):
    def __init__(self, params: list[str], body: Expression):
        # fn params => body
        super().__init__()
        self.params = params
        self.body = body

    def __repr__(self):
        return f"( fn ({' '.join(self.params)}) => ({self.body}) )"


class BinaryExpr(Expression):
    def __init__(self, op: str, left: Expression, right: Expression):
        super().__init__()
        self.op = op
        self.left_expr = left
        self.right_expr = right

    def __repr__(self):
        return f"( {self.left_expr} {self.op} {self.right_expr} )"


class UnaryExpr(Expression):
    def __init__(self, op: str, expr: Expression):
        super().__init__()
        self.op = op
        self.expr = expr

    def __repr__(self):
        return f"( {self.op} {self.expr} )"


class UnitExpr(Expression):
    """Represents the "unit", or ()"""

    def __init__(self):
        super().__init__()


class IdExpr(Expression):
    """Special expression since its type comes from the symbol table"""

    def __init__(self, id: str):
        # Note: does not call super because its type comes from looking up the identifier in the scope
        self.id = id

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id})"


class Literal(Expression):
    def __init__(self, val: Any):
        super().__init__()
        self._val = val

    def __repr__(self):
        return str(self._val)


class IntLiteral(Literal):
    """Integer literal"""

    def __init__(self, val: int):
        super().__init__(val)


class RealLiteral(Literal):
    """Real literal"""

    def __init__(self, val: float):
        super().__init__(val)


class BoolLiteral(Literal):
    """Boolean literal"""

    def __init__(self, val: bool):
        super().__init__(val)
