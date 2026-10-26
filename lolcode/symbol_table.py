from .constants import commentClasses

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


def buildSymbolTable(tokens):
    """Fills a SymbolTable from the I HAS A declarations in a syntax-checked token list.

    Only literal initial values (I HAS A x ITZ 12) are filled in. Values that need
    evaluating (expressions, R, GIMMEH) are left as NOOB for the semantic analyzer.
    """
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

        # I HAS A <var> ITZ <literal>, with the YARN's quotes already split off by the lexer
        initToks = [t for t in lineToks[3:] if t.classification != "String Delimiter"]
        if len(lineToks) > 2 and lineToks[2].lexeme == "ITZ" and len(initToks) == 1:
            literal = initToks[0]
            if literal.classification in literalTypes:
                table.assign(name, literal.lexeme, literalTypes[literal.classification])

    return table
