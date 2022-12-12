"""
File: robinson_algorithm.py
Author: Gavin Vogt
This program crudely implements the basic algorithm given by Robinson in the
1965 paper "A Machine-Oriented Logic Based on the Resolution Principle"
"""


from terms import Term, Variable, Application, Constant
from util import occurs, substitute, apply_substitution


def substitution_all(terms: set[Term], substitution: dict[str, Term]):
    """Applies the given substitution to every term in the set"""
    return {apply_substitution(term, substitution) for term in terms}


def disagreement_set(terms: set[Term]) -> set[Term]:
    """Calculates the disagreement set of the terms"""
    if len(terms) <= 1:
        # Nothing could disagree
        return set()
    elif any(isinstance(term, Variable) for term in terms):
        # Disagreement at variable x = t1 = t2 = ...
        # (we know there are at least 2 unequal terms)
        return terms

    # Every term is a function application
    t = next(iter(terms))  # Get the name and arity from one of the functions
    func_name = t.name
    arity = t.arity()
    assert all((term.name == func_name and term.arity() == arity) for term in terms)

    # Check each argument in the application for disagreement
    for i in range(arity):
        disagreement = disagreement_set({term.args[i] for term in terms})
        if len(disagreement) != 0:
            return disagreement

    # No disagreement found (should never reach this point)
    return set()


def lexical_order(terms: set[Term]):
    """Returns the lexical ordering of the terms (variables first, then applications)"""
    return sorted(terms, key=lambda term: -1 if isinstance(term, Variable) else 1)


def unify(terms: set[Term]):
    # Step 1: empty substitution
    substitution: dict[str, Term] = {}

    while True:
        # Step 2: Apply the substitution to every term in the set
        if len(substitution_all(terms, substitution)) == 1:
            # Substitution turned set of terms into a singleton (unified them all)
            return substitution

        # Step 3:
        disagreement = lexical_order(
            disagreement_set(substitution_all(terms, substitution))
        )
        s = disagreement[0]
        t = disagreement[1]
        if isinstance(s, Variable) and not occurs(s, t):
            for var, term in substitution.items():
                substitution[var] = substitute(term, s, t)
            substitution[s.name] = t
        else:
            raise Exception("Not unifiable")


def main():
    # x1
    # f(x2, g(x4), x3, x5)
    # f(x3, g(a),  b,  x6)
    terms = {
        Variable("x1"),
        Application(
            "f",
            [
                Variable("x2"),
                Application("g", [Variable("x4")]),
                Variable("x3"),
                Variable("x5"),
            ],
        ),
        Application(
            "f",
            [
                Variable("x3"),
                Application("g", [Constant("a")]),
                Constant("b"),
                Variable("x6"),
            ],
        ),
    }

    # f( x1,  h(x1), x2, g(x2))"
    # f(g(x3), x4,   x3,  x1)"
    terms2 = {
        Application(
            "f",
            [
                Variable("x1"),
                Application("h", [Variable("x1")]),
                Variable("x2"),
                Application("g", [Variable("x2")]),
            ],
        ),
        Application(
            "f",
            [
                Application("g", [Variable("x3")]),
                Variable("x4"),
                Variable("x3"),
                Variable("x1"),
            ],
        ),
    }

    print("EXAMPLE 1:")
    substitution = unify(terms)
    for var, term in substitution.items():
        print(var, "=", term)

    print("-" * 60)
    print("EXAMPLE 2:")
    substitution = unify(terms2)
    for var, term in substitution.items():
        print(var, "=", term)


if __name__ == "__main__":
    main()
