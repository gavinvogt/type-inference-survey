"""
File: type_unification.py
Author: Gavin Vogt
This program performs type unification on a set of terms
"""

from constructs import Type, TypeApplication, TypeVariable, TypeConstant, TypeList


def occurs(var: TypeVariable, term: Type) -> bool:
    """Checks if the variable occurs in the term"""
    if var == term:
        return True
    elif isinstance(term, TypeVariable):
        return False
    elif isinstance(term, TypeApplication):
        return any(occurs(var, arg) for arg in term.args)
    elif isinstance(term, TypeList):
        return occurs(var, term.el_type)
    else:
        return False


def apply_substitution(term: Type, x: TypeVariable, t: Type) -> Type:
    """Applies a substitution of x -> t to the given term"""
    if isinstance(term, TypeApplication):
        return TypeApplication(
            [apply_substitution(arg, x, t) for arg in term.args],
            apply_substitution(term._ret, x, t),
        )
    elif isinstance(term, TypeList):
        return TypeList(apply_substitution(term.el_type, x, t))
    elif isinstance(term, TypeVariable) and term.name == x.name:
        return t
    else:
        return term


def unify(equations: list[tuple[Type, Type]]):
    substitutions: dict[str, Type] = {}
    while len(equations) > 0:
        t1, t2 = equations.pop(0)
        if t1 == t2:
            # Delete tautology like X=X (do nothing)
            pass
        elif isinstance(t1, TypeConstant) and isinstance(t2, TypeConstant):
            # Here we check that type constants are compatible
            # (already know that t1 != t2 from above `if` statement)
            raise Exception(f"Incompatible types {t1} and {t2}")
        elif isinstance(t1, TypeApplication) and isinstance(t2, TypeApplication):
            if len(t1.args) == len(t2.args):
                # Decompose two function types
                decomposed_type_eqs: list[tuple[Type, Type]] = []
                for arg1, arg2 in zip(t1.args, t2.args):
                    decomposed_type_eqs.append((arg1, arg2))
                decomposed_type_eqs.append((t1._ret, t2._ret))
                equations = [*decomposed_type_eqs, *equations]
            else:
                # Conflict (type unification fails)
                raise Exception("Conflict: argument count mismatch")
        elif isinstance(t1, TypeList) and isinstance(t2, TypeList):
            # Decompose two list types
            equations.insert(0, (t1.el_type, t2.el_type))
        elif isinstance(t2, TypeVariable) and not isinstance(t1, TypeVariable):
            # Swap so the type variable is first (Orient rule)
            equations.insert(0, (t2, t1))
        elif isinstance(t1, TypeVariable):
            # Eliminate rule
            if occurs(t1, t2):
                raise Exception("Error: circular use of variable")
            else:
                equations = [
                    (
                        apply_substitution(term1, t1, t2),
                        apply_substitution(term2, t1, t2),
                    )
                    for (term1, term2) in equations
                ]

                # Apply the new substitution to the old substitutions
                for name in substitutions.keys():
                    substitutions[name] = apply_substitution(
                        substitutions[name], t1, t2
                    )

                substitutions[t1.name] = t2
        else:
            raise Exception(f"Failed to unify term {t1} = {t2}")

    return substitutions


def main():
    # Code:
    """
    fn isZero => if isZero 1 then 2 else 3
    """
    # Note: anonymous function that takes takes function `isZero` as an argument

    unify([(TypeVariable("X"), TypeList(TypeConstant("Int")))])

    # Constraint set:
    """
    t1 = t5 -> t4       # t4 is the result of isZero(1)
    t5 = int            # 1 has type int
    t4 = bool           # t4 must be bool since used as condition to `if`
    t6 = int            # 2 has type int
    t7 = int            # 3 has type int
    t6 = t3             # Return type of `if` must match expr1
    t7 = t3             # Return type of `if` must match expr2
    t2 = t1 -> t3       # Type of overall expression is type deduced from `isZero` => result of `if`
    """

    # Unify the expression
    unify(
        [
            (
                TypeVariable("t1"),
                TypeApplication([TypeVariable("t5")], TypeVariable("t4")),
            ),
            (TypeVariable("t5"), TypeConstant("int")),
            (TypeVariable("t4"), TypeConstant("bool")),
            (TypeVariable("t6"), TypeConstant("int")),
            (TypeVariable("t7"), TypeConstant("int")),
            (TypeVariable("t6"), TypeVariable("t3")),
            (TypeVariable("t7"), TypeVariable("t3")),
            (
                TypeVariable("t2"),
                TypeApplication([TypeVariable("t1")], TypeVariable("t3")),
            ),
        ]
    )

    print("------- (should error)")
    unify(
        [
            (TypeVariable("t1"), TypeConstant("int")),
            (TypeVariable("t1"), TypeConstant("bool")),
        ]
    )

    print("----")
    """
    FunctionDefinition(
        Id("f"),   # name
        Id("x"),   # argument
        Id("x"),   # Just returns x
    )

    t1 = t2 -> t2
    """
    # f(x) = x should have generic types
    unify(
        [
            (
                TypeVariable("t1"),
                TypeApplication([TypeVariable("t2")], TypeVariable("t2")),
            )
        ]
    )


if __name__ == "__main__":
    main()
