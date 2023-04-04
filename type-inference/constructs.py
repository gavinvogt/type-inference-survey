"""
File: constructs.py
Author: Gavin Vogt
Defines the Type contructs
"""


class Type:
    pass


class TypeVariable(Type):
    """Represents a type variable that has not been narrowed to a contant type"""

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other: object):
        if isinstance(other, TypeVariable):
            return self.name == other.name
        else:
            return False


class TypeApplication(Type):
    """Represents a function type such as (a -> b)"""

    def __init__(self, args: list[Type], ret: Type | None):
        self._args = args
        if ret is None:
            self._ret = TypeConstant("void")
        else:
            self._ret = ret

    def __str__(self):
        if len(self._args) == 1 and not isinstance(self._args[0], TypeApplication):
            return f"{self._args[0]} -> {self._ret}"
        else:
            arg_list = ", ".join(str(arg) for arg in self._args)
            return f"({arg_list}) -> {self._ret}"

    @property
    def args(self):
        return self._args

    def __eq__(self, other: object):
        """Checks if two types are equivalent"""
        if isinstance(other, TypeApplication):
            return (
                len(self.args) == len(other.args)
                and all(x == y for x, y in zip(self.args, other.args))
                and self._ret == other._ret
            )
        else:
            return False


class TypeConstant(Type):
    """Represents a constant type (bool, int, float). Could be extended to
    handle more builtin types and/or user-defined types."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other: object):
        if isinstance(other, TypeConstant):
            return self.name == other.name
        else:
            return False


class TypeList(Type):
    """Represents a list that contains some other type (type var, constant, or other list)"""

    def __init__(self, el_type: Type):
        self.el_type = el_type

    def __str__(self):
        return f"{self.el_type}[]"

    def __eq__(self, other: object):
        if isinstance(other, TypeList):
            return self.el_type == other.el_type
        else:
            return False
