"""
File: type_inference.py
Author: Gavin Vogt
This program performs type inference on an AST. Assumes that ID binding has
already taken place.
"""

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
    UnaryExpr,
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


class TypeEquationGenerator:
    def __init__(self, tvg: TypeVarGenerator):
        self._tvg = tvg

    def gen_type_eqs(self, ast: AST, scope: Scope) -> list[tuple[Type, Type]]:
        """
        Generates the type equations for the given AST.

        Parameters
        ----------
        ast : `AST`
            AST node to generate equations for
        scope : `Scope`
            Parent scope the AST would be executed in
        """
        if isinstance(ast, FunctionDefinition):
            return self._function_definition(ast, scope)
        elif isinstance(ast, Expression):
            return self._expression(ast, scope)
        else:
            raise Exception(f"Unexpected AST type {type(ast)}")

    def _function_definition(
        self, ast: FunctionDefinition, scope: Scope
    ) -> list[tuple[Type, Type]]:
        """
        Generates the type equations for the given function definition.

        Parameters
        ----------
        ast : `FunctionDefinition`
            Function definition AST node
        scope : `Scope`
            Parent scope the function was defined in (the context)
        """
        # Create the function in the main scope
        equations: list[tuple[Type, Type]] = []
        scope.create(ast.func_name)
        ast.symbol = scope.lookup(ast.func_name)
        ast.symbol.type = self._tvg.next()

        # Create a child scope for the function body and add the parameters
        inside_function = Scope(scope)
        for param in ast.params:
            # NOTE: these parameters are curried like ((f a) b) c, rather than f(a, b, c)
            inside_function.create(param)
            inside_function.lookup(param).type = self._tvg.next()

        # Type equations for the body
        equations.extend(self._expression(ast.body, inside_function))

        # Overall function type
        param_types = [inside_function.lookup(param).type for param in ast.params]
        if len(param_types) == 0:
            param_types.append(TypeConstant(UNIT_TYPE))
        function_type = self._get_symbol(ast.body, inside_function).type  # Return type
        for param_type in reversed(param_types):
            # param1 -> param2 -> ... -> return type
            function_type = TypeApplication(param_type, function_type)
        equations.append(
            (
                scope.lookup(ast.func_name).type,
                function_type,
            )
        )
        return equations

    def _expression(self, ast: Expression, scope: Scope) -> list[tuple[Type, Type]]:
        """
        Generates the type equations for the given expression.

        Parameters
        ----------
        ast : `Expression`
            Expression AST node
        scope : `Scope`
            Parent scope the expression would be executed under (the context)
        """
        if isinstance(ast, IdExpr):
            ast.symbol = self._get_symbol(ast, scope)
        else:
            # Create the type variable for this expression
            ast.symbol.type = self._tvg.next()
        symbol = self._get_symbol(ast, scope)

        match ast:
            case IfExpr():
                return self._if_expr(ast, scope)
            case LetExpr():
                return self._let_expr(ast, scope)
            case IdExpr():
                # TODO
                return []
            case CallExpr():
                return self._call_expr(ast, scope)
            case FnExpr():
                return self._fn_expr(ast, scope)
            case BinaryExpr():
                return self._binary_expr(ast, scope)
            case UnaryExpr():
                return self._unary_expr(ast, scope)
            case UnitExpr():
                return [(symbol.type, TypeConstant(UNIT_TYPE))]
            case IntLiteral():
                return [(symbol.type, TypeConstant(INT_TYPE))]
            case RealLiteral():
                return [(symbol.type, TypeConstant(REAL_TYPE))]
            case BoolLiteral():
                return [(symbol.type, TypeConstant(BOOL_TYPE))]
            case _:
                raise Exception(f"Unexpected Expression type {type(ast)}")

    def _if_expr(self, ast: IfExpr, scope: Scope) -> list[tuple[Type, Type]]:
        """
        Generates the type equations for the given if expression.

        Parameters
        ----------
        ast : `IfExpr`
            If expression AST node
        scope : `Scope`
            Parent scope the expression would be executed under (the context)
        """
        equations: list[tuple[Type, Type]] = []
        symbol = self._get_symbol(ast, scope)

        for expr in (ast.condition, ast.then_expr, ast.else_expr):
            equations.extend(self._expression(expr, scope))
        equations.append(
            (
                self._get_symbol(ast.condition, scope).type,
                TypeConstant(BOOL_TYPE),
            )
        )
        equations.append((symbol.type, self._get_symbol(ast.then_expr, scope).type))
        equations.append((symbol.type, self._get_symbol(ast.else_expr, scope).type))
        return equations

    def _let_expr(self, ast: LetExpr, scope: Scope) -> list[tuple[Type, Type]]:
        """
        Generates the type equations for the given let expression.

        Parameters
        ----------
        ast : `LetExpr`
            Let expression AST node
        scope : `Scope`
            Parent scope the expression would be executed under (the context)
        """
        equations: list[tuple[Type, Type]] = []
        symbol = self._get_symbol(ast, scope)

        inside_let = Scope(scope)
        inside_let.create(ast.var)
        inside_let.lookup(ast.var).type = self._tvg.next()
        # Use the child scope to allow recursive use of the let-defined variable
        equations.extend(self._expression(ast.val, inside_let))
        equations.extend(self._expression(ast.expr, inside_let))

        # t_var = t_val
        equations.append(
            (
                inside_let.lookup(ast.var).type,
                self._get_symbol(ast.val, scope).type,
            )
        )
        # Overall expression matches the type of expr
        expr_type = self._get_symbol(ast.expr, inside_let).type
        equations.append((symbol.type, expr_type))
        return equations

    def _call_expr(self, ast: CallExpr, scope: Scope) -> list[tuple[Type, Type]]:
        """
        Generates the type equations for the given call expression.

        Parameters
        ----------
        ast : `CallExpr`
            Call expression AST node
        scope : `Scope`
            Parent scope the expression would be executed under (the context)
        """
        equations: list[tuple[Type, Type]] = []
        symbol = self._get_symbol(ast, scope)

        equations.extend(self._expression(ast.func_expr, scope))
        equations.extend(self._expression(ast.arg, scope))
        equations.append(
            (
                # t_func = t_arg -> t_call
                self._get_symbol(ast.func_expr, scope).type,
                TypeApplication(
                    self._get_symbol(ast.arg, scope).type,
                    symbol.type,
                ),
            )
        )
        return equations

    def _fn_expr(self, ast: FnExpr, scope: Scope) -> list[tuple[Type, Type]]:
        """
        Generates the type equations for the given anonymous function expression.

        Parameters
        ----------
        ast : `FnExpr`
            Anonymous function expression AST node
        scope : `Scope`
            Parent scope the expression would be executed under (the context)
        """
        equations: list[tuple[Type, Type]] = []
        symbol = self._get_symbol(ast, scope)

        inside_fn = Scope(scope)
        for param in ast.params:
            # NOTE: these parameters are curried like ((f a) b) c, rather than f(a, b, c)
            inside_fn.create(param)
            inside_fn.lookup(param).type = self._tvg.next()
        equations.extend(self._expression(ast.body, inside_fn))
        param_types = [inside_fn.lookup(param).type for param in ast.params]
        if len(param_types) == 0:
            param_types.append(TypeConstant(UNIT_TYPE))
        fn_type = self._get_symbol(ast.body, inside_fn).type
        for param_type in reversed(param_types):
            fn_type = TypeApplication(param_type, fn_type)
        equations.append((symbol.type, fn_type))
        return equations

    def _binary_expr(self, ast: BinaryExpr, scope: Scope) -> list[tuple[Type, Type]]:
        """
        Generates the type equations for the given binary expression.

        Parameters
        ----------
        ast : `BinaryExpr`
            Binary expression AST node
        scope : `Scope`
            Parent scope the expression would be executed under (the context)
        """
        equations: list[tuple[Type, Type]] = []
        symbol = self._get_symbol(ast, scope)

        equations.extend(self._expression(ast.left_expr, scope))
        equations.extend(self._expression(ast.right_expr, scope))

        if ast.op in {"==", "!=", "<", ">", "<=", ">="}:
            equations.append((symbol.type, TypeConstant(BOOL_TYPE)))
            equations.append(
                (
                    self._get_symbol(ast.left_expr, scope).type,
                    self._get_symbol(ast.right_expr, scope).type,
                )
            )
        elif ast.op in {"+", "-", "*"}:
            # int -> int -> int
            equations.append((symbol.type, TypeConstant(INT_TYPE)))
            equations.append(
                (
                    self._get_symbol(ast.left_expr, scope).type,
                    TypeConstant(INT_TYPE),
                )
            )
            equations.append(
                (
                    self._get_symbol(ast.right_expr, scope).type,
                    TypeConstant(INT_TYPE),
                )
            )

        elif ast.op == "/":
            # real -> real -> real
            equations.append((symbol.type, TypeConstant(REAL_TYPE)))
            equations.append(
                (
                    self._get_symbol(ast.left_expr, scope).type,
                    TypeConstant(REAL_TYPE),
                )
            )
            equations.append(
                (
                    self._get_symbol(ast.right_expr, scope).type,
                    TypeConstant(REAL_TYPE),
                )
            )

        elif ast.op in {"and", "or"}:
            # bool -> bool -> bool
            equations.append((symbol.type, TypeConstant(BOOL_TYPE)))
            equations.append(
                (
                    self._get_symbol(ast.left_expr, scope).type,
                    TypeConstant(BOOL_TYPE),
                )
            )
            equations.append(
                (
                    self._get_symbol(ast.right_expr, scope).type,
                    TypeConstant(BOOL_TYPE),
                )
            )
        else:
            raise Exception(f"Unrecognized binary operator {ast.op}")

        return equations

    def _unary_expr(self, ast: UnaryExpr, scope: Scope) -> list[tuple[Type, Type]]:
        """
        Generates the type equations for the given unary expression.

        Parameters
        ----------
        ast : `UnaryExpr`
            Unary expression AST node
        scope : `Scope`
            Parent scope the expression would be executed under (the context)
        """
        equations = self._expression(ast.expr, scope)
        symbol = self._get_symbol(ast, scope)
        if ast.op == "-":
            # int -> int
            equations.append((symbol.type, TypeConstant(INT_TYPE)))
            equations.append(
                (
                    self._get_symbol(ast.expr, scope).type,
                    TypeConstant(INT_TYPE),
                )
            )
        elif ast.op == "not":
            # bool -> bool
            equations.append((symbol.type, TypeConstant(BOOL_TYPE)))
            equations.append(
                (
                    self._get_symbol(ast.expr, scope).type,
                    TypeConstant(BOOL_TYPE),
                )
            )
        else:
            raise Exception(f"Unrecognized unary operator {ast.op}")

        return equations

    def _get_symbol(self, ast: Expression, scope: Scope):
        """
        Gets the type symbol for the given AST node.

        Parameters
        ----------
        ast : `Expression`
            Expression AST node
        scope : `Scope`
            Parent scope the expression would be executed under (the context)
        """
        if isinstance(ast, IdExpr):
            return scope.lookup(ast.id)
        else:
            return ast.symbol


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
    type_eq_generator = TypeEquationGenerator(tvg)

    equations = type_eq_generator.gen_type_eqs(ast, scope)
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


def type_infer_code(asts: list[FunctionDefinition]):
    # Set up the scope
    tvg = TypeVarGenerator()
    global_scope = create_global_scope(tvg)

    # Infer the type of each function
    for ast in asts:
        print(ast)
        type_infer(ast, global_scope, tvg)


def type_infer_program(file_name: str):
    # Parse the program
    p = Parser()
    asts = p.parse_file(f"tests/{file_name}")

    # Type infer the program
    type_infer_code(asts)


def main():
    for file_name in ("basic.mml", "recursive.mml", "hof.mml", "lists.mml", "sort.mml"):
        type_infer_program(file_name)
        print("-" * 60 + "\n")


if __name__ == "__main__":
    main()
