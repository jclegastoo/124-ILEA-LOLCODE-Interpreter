from ..constants import types
from ..expressions import parseExpression
from ..tokens import SyntaxErrorDetail


class CheckerState:
    """Tracks open WAZZUP and nested blocks while checking a program line by line."""
    def __init__(self):
        self.inWazzup = False
        self.wazzupLine = None
        # Entries are (blockType, startLine, data), e.g. ('LOOP', 4, {'label': 'x'})
        self.blockStack = []

    def topBlockType(self):
        return self.blockStack[-1][0] if self.blockStack else None

    def topBlockData(self):
        return self.blockStack[-1][2]


def isType(tok):
    return tok.lexeme in types or tok.classification == "Type Literal"


def expectNoExtraTokens(lineToks, keyword, lineNum):
    if len(lineToks) > 1:
        raise SyntaxErrorDetail(f"Unexpected tokens after '{keyword}'.", lineNum)


def parseWholeExpression(toks, lineNum, where):
    """Parses toks as exactly one expression; `where` describes it in the error message."""
    expr, rest = parseExpression(toks)
    if rest:
        raise SyntaxErrorDetail(f"Unexpected token '{rest[0].lexeme}' {where}.", lineNum)
    return expr
