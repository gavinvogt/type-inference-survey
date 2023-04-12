"""
File: constructs.py
Author: Gavin Vogt
Defines the Type contructs
"""

from typing import Optional


class Type:
    def __repr__(self):
        return f"{self.__class__.__name__}({str(self)})"


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
    """Represents a function type such as (a -> b -> c)"""

    def __init__(self, arg: Type, ret: Optional[Type]):
        self.arg = arg
        if ret is None:
            self.ret = TypeConstant("unit")
        else:
            self.ret = ret

    def __str__(self):
        if isinstance(self.arg, TypeApplication):
            # Add parenthesis to clarify associativity
            return f"({self.arg}) -> {self.ret}"
        else:
            # No parenthesis needed
            return f"{self.arg} -> {self.ret}"

    def __eq__(self, other: object):
        """Checks if two types are equivalent"""
        if isinstance(other, TypeApplication):
            return (
                # TODO: get rid of length check
                # len(self.args) == len(other.args)
                self.arg == other.arg
                and self.ret == other.ret
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
