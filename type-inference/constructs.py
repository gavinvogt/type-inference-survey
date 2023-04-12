"""
File: constructs.py
Author: Gavin Vogt
Defines the Type contructs
"""

from typing import Optional
from abc import ABC, abstractmethod


class PolymorphicTypeVar:
    LETTERS = "abcdefghijklmnopqrstuvwxyz"

    def __init__(self):
        self._n = 0
        self._types: dict[str, str] = {}

    def get_type(self, var_name: str):
        if var_name not in self._types:
            letter = self.LETTERS[self._n]
            self._types[var_name] = f"'{letter}"
            self._n += 1  # advance the letter
        return self._types[var_name]


class Type(ABC):
    def __repr__(self):
        return f"{self.__class__.__name__}({str(self)})"

    @abstractmethod
    def type_str(self, ptv: Optional[PolymorphicTypeVar] = None) -> str:
        """
        Gets the full type string using 'a, 'b, ... for polymorphic type variables.

        Example:
        map : ('a -> 'b) -> 'a[] -> 'b[]
        """
        return NotImplemented


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

    def type_str(self, ptv: Optional[PolymorphicTypeVar] = None):
        if ptv is None:
            ptv = PolymorphicTypeVar()
        return ptv.get_type(self.name)


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

    def type_str(self, ptv: Optional[PolymorphicTypeVar] = None):
        if ptv is None:
            ptv = PolymorphicTypeVar()

        arg = self.arg.type_str(ptv)
        ret = self.ret.type_str(ptv)
        if isinstance(self.arg, TypeApplication):
            # Add parenthesis to clarify associativity
            return f"({arg}) -> {ret}"
        else:
            # No parenthesis needed
            return f"{arg} -> {ret}"


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

    def type_str(self, ptv: Optional[PolymorphicTypeVar] = None):
        return self.name


class TypeList(Type):
    """Represents a list that contains some other type (type var, constant, or other list)"""

    def __init__(self, el_type: Type):
        self.el_type = el_type

    def __str__(self):
        if isinstance(self.el_type, TypeApplication):
            # Add parenthesis to clarify associativity
            return f"({self.el_type})[]"
        else:
            # No parenthesis needed
            return f"{self.el_type}[]"

    def __eq__(self, other: object):
        if isinstance(other, TypeList):
            return self.el_type == other.el_type
        else:
            return False

    def type_str(self, ptv: Optional[PolymorphicTypeVar] = None):
        if ptv is None:
            ptv = PolymorphicTypeVar()

        el_type = self.el_type.type_str(ptv)
        if isinstance(self.el_type, TypeApplication):
            # Add parenthesis to clarify associativity
            return f"(el)[]"
        else:
            # No parenthesis needed
            return f"{el_type}[]"
