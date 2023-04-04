"""
File: type_inference.py
Author: Gavin Vogt
This program performs type inference on an AST. Assumes that ID binding has
already taken place.
"""

from typing import Optional, Union
from parser import load_program
from type_unification import unify
from ast import (
    AST,
    FunctionDefinition,
    FunctionCall,
    IfExpr,
    LetExpr,
    BinaryOp,
    IdExpr,
    IntLiteral,
    FloatLiteral,
    BoolLiteral,
    TypeSymbol,
    Expression,
)
from constructs import Type, TypeApplication, TypeVariable, TypeConstant, TypeList

INT_TYPE = "Int"
FLOAT_TYPE = "Float"
BOOL_TYPE = "Bool"


class Scope:
    def __init__(self, parent: Union["Scope", None] = None):
        self._parent = parent
        self._symbols: dict[str, TypeSymbol] = {}

    @property
    def symbols(self):
        """Readonly symbols dict"""
        return self._symbols

    def create(self, id: str):
        """Creates the given ID in the symbol table and gives it a type symbol"""
        if id in self._symbols:
            raise Exception(f"Identifier {id} already exists in scope")
        self._symbols[id] = TypeSymbol()

    def lookup(self, id: str) -> TypeSymbol:
        """Searches for the given ID in the scope"""
        if id in self._symbols:
            return self._symbols[id]
        elif self._parent is not None:
            return self._parent.lookup(id)
        else:
            raise Exception(f"{id} not found")


class TypeVarGenerator:
    """Helper class for generating new, unique type variables"""

    def __init__(self):
        self._n = 0

    def next(self):
        """Gets the next type variable"""
        n = self._n
        self._n += 1
        return TypeVariable(f"t{n}")


def gen_type_eqs(ast: AST, scope: Scope, tvg: TypeVarGenerator):
    """Walks the AST to decorate every ID with a type, and create type equations
    for all the IDs and expressions"""

    def get_symbol(ast: Expression, s: Optional[Scope] = None):
        if s is None:
            s = scope
        if isinstance(ast, IdExpr):
            return s.lookup(ast.id)
        else:
            return ast.symbol

    equations: list[tuple[Type, Type]] = []
    if isinstance(ast, FunctionDefinition):
        scope.create(ast.func_name)
        scope.lookup(ast.func_name).type = tvg.next()

        inside_function = Scope(scope)
        for param in ast.params:
            inside_function.create(param)
            inside_function.lookup(param).type = tvg.next()

        equations.extend(gen_type_eqs(ast.body, inside_function, tvg))
        equations.append(
            (
                scope.lookup(ast.func_name).type,
                TypeApplication(
                    [inside_function.lookup(param).type for param in ast.params],
                    get_symbol(ast.body, inside_function).type,
                ),
            )
        )
    elif isinstance(ast, Expression):
        if not isinstance(ast, IdExpr):
            # Create the type variable for this expression
            ast.symbol.type = tvg.next()
        symbol = get_symbol(ast)

        match ast:
            case IfExpr():
                for expr in (ast.condition, ast.then_expr, ast.else_expr):
                    equations.extend(gen_type_eqs(expr, scope, tvg))
                equations.append(
                    (get_symbol(ast.condition).type, TypeConstant(BOOL_TYPE))
                )
                equations.append((symbol.type, get_symbol(ast.then_expr).type))
                equations.append((symbol.type, get_symbol(ast.else_expr).type))
            case LetExpr():
                inside_let = Scope(scope)
                inside_let.create(ast.var)
                inside_let.lookup(ast.var).type = tvg.next()
                equations.extend(gen_type_eqs(ast.val, scope, tvg))
                equations.extend(gen_type_eqs(ast.expr, inside_let, tvg))

                # let var = val : type of var must match type of val
                equations.append(
                    (inside_let.lookup(ast.var).type, get_symbol(ast.val).type)
                )
                # Overall expression matches the type of expr
                equations.append((symbol.type, get_symbol(ast.expr).type))
            case FunctionCall():
                equations.extend(gen_type_eqs(ast.func_expr, scope, tvg))
                for arg in ast.args:
                    equations.extend(gen_type_eqs(arg, scope, tvg))
                equations.append(
                    (
                        # t_func = t_args -> t_call
                        get_symbol(ast.func_expr).type,
                        TypeApplication(
                            [get_symbol(arg).type for arg in ast.args],
                            symbol.type,
                        ),
                    )
                )
            case BinaryOp():
                equations.extend(gen_type_eqs(ast.left_expr, scope, tvg))
                equations.extend(gen_type_eqs(ast.right_expr, scope, tvg))

                if ast.op == "==":
                    equations.append((symbol.type, TypeConstant(BOOL_TYPE)))
                    equations.append(
                        (
                            get_symbol(ast.left_expr).type,
                            get_symbol(ast.right_expr).type,
                        )
                    )
                elif ast.op == "+":
                    equations.append((symbol.type, TypeConstant(INT_TYPE)))
                    equations.append(
                        (get_symbol(ast.left_expr).type, TypeConstant(INT_TYPE))
                    )
                    equations.append(
                        (get_symbol(ast.right_expr).type, TypeConstant(INT_TYPE))
                    )

                elif ast.op == "and":
                    equations.append((symbol.type, TypeConstant(BOOL_TYPE)))
                    equations.append(
                        (get_symbol(ast.left_expr).type, TypeConstant(BOOL_TYPE))
                    )
                    equations.append(
                        (get_symbol(ast.right_expr).type, TypeConstant(BOOL_TYPE))
                    )
            case IntLiteral():
                equations.append((symbol.type, TypeConstant(INT_TYPE)))
            case FloatLiteral():
                equations.append((symbol.type, TypeConstant(FLOAT_TYPE)))
            case BoolLiteral():
                equations.append((symbol.type, TypeConstant(BOOL_TYPE)))

    return equations


def type_infer(ast: AST):
    global_scope = Scope()
    # TODO: remove hardcoding of these "builtin" functions

    # hd: a[] -> a
    global_scope.create("hd")
    generic_var = TypeVariable("A")
    global_scope.lookup("hd").type = TypeApplication(
        [TypeList(generic_var)], generic_var
    )

    # null: a[] -> bool
    global_scope.create("null")
    generic_var = TypeVariable("B")
    global_scope.lookup("null").type = TypeApplication(
        [TypeList(generic_var)], TypeConstant(BOOL_TYPE)
    )

    # nil: () -> a[]
    global_scope.create("nil")
    generic_var = TypeVariable("C")
    global_scope.lookup("nil").type = TypeApplication([], TypeList(generic_var))

    # cons: (a, a[]) -> a[]
    global_scope.create("cons")
    generic_var = TypeVariable("D")
    global_scope.lookup("cons").type = TypeApplication(
        [generic_var, TypeList(generic_var)],
        TypeList(generic_var),
    )

    # tl: a[] -> a[]
    global_scope.create("tl")
    generic_var = TypeVariable("E")
    global_scope.lookup("tl").type = TypeApplication(
        [TypeList(generic_var)], TypeList(generic_var)
    )

    equations = gen_type_eqs(ast, global_scope, TypeVarGenerator())
    for (t1, t2) in equations:
        print(t1, "=", t2)
    substitutions = unify(equations)

    for name, symbol in global_scope.symbols.items():
        if isinstance(symbol.type, TypeVariable):
            print(name, ":", substitutions[symbol.type.name])


def main():
    asts = load_program("tests/test.json")
    for ast in asts:
        type_infer(ast)
        print("-" * 60 + "\n\n")

    # f x = if x == 4 and 3 == 7 then x + 1 else 6
    # fact x = if x == 0 then 1 else x + fact(x + 1)
    # f x = x
    # f x = x + 1
    # higher_order_function (func, x) = if func(0) then x + 3 else 4


if __name__ == "__main__":
    main()
