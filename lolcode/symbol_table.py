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

def evaluateExpression(tree, table):
    op = tree[0]

    if op == "NUMBR":
        return int(tree[1]), "NUMBR"

    if op == "NUMBAR":
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

        # Spec: NUMBAR if at least one operand is a NUMBAR, otherwise NUMBR
        isNumbar = "NUMBAR" in (leftType, rightType)

        if op in ("QUOSHUNT OF", "MOD OF") and right == 0:
            raise ValueError(f"Division by zero in '{op}'.")

        if op == "SUM OF":
            result = left + right
        elif op == "DIFF OF":
            result = left - right
        elif op == "PRODUKT OF":
            result = left * right
        elif op == "QUOSHUNT OF":
            # NUMBR / NUMBR truncates toward zero: 5/2 -> 2, -7/2 -> -3
            result = left / right if isNumbar else int(left / right)
        elif op == "MOD OF":
            result = left % right
        elif op == "BIGGR OF":
            result = max(left, right)
        elif op == "SMALLR OF":
            result = min(left, right)

        if isNumbar:
            return float(result), "NUMBAR"
        return int(result), "NUMBR"

    # NOT operation
    if op == "NOT":
        value, valueType = evaluateExpression(tree[1], table)
        result = not toTroof(value, valueType)
        return ("WIN" if result else "FAIL"), "TROOF"

    # Binary Boolean operations
    if op in ("BOTH OF", "EITHER OF", "WON OF"):
        left, leftType = evaluateExpression(tree[1], table)
        right, rightType = evaluateExpression(tree[2], table)

        left = toTroof(left, leftType)
        right = toTroof(right, rightType)

        if op == "BOTH OF":
            result = left and right
        elif op == "EITHER OF":
            result = left or right
        elif op == "WON OF":
            result = left != right

        return ("WIN" if result else "FAIL"), "TROOF"

    # MAEK <expr> [A] <type>
    if op == "MAEK":
        value, valueType = evaluateExpression(tree[1], table)
        targetType = tree[2]

        # Convert to TROOF
        if targetType == "TROOF":
            result = toTroof(value, valueType)
            return ("WIN" if result else "FAIL"), "TROOF"

        # Convert to NUMBR or NUMBAR
        if targetType in ("NUMBR", "NUMBAR"):

            if valueType == "YARN":
                if not re.fullmatch(r"-?\d+(\.\d+)?", value):
                    raise ValueError(f"Cannot convert YARN '{value}' to {targetType}.")

            if valueType == "NOOB":
                value = 0
            elif valueType == "TROOF":
                value = 1 if toTroof(value, valueType) else 0

            if targetType == "NUMBR":
                return int(float(value)), "NUMBR"

            return float(value), "NUMBAR"

        # Convert to YARN
        if targetType == "YARN":
            if valueType == "NOOB":
                return "", "YARN"

            if valueType == "NUMBAR":
                text = str(value)
                if "." in text:
                    whole, decimal = text.split(".", 1)
                    text = whole + "." + decimal[:2]
                return text, "YARN"

            return str(value), "YARN"

        # Convert to NOOB
        if targetType == "NOOB":
            return None, "NOOB"

        raise ValueError(f"Invalid type '{targetType}' in MAEK.")

    raise NotImplementedError(f"Evaluation for '{op}' is not yet implemented.")

def toTroof(value, valueType):
    if valueType == "NOOB":
        return False
    if valueType == "TROOF":
        return value == "WIN" if isinstance(value, str) else bool(value)
    if valueType in ("NUMBR", "NUMBAR"):
        return float(value) != 0
    if valueType == "YARN":
        return value != ""

    raise ValueError(f"Cannot convert '{valueType}' to TROOF.")

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
