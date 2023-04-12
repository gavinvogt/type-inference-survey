"""
File: scope.py
Author: Gavin Vogt
This program defines a class for keeping track of the identifiers in scope
and what their types are.
"""

from typing import Optional

from microml.ast import TypeSymbol


class Scope:
    """
    Tracks identifiers in the current scope and their type symbols. Also keeps track
    of the parent scope, if any.
    """

    def __init__(self, parent: Optional["Scope"] = None):
        self._parent = parent
        self._symbols: dict[str, TypeSymbol] = {}

    def __str__(self):
        symbols = "\n".join(
            f"{name}: {symbol}" for name, symbol in self.symbols.items()
        )
        if self._parent is None:
            return symbols
        else:
            return str(self._parent) + "\n----------\n" + symbols

    @property
    def symbols(self):
        """Readonly symbols dict"""
        return self._symbols

    def create(self, id: str):
        """Creates the given ID in the symbol table and gives it a type symbol"""
        if id in self._symbols:
            raise Exception(f"Identifier {id} already exists in scope")
        self._symbols[id] = TypeSymbol()

    def lookup(self, id: str) -> TypeSymbol:
        """Searches for the given ID in the scope"""
        if id in self._symbols:
            return self._symbols[id]
        elif self._parent is not None:
            return self._parent.lookup(id)
        else:
            raise Exception(f"{id} not found")
