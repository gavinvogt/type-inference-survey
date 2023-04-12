"""
File: type_inference.py
Author: Gavin Vogt
This program performs type inference on an AST. Assumes that ID binding has
already taken place.
"""

from typing import Optional

from microml.parser import Parser
from type_unification import unify
from constructs import Type, TypeApplication, TypeVariable, TypeConstant, TypeList
from scope import Scope
from microml.ast import (
    AST,
    FunctionDefinition,
    FunctionCall,
    IfExpr,
    LetExpr,
    BinaryExpr,
    IdExpr,
    UnitExpr,
    IntLiteral,
    RealLiteral,
    BoolLiteral,
    Expression,
)

INT_TYPE = "int"
REAL_TYPE = "real"
BOOL_TYPE = "bool"
UNIT_TYPE = "unit"


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
            # NOTE: these parameters are curried like ((f a) b) c, rather than f(a, b, c)
            inside_function.create(param)
            inside_function.lookup(param).type = tvg.next()

        equations.extend(gen_type_eqs(ast.body, inside_function, tvg))

        param_types = [inside_function.lookup(param).type for param in ast.params]
        if len(param_types) == 0:
            param_types.append(TypeConstant(UNIT_TYPE))
        function_type = get_symbol(ast.body, inside_function).type
        for param_type in reversed(param_types):
            function_type = TypeApplication(param_type, function_type)
        equations.append(
            (
                scope.lookup(ast.func_name).type,
                function_type,
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
                equations.extend(gen_type_eqs(ast.arg, scope, tvg))
                # TODO: if FunctionCall uses args instead of arg
                # for arg in ast.args:
                #     equations.extend(gen_type_eqs(arg, scope, tvg))
                equations.append(
                    (
                        # t_func = t_args -> t_call
                        get_symbol(ast.func_expr).type,
                        TypeApplication(
                            get_symbol(ast.arg).type,
                            # [get_symbol(arg).type for arg in ast.args], # TODO: if args instead of arg
                            symbol.type,
                        ),
                    )
                )
            case BinaryExpr():
                equations.extend(gen_type_eqs(ast.left_expr, scope, tvg))
                equations.extend(gen_type_eqs(ast.right_expr, scope, tvg))

                if ast.op in {"==", "!=", "<", ">", "<=", ">="}:
                    equations.append((symbol.type, TypeConstant(BOOL_TYPE)))
                    equations.append(
                        (
                            get_symbol(ast.left_expr).type,
                            get_symbol(ast.right_expr).type,
                        )
                    )
                elif ast.op in {"+", "-", "*"}:
                    # int -> int -> int
                    equations.append((symbol.type, TypeConstant(INT_TYPE)))
                    equations.append(
                        (get_symbol(ast.left_expr).type, TypeConstant(INT_TYPE))
                    )
                    equations.append(
                        (get_symbol(ast.right_expr).type, TypeConstant(INT_TYPE))
                    )

                elif ast.op == "/":
                    # real -> real -> real
                    equations.append((symbol.type, TypeConstant(REAL_TYPE)))
                    equations.append(
                        (get_symbol(ast.left_expr).type, TypeConstant(REAL_TYPE))
                    )
                    equations.append(
                        (get_symbol(ast.right_expr).type, TypeConstant(REAL_TYPE))
                    )

                elif ast.op in {"and", "or"}:
                    equations.append((symbol.type, TypeConstant(BOOL_TYPE)))
                    equations.append(
                        (get_symbol(ast.left_expr).type, TypeConstant(BOOL_TYPE))
                    )
                    equations.append(
                        (get_symbol(ast.right_expr).type, TypeConstant(BOOL_TYPE))
                    )
            case UnitExpr():
                equations.append((symbol.type, TypeConstant(UNIT_TYPE)))
            case IntLiteral():
                equations.append((symbol.type, TypeConstant(INT_TYPE)))
            case RealLiteral():
                equations.append((symbol.type, TypeConstant(REAL_TYPE)))
            case BoolLiteral():
                equations.append((symbol.type, TypeConstant(BOOL_TYPE)))

    return equations


def type_infer(ast: AST):
    global_scope = Scope()
    # TODO: remove hardcoding of these "builtin" functions

    # hd: a[] -> a
    global_scope.create("hd")
    generic_var = TypeVariable("A")
    global_scope.lookup("hd").type = TypeApplication(TypeList(generic_var), generic_var)

    # null: a[] -> bool
    global_scope.create("null")
    generic_var = TypeVariable("B")
    global_scope.lookup("null").type = TypeApplication(
        TypeList(generic_var), TypeConstant(BOOL_TYPE)
    )

    # nil: () -> a[]
    global_scope.create("nil")
    generic_var = TypeVariable("C")
    global_scope.lookup("nil").type = TypeList(generic_var)

    # cons: (a, a[]) -> a[]
    global_scope.create("cons")
    generic_var = TypeVariable("D")
    global_scope.lookup("cons").type = TypeApplication(
        generic_var,
        TypeApplication(TypeList(generic_var), TypeList(generic_var)),
    )

    # tl: a[] -> a[]
    global_scope.create("tl")
    generic_var = TypeVariable("E")
    global_scope.lookup("tl").type = TypeApplication(
        TypeList(generic_var), TypeList(generic_var)
    )

    equations = gen_type_eqs(ast, global_scope, TypeVarGenerator())
    # for (t1, t2) in equations:
    #     print(t1, "=", t2)
    substitutions = unify(equations)

    for name, symbol in global_scope.symbols.items():
        if isinstance(symbol.type, TypeVariable):
            print(name, ":", substitutions[symbol.type.name])


def main():
    for file_name in ("basic.mml", "recursive.mml", "hof.mml"):
        p = Parser()
        asts = p.parse_file(f"tests/{file_name}")
        # asts = load_program("tests/test.json")
        for ast in asts:
            print(ast)
            type_infer(ast)
            # print("-" * 60 + "\n")
        print("-" * 60 + "\n")

    # f x = if x == 4 and 3 == 7 then x + 1 else 6
    # fact x = if x == 0 then 1 else x + fact(x + 1)
    # f x = x
    # f x = x + 1
    # higher_order_function (func, x) = if func(0) then x + 3 else 4


if __name__ == "__main__":
    main()
