from .constants import commentClasses
from .expressions import parseExpression
import re

class Symbol:
    def __init__(self, name, value=None, type="NOOB"):
        self.name = name
        self.value = value
        self.type = type

    def displayValue(self):
        return "NOOB" if self.type == "NOOB" else str(self.value)

    def __repr__(self):
        return f"Symbol({self.name!r}, {self.value!r}, {self.type!r})"


class SymbolTable:
    """Variables available in the program and their current values. IT always exists."""
    def __init__(self):
        self.symbols = {}
        self.declare("IT")

    def declare(self, name, value=None, type="NOOB"):
        self.symbols[name] = Symbol(name, value, type)

    def assign(self, name, value, type):
        symbol = self.symbols[name]
        symbol.value = value
        symbol.type = type

    def lookup(self, name):
        return self.symbols.get(name)

    def isDeclared(self, name):
        return name in self.symbols

    def __iter__(self):
        return iter(self.symbols.values())

