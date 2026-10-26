from ..expressions import parseExpression
from ..lexer import isValidIdentifier
from ..tokens import SyntaxErrorDetail
from .helpers import isType, expectNoExtraTokens, parseWholeExpression


# WAZZUP
def checkWazzup(lineToks, lineNum, state):
    if state.inWazzup:
        raise SyntaxErrorDetail("Nested 'WAZZUP' is not allowed.", lineNum)
    expectNoExtraTokens(lineToks, "WAZZUP", lineNum)
    state.inWazzup = True
    state.wazzupLine = lineNum


# BUHBYE
def checkBuhbye(lineToks, lineNum, state):
    if not state.inWazzup:
        raise SyntaxErrorDetail("'BUHBYE' found without matching 'WAZZUP'.", lineNum)
    expectNoExtraTokens(lineToks, "BUHBYE", lineNum)
    state.inWazzup = False


# I HAS A <var> [ITZ <expr>]
def checkDeclaration(lineToks, lineNum, state):
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected variable identifier after 'I HAS A'.", lineNum)
    varTok = lineToks[1]
    if not isValidIdentifier(varTok.lexeme) or varTok.classification not in ("Variable Identifier", "Loop Identifier", "Function Identifier"):
        raise SyntaxErrorDetail(f"Invalid variable identifier '{varTok.lexeme}'.", lineNum)

    if len(lineToks) > 2:
        if lineToks[2].lexeme != "ITZ":
            raise SyntaxErrorDetail(f"Unexpected token '{lineToks[2].lexeme}' in variable declaration. Expected 'ITZ' or newline.", lineNum)
        if len(lineToks) == 3:
            raise SyntaxErrorDetail("Expected expression after 'ITZ'.", lineNum)
        parseWholeExpression(lineToks[3:], lineNum, "after variable initialization")


# <var> R <expr>
def checkAssignment(lineToks, lineNum, state):
    first = lineToks[0]
    if first.classification != "Variable Identifier" and not isValidIdentifier(first.lexeme):
        raise SyntaxErrorDetail(f"Invalid target '{first.lexeme}' for assignment 'R'.", lineNum)
    if len(lineToks) == 2:
        raise SyntaxErrorDetail("Expected expression after 'R'.", lineNum)
    parseWholeExpression(lineToks[2:], lineNum, "after assignment expression")


# <var> IS NOW A <type>
def checkRecast(lineToks, lineNum, state):
    if len(lineToks) < 3:
        raise SyntaxErrorDetail("Expected type after 'IS NOW A'.", lineNum)
    if not isType(lineToks[2]):
        raise SyntaxErrorDetail(f"Invalid type '{lineToks[2].lexeme}' after 'IS NOW A'.", lineNum)
    if len(lineToks) > 3:
        raise SyntaxErrorDetail(f"Unexpected token '{lineToks[3].lexeme}' after type.", lineNum)


# VISIBLE <expr>+ [!]
def checkVisible(lineToks, lineNum, state):
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected expression after 'VISIBLE'.", lineNum)
    cur = lineToks[1:]
    if cur[-1].lexeme == "!":
        cur = cur[:-1]
        if not cur:
            raise SyntaxErrorDetail("Expected expression before '!' in 'VISIBLE'.", lineNum)

    while cur:
        expr, cur = parseExpression(cur)


# GIMMEH <var>
def checkGimmeh(lineToks, lineNum, state):
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected variable identifier after 'GIMMEH'.", lineNum)
    if len(lineToks) > 2:
        raise SyntaxErrorDetail(f"Unexpected token '{lineToks[2].lexeme}' after 'GIMMEH <var>'.", lineNum)
    if lineToks[0].classification != "Variable Identifier" and not isValidIdentifier(lineToks[1].lexeme):
        raise SyntaxErrorDetail(f"Invalid variable identifier '{lineToks[1].lexeme}'.", lineNum)


# FOUND YR <expr>
def checkFoundYr(lineToks, lineNum, state):
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected expression after 'FOUND YR'.", lineNum)
    parseWholeExpression(lineToks[1:], lineNum, "after 'FOUND YR' expression")


# GTFO
def checkGtfo(lineToks, lineNum, state):
    expectNoExtraTokens(lineToks, "GTFO", lineNum)


# Standalone expression (evaluates to IT)
def checkExpressionStatement(lineToks, lineNum, state):
    try:
        parseWholeExpression(lineToks, lineNum, f"at line {lineNum}")
    except SyntaxErrorDetail:
        raise SyntaxErrorDetail(f"Invalid statement starting with '{lineToks[0].lexeme}'.", lineNum)
