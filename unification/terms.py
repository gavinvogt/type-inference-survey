from abc import ABCMeta, abstractmethod


class Term(metaclass=ABCMeta):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        info = ", ".join(f"{name}={repr(value)}" for name, value in vars(self).items())
        return f"{self.__class__.__name__}({info})"

    def __hash__(self):
        return hash(self.name)

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        return NotImplemented


class Variable(Term):
    def __eq__(self, other: object):
        if isinstance(other, Variable):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return super().__hash__()


class Application(Term):
    def __init__(self, name: str, args: list[Term]):
        super().__init__(name)
        self.args = args

    def arity(self):
        return len(self.args)

    def __str__(self):
        if len(self.args) == 0:
            return super().__str__()
        else:
            args = ", ".join(str(arg) for arg in self.args)
            return f"{self.name}({args})"

    def __eq__(self, other: object):
        if isinstance(other, Application):
            return (
                self.name == other.name
                and self.arity() == other.arity()
                and all(self.args[i] == other.args[i] for i in range(self.arity()))
            )
        else:
            return False

    def __hash__(self):
        return super().__hash__()


class Constant(Application):
    def __init__(self, name: str):
        # A constant symbol is the special case of a 0-adic function application
        # For example, "f" is an implicit call "f()" with no arguments
        super().__init__(name, [])
