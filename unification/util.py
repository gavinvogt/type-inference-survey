from terms import Term, Variable, Application, Constant


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
