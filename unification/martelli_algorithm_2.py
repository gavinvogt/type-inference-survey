"""
File: martelli_algorithm_2.py
Author: Gavin Vogt
This program implements Algorithm 2 as given by Martelli and Montanari in the
1982 paper "An Efficient Unification Algorithm"
"""

from typing import Optional, TypeVar, Generic
from terms import Term, Variable, Application
from util import apply_substitution, term_vars, UnionFind
from parse_term import parse_term


T = TypeVar("T", contravariant=True)


class Multiset(Generic[T]):
    def __init__(self, terms: Optional[list[T]] = None):
        if terms is None:
            self.terms = []
        else:
            self.terms = terms

    def __repr__(self):
        terms = ", ".join(str(term) for term in self.terms)
        return f"({terms})"

    def __len__(self):
        return len(self.terms)

    def __iter__(self):
        return iter(self.terms)

    def add(self, term: T):
        self.terms.append(term)

    def union(self, other: "Multiset[T]"):
        return Multiset(self.terms + other.terms)

    def update(self, other: "Multiset[T]"):
        self.terms.extend(other.terms)


class Multiequation:
    """
    A multiequation sets a non-empty set of Variables equal to a multiset of non-variable Terms.
    Example:
    { x1, x2, x3 } = ( f(a, b), g(c, d) )
    """

    def __init__(self, vars: set[Variable], terms: Multiset[Application]):
        # Multiequation S = M
        self.vars = vars
        self.terms = terms

    def __repr__(self):
        vars = (
            "{"
            + ", ".join(var.name for var in sorted(self.vars, key=lambda var: var.name))
            + "}"
        )
        terms = "(" + ", ".join(str(term) for term in self.terms) + ")"
        return f"{vars} = {terms}"

    def union(self, other: "Multiequation"):
        return Multiequation(self.vars.union(other.vars), self.terms.union(other.terms))

    def update(self, other: "Multiequation"):
        self.vars.update(other.vars)
        self.terms.update(other.terms)


def make_multeq(M: Multiset[Term]):
    """Converts a multiset of terms to unify into a multiequation"""
    var_names = set[str]()
    terms = Multiset[Application]()
    for term in M.terms:
        match term:
            case Variable():
                var_names.add(term.name)
            case Application():
                terms.add(term)
            case _:
                pass
    return Multiequation({Variable(name) for name in var_names}, terms)


def common(M: Multiset[Term]) -> Term:
    """Finds the common part of a multiset of terms"""
    if len(M) == 0:
        raise Exception("Empty multiset")

    # If there is a variable in M
    for term in M:
        if isinstance(term, Variable):
            return term

    # Every term is a function
    func_name = M.terms[0].name
    arity = M.terms[0].arity()
    assert all(
        (term.name == func_name and term.arity() == arity) for term in M.terms
    ), "clash"

    common_args: list[Term] = []
    for i in range(arity):
        leaves = Multiset[Term]([term.args[i] for term in M.terms])
        common_args.append(common(leaves))
    return Application(func_name, common_args)


def frontier(M: Multiset[Term]):
    """Finds the frontier of a multiset of terms"""
    if len(M) == 0:
        raise Exception("Empty multiset")
    elif any(isinstance(term, Variable) for term in M):
        # There is a variable term
        return [make_multeq(M)]
    else:
        # Every term is a function
        func_name = M.terms[0].name
        arity = M.terms[0].arity()
        assert all(
            (term.name == func_name and term.arity() == arity) for term in M.terms
        ), "clash"

        f: list[Multiequation] = []
        for i in range(arity):
            leaves = Multiset[Term]([term.args[i] for term in M.terms])
            f.extend(frontier(leaves))
        return f


def DEC(M: Multiset[Term]) -> tuple[Term, list[Multiequation]]:
    """Finds the common part and frontier of a multiset of terms"""
    if len(M) == 0:
        raise Exception("Empty multiset")

    # If there is a variable in M
    for term in M:
        if isinstance(term, Variable):
            return term, [make_multeq(M)]

    # All functions in M
    func_name = M.terms[0].name
    arity = M.terms[0].arity()
    assert all(
        (term.name == func_name and term.arity() == arity) for term in M.terms
    ), "clash"

    common_args: list[Term] = []
    f: list[Multiequation] = []
    for i in range(arity):
        leaves = Multiset[Term]([term.args[i] for term in M.terms])
        common, frontier = DEC(leaves)
        common_args.append(common)
        f.extend(frontier)
    return Application(func_name, common_args), f


def compactify(multiequations: list[Multiequation]):
    """
    Compactifies the list of multiequations using a UNION-FIND to merge equations
    that have variables that are part of the same group.

    For example:
        {x1, x2} = (A)
        {x2, x3} = (B)
        {x4}     = (C)
    Will become:
        {x1, x2, x3} = (A, B)
        {x4}     = (C)
    """
    # Get all the variable names
    var_names: set[str] = set()
    for meq in multiequations:
        var_names.update(var.name for var in meq.vars)

    # Get the sets of variable names to group together
    uf = UnionFind(var_names)
    for meq in multiequations:
        if len(meq.vars) >= 2:
            uf.union_all(var.name for var in meq.vars)
    var_sets = uf.get_sets()

    # Set up the compactified multiequations
    compactified: list[Multiequation] = []
    var_to_meq: dict[str, Multiequation] = {}
    for var_set in var_sets:
        meq = Multiequation({Variable(var_name) for var_name in var_set}, Multiset())
        compactified.append(meq)
        for var_name in var_set:
            var_to_meq[var_name] = meq

    # Add each set of terms to the correct multiequation
    for meq in multiequations:
        var_to_meq[next(iter(meq.vars)).name].terms.update(meq.terms)
    return compactified


def solve_multiequations(system: list[Multiequation]):
    # System R = (T, U)
    # T = sequence of multiequations (solved part)
    # U = set of multiequations (unsolved part)

    # Conditions:
    # 1. Set of left-hand vars for all multiequations in T is disjoint with that of U
    # 2. Right-hand sides of all multiequations in T have 0-1 terms
    # 3. Every variable on the left-hand side of a multiequation in T can only occur
    #    in the right-hand side of any preceding multiequation
    U = system
    T: list[Multiequation] = []

    # Step 1
    while len(U) > 0:
        found = False
        for selected_meq in U:
            # Step 1.1: Find a multiequation that has terms
            if len(selected_meq.terms) > 0:
                # Step 1.2: Compute the common part and frontier of the selected multiequation's terms
                common, frontier = DEC(selected_meq.terms)

                # Step 1.3: Make sure the left-hand sides of the frontier don't contain
                # a variable in the left-hand side of the selected multiequation
                for meq in frontier:
                    if not meq.vars.isdisjoint(selected_meq.vars):
                        raise Exception("cycle")

                # Step 1.4: Transform U using multiequation reduction on `selected_meq`
                # and compactification
                selected_meq.terms = Multiset([common])
                U.extend(frontier)
                U = compactify(U)

                # Step 1.5: Apply the substitution to all terms on the right-hand side
                # of every multiequation in U
                substitution = {var.name: common for var in selected_meq.vars}
                for meq in U:
                    meq.terms = Multiset(
                        [apply_substitution(term, substitution) for term in meq.terms]
                    )

                # Step 1.6: Move the selected multiequation from U to T
                for meq in U:
                    if not selected_meq.vars.isdisjoint(meq.vars):
                        # Re-located the selected multiequation object
                        selected_meq = meq
                        break
                U.remove(selected_meq)
                T.append(selected_meq)

                found = True
                break
        if not found:
            # All multiequations in U have an empty right-hand side
            break

    # Step 2: Transfer all left-over multiequations from U to T
    T.extend(U)
    return T


def unify(terms: Multiset[Term]):
    unique_var = Variable("")
    multiequations = [Multiequation({unique_var}, terms)]
    V: set[Variable] = set()
    for term in terms:
        V.update(term_vars(term))

    for var in V:
        multiequations.append(Multiequation({var}, Multiset()))

    solution = solve_multiequations(multiequations)
    for meq in solution:
        print("{" + ", ".join(str(var) for var in meq.vars) + "} =", meq.terms)


def main():
    # Expect:
    # f(h(C), g(A, f(B, B)))
    terms = Multiset[Term](
        [
            parse_term("f( x1,   g(A,  f(x5, B)))"),
            parse_term("f(h(C),  g(x2, f(B, x5)))"),
            parse_term("f(h(x4), g(x6,    x3))"),
        ]
    )

    # Expect:
    # f(g(h(A, B), h(A, B)), g(h(A, B), h(A, B)), h(A, B), B)
    terms2 = Multiset[Term](
        [
            parse_term("f(      x1,        g(x2, x3),     x2,     B)"),
            parse_term("f(g(h(A, x5), x2),     x1,     h(A, x4),  x4)"),
        ]
    )

    print("EXAMPLE 1:")
    unify(terms)

    print("-" * 60)
    print("EXAMPLE 2:")
    unify(terms2)


if __name__ == "__main__":
    main()
