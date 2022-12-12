"""
File: martelli_algorithm_1.py
Author: Gavin Vogt
This program implements Algorithm 1 as given by Martelli and Montanari in the
1982 paper "An Efficient Unification Algorithm"
"""


from terms import Term, Variable, Application
from util import occurs, substitute


class Equation:
    def __init__(self, t1: Term, t2: Term):
        self.left = t1
        self.right = t2

    def __repr__(self):
        return f"{self.left} = {self.right}"


def var_occurs_in_equations(var: Variable, equations: set[Equation]):
    """
    Checks if the given variable occurs somewhere in the set of equations
    var: Variable to search for
    equations: Set of equations to search
    """
    return any(occurs(var, eq.left) or occurs(var, eq.right) for eq in equations)


def unify(equations: set[Equation]):
    """
    Transforms the set of equations into an equivalent set of equations in solved form.
    equations: set of Equations
    """
    no_transformation: set[Equation] = set()
    while len(equations) > 0:
        eq = equations.pop()
        left = eq.left
        right = eq.right
        if not isinstance(left, Variable) and isinstance(right, Variable):
            # Case (a)
            # t = x
            # Rewrite as x = t
            equations.add(Equation(right, left))
        elif (
            isinstance(left, Variable) and isinstance(right, Variable) and left == right
        ):
            # Case (b)
            # x = x
            # Erase this equation
            pass
        elif not isinstance(left, Variable) and not isinstance(right, Variable):
            # Case (c)
            # t' = t"
            assert isinstance(left, Application)
            assert isinstance(right, Application)
            if left.name != right.name:
                raise Exception(f"Different root function symbols")
            elif left.arity() != right.arity():
                raise Exception(f"Different function arities")
            else:
                # Apply term reduction
                for arg1, arg2 in zip(left.args, right.args):
                    equations.add(Equation(arg1, arg2))
        elif isinstance(left, Variable) and var_occurs_in_equations(
            left, equations.union(no_transformation)
        ):
            # Case (d)
            # x = t
            # Variable x occurs somewhere else in the set of equations
            # t != x (don't need to check since x=x is already handled)
            if occurs(left, right):
                # Unification failure in occurs check
                raise Exception(f"{left} occurs in {right}")
            else:
                # Apply variable elimination
                for equation in equations:
                    # Apply the left -> right substitution to each side of the equation
                    equation.left = substitute(equation.left, left, right)
                    equation.right = substitute(equation.right, left, right)
                for equation in no_transformation:
                    # Apply the left -> right substitution to each side of the equation
                    equation.left = substitute(equation.left, left, right)
                    equation.right = substitute(equation.right, left, right)
                equations.add(eq)
        else:
            # None of the transformations (a-d) apply
            no_transformation.add(eq)

    return no_transformation


def main():
    # g(x2) = x1
    eq1 = Equation(Application("g", [Variable("x2")]), Variable("x1"))
    eq2 = Equation(
        # f(x1, h(x1), x2)
        Application(
            "f", [Variable("x1"), Application("h", [Variable("x1")]), Variable("x2")]
        ),
        # f(g(x3), x4, x3)
        Application(
            "f", [Application("g", [Variable("x3")]), Variable("x4"), Variable("x3")]
        ),
    )
    equations = {eq1, eq2}
    mgu = unify(equations)
    print("Most general unifier:")
    for equation in sorted(mgu, key=lambda eq: eq.left.name):
        print(equation)


if __name__ == "__main__":
    main()
