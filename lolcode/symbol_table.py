from .constants import commentClasses
from .expressions import parseExpression

# Literal token classifications and the LOLCODE type they hold
literalTypes = {
    "NUMBR Literal": "NUMBR",
    "NUMBAR Literal": "NUMBAR",
    "YARN Literal": "YARN",
    "TROOF Literal": "TROOF",
}


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

def evaluateExpression(tree, table):
    op = tree[0]

    if op == "NUMBR Literal":
        return int(tree[1]), "NUMBR"

    if op == "NUMBAR Literal":
        return float(tree[1]), "NUMBAR"

    if op == "YARN":
        return tree[1], "YARN"

    if op == "TROOF":
        return tree[1], "TROOF"

    if op == "VAR":
        symbol = table.lookup(tree[1])

        if symbol is None:
            raise ValueError(f"Undeclared variable '{tree[1]}'.")

        if symbol.type == "NOOB":
            raise ValueError(f"Variable '{tree[1]}' is uninitialized.")

        value = symbol.value

        if symbol.type == "NUMBR":
            value = int(value)
        elif symbol.type == "NUMBAR":
            value = float(value)

        return value, symbol.type

    if op in ("SUM OF", "DIFF OF", "PRODUKT OF",
              "QUOSHUNT OF", "MOD OF", "BIGGR OF", "SMALLR OF"):

        left, leftType = evaluateExpression(tree[1], table)
        right, rightType = evaluateExpression(tree[2], table)

        if leftType not in ("NUMBR", "NUMBAR") or rightType not in ("NUMBR", "NUMBAR"):
            raise ValueError(f"Non-numeric operand in '{op}'.")

        if op == "SUM OF":
            result = left + right
        elif op == "DIFF OF":
            result = left - right
        elif op == "PRODUKT OF":
            result = left * right
        elif op == "QUOSHUNT OF":
            result = left / right
        elif op == "MOD OF":
            result = left % right
        elif op == "BIGGR OF":
            result = max(left, right)
        elif op == "SMALLR OF":
            result = min(left, right)

        resultType = "NUMBAR" if isinstance(result, float) else "NUMBR"
        return result, resultType

    raise NotImplementedError(f"Evaluation for '{op}' is not yet implemented.")

def buildSymbolTable(tokens):
    table = SymbolTable()

    lines = {}
    for t in tokens:
        if t.classification not in commentClasses:
            lines.setdefault(t.line, []).append(t)

    for lineToks in lines.values():
        if lineToks[0].lexeme != "I HAS A" or len(lineToks) < 2:
            continue

        name = lineToks[1].lexeme
        table.declare(name)

        if len(lineToks) > 3 and lineToks[2].lexeme == "ITZ":
            tree, remaining = parseExpression(lineToks[3:])

            if remaining:
                raise ValueError(f"Unexpected tokens in initialization of '{name}'.")

            value, valueType = evaluateExpression(tree, table)
            table.assign(name, value, valueType)

    return table
