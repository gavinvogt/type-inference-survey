from terms import Term, Variable, Application, Constant
from typing import Iterable


def occurs(var: Variable, term: Term):
    """
    Checks if the given variable occurs in the term
    """
    match term:
        case Constant():
            return False
        case Variable():
            # A variable could only occur in another variable if they are the same
            # This case is irrelevant, however, since equations of form "x = x" get erased
            return var == term
        case Application():
            return any(occurs(var, arg) for arg in term.args)
        case _:
            raise Exception(f"Unknown term type {type(term)}")


def substitute(term: Term, x: Variable, t: Term):
    """
    Applies the substitution x -> t to the given term
    term: Term to apply substitution to
    x: Variable to replace
    t: Term to replace with
    """
    match term:
        case Variable():
            return t if (term == x) else term
        case Application():
            return Application(term.name, [substitute(arg, x, t) for arg in term.args])
        case _:
            return term


def apply_substitution(term: Term, substitution: dict[str, Term]) -> Term:
    match term:
        case Variable():
            return substitution.get(term.name, term)
        case Application():
            return Application(
                term.name, [apply_substitution(arg, substitution) for arg in term.args]
            )
        case _:
            return term


def term_vars(term: Term):
    """Finds the set of Variables in the given Term"""
    v: set[Variable] = set()
    match term:
        case Variable():
            v.add(term)
        case Application():
            for arg in term.args:
                v.update(term_vars(arg))
        case _:
            pass
    return v


class UnionFind:
    def __init__(self, vars: Iterable[str]):
        # Each node starts as its own parent
        self._parent = {var: var for var in vars}

    def find(self, var: str):
        """Find the parent var name for the given var name"""
        if self._parent[var] != var:
            # Compress path while finding the root parent
            self._parent[var] = self.find(self._parent[var])
        return self._parent[var]

    def union(self, var1: str, var2: str):
        """Join the sets containing var1 and var2"""
        parent1 = self._parent[var1]
        parent2 = self._parent[var2]
        if parent1 != parent2:
            # Join the sets
            self._parent[parent2] = parent1

    def union_all(self, vars: Iterable[str]):
        """Union all the variables in the given set"""
        var1 = next(iter(vars))
        for var in vars:
            self.union(var1, var)

    def get_sets(self) -> list[set[str]]:
        """Gets the sets of variables that are grouped together"""
        groups: dict[str, set[str]] = {}
        for var in self._parent.keys():
            parent = self.find(var)
            if parent in groups:
                groups[parent].add(var)
            else:
                groups[parent] = {var}
        return list(groups.values())
