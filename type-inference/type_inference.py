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
    CallExpr,
    IfExpr,
    LetExpr,
    FnExpr,
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

    # print("\n-------- SCOPE -----------")
    # print(scope)
    # print("--------------------------")

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
        fn_type = get_symbol(ast.body, inside_function).type
        for param_type in reversed(param_types):
            fn_type = TypeApplication(param_type, fn_type)
        equations.append(
            (
                scope.lookup(ast.func_name).type,
                fn_type,
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
                # Use the child scope to allow recursive use of the let-defined variable
                equations.extend(gen_type_eqs(ast.val, inside_let, tvg))
                equations.extend(gen_type_eqs(ast.expr, inside_let, tvg))

                # let var = val : type of var must match type of val
                equations.append(
                    (inside_let.lookup(ast.var).type, get_symbol(ast.val).type)
                )
                # Overall expression matches the type of expr
                equations.append((symbol.type, get_symbol(ast.expr).type))
            case CallExpr():
                equations.extend(gen_type_eqs(ast.func_expr, scope, tvg))
                equations.extend(gen_type_eqs(ast.arg, scope, tvg))
                equations.append(
                    (
                        # t_func = t_arg -> t_call
                        get_symbol(ast.func_expr).type,
                        TypeApplication(
                            get_symbol(ast.arg).type,
                            symbol.type,
                        ),
                    )
                )
            case FnExpr():
                inside_fn = Scope(scope)
                for param in ast.params:
                    # NOTE: these parameters are curried like ((f a) b) c, rather than f(a, b, c)
                    inside_fn.create(param)
                    inside_fn.lookup(param).type = tvg.next()
                equations.extend(gen_type_eqs(ast.body, inside_fn, tvg))
                param_types = [inside_fn.lookup(param).type for param in ast.params]
                if len(param_types) == 0:
                    param_types.append(TypeConstant(UNIT_TYPE))
                fn_type = get_symbol(ast.body, inside_fn).type
                for param_type in reversed(param_types):
                    fn_type = TypeApplication(param_type, fn_type)
                equations.append((symbol.type, fn_type))
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


def create_global_scope(tvg: TypeVarGenerator) -> Scope:
    """
    Creates a global scope for a Micro-ML program, containing certain built-in functions
    """
    scope = Scope()

    # hd: 'a[] -> 'a
    scope.create("hd")
    generic_var = tvg.next()
    scope.lookup("hd").type = TypeApplication(TypeList(generic_var), generic_var)

    # null: 'a[] -> bool
    scope.create("null")
    generic_var = tvg.next()
    scope.lookup("null").type = TypeApplication(
        TypeList(generic_var), TypeConstant(BOOL_TYPE)
    )

    # nil: 'a[]
    scope.create("nil")
    generic_var = tvg.next()
    scope.lookup("nil").type = TypeList(generic_var)

    # cons: 'a -> 'a[] -> 'a[]
    scope.create("cons")
    generic_var = tvg.next()
    scope.lookup("cons").type = TypeApplication(
        generic_var,
        TypeApplication(TypeList(generic_var), TypeList(generic_var)),
    )

    # tl: 'a[] -> 'a[]
    scope.create("tl")
    generic_var = tvg.next()
    scope.lookup("tl").type = TypeApplication(
        TypeList(generic_var), TypeList(generic_var)
    )

    return scope


def type_infer(ast: AST, scope: Scope, tvg: TypeVarGenerator):
    # Generate and solve the type equations
    equations = gen_type_eqs(ast, scope, tvg)
    # for (t1, t2) in equations:
    #     print(t1, "=", t2)
    substitutions = unify(equations)

    if isinstance(ast, FunctionDefinition):
        # Update the type of the function in the scope using the substitution set
        symbol = scope.lookup(ast.func_name)
        assert isinstance(symbol.type, TypeVariable)
        symbol.type = substitutions[symbol.type.name]

        # Display the function's type
        print(ast.func_name, ":", symbol.type.type_str())

    # for name, symbol in scope.symbols.items():
    #     print(name, ":", symbol)
    #     if isinstance(symbol.type, TypeVariable):
    #         print(name, ":", substitutions[symbol.type.name])


def type_infer_program(file_name: str):
    # Parse the program
    p = Parser()
    asts = p.parse_file(f"tests/{file_name}")

    # Type infer the program
    tvg = TypeVarGenerator()
    global_scope = create_global_scope(tvg)
    for ast in asts:
        print(ast)
        type_infer(ast, global_scope, tvg)


def main():
    for file_name in ("basic.mml", "recursive.mml", "hof.mml", "lists.mml"):
        type_infer_program(file_name)
        print("-" * 60 + "\n")

    # f x = if x == 4 and 3 == 7 then x + 1 else 6
    # f x = x
    # f x = x + 1
    # higher_order_function (func, x) = if func(0) then x + 3 else 4


if __name__ == "__main__":
    main()
