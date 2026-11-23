from ..expressions import parseExpression
from ..lexer import isValidIdentifier
from ..tokens import SyntaxErrorDetail
from .helpers import isType, expectNoExtraTokens, parseWholeExpression, expectVariable



# CAN HAS STDIO?
def checkStdio(lineToks, lineNum, state):
    if state.hasStdio:
        raise SyntaxErrorDetail("Multiple 'CAN HAS STDIO?' statements are not allowed.", lineNum)
    if state.hasWazzup or state.inWazzup:
        raise SyntaxErrorDetail("'CAN HAS STDIO?' must appear before 'WAZZUP'.", lineNum)
    if state.hasExecutedStatements:
        raise SyntaxErrorDetail("'CAN HAS STDIO?' cannot appear after executable statements.", lineNum)

    if lineToks[0].lexeme == "CAN HAS STDIO?":
        expectNoExtraTokens(lineToks, "CAN HAS STDIO?", lineNum)
    elif lineToks[0].lexeme == "CAN HAS":
        if len(lineToks) < 2:
            raise SyntaxErrorDetail("Expected library name after 'CAN HAS'.", lineNum)
        libName = lineToks[1].lexeme
        if libName == "STDIO?":
            if len(lineToks) > 2:
                raise SyntaxErrorDetail("Unexpected tokens after 'CAN HAS STDIO?'.", lineNum)
        elif libName == "STDIO":
            if len(lineToks) == 2 or lineToks[2].lexeme != "?":
                raise SyntaxErrorDetail("Expected '?' after 'STDIO' in 'CAN HAS STDIO?'.", lineNum)
            if len(lineToks) > 3:
                raise SyntaxErrorDetail("Unexpected tokens after 'CAN HAS STDIO?'.", lineNum)
        else:
            raise SyntaxErrorDetail(f"Unknown library '{libName}'. Expected 'STDIO?'.", lineNum)

    state.hasStdio = True


# WAZZUP
def checkWazzup(lineToks, lineNum, state):
    if state.inWazzup:
        raise SyntaxErrorDetail("Nested 'WAZZUP' is not allowed.", lineNum)

    if state.hasWazzup:
        raise SyntaxErrorDetail("Multiple 'WAZZUP' sections are not allowed.", lineNum)

    if state.hasExecutedStatements:
        raise SyntaxErrorDetail("'WAZZUP' cannot appear after executable statements.", lineNum)

    expectNoExtraTokens(lineToks, "WAZZUP", lineNum)

    state.inWazzup = True
    state.hasWazzup = True
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

    if not isValidIdentifier(varTok.lexeme) or varTok.classification not in (
        "Variable Identifier",
        "Loop Identifier",
        "Function Identifier"
    ):
        raise SyntaxErrorDetail(f"Invalid variable identifier '{varTok.lexeme}'.", lineNum)

    # Check for duplicate variable declaration
    if varTok.lexeme in state.declaredVariables:
        raise SyntaxErrorDetail(f"Variable '{varTok.lexeme}' is already declared.", lineNum)

    initExpr = None

    if len(lineToks) > 2:
        if lineToks[2].lexeme != "ITZ":
            raise SyntaxErrorDetail(f"Unexpected token '{lineToks[2].lexeme}' in variable declaration. Expected 'ITZ' or newline.", lineNum)

        if len(lineToks) == 3:
            raise SyntaxErrorDetail("Expected expression after 'ITZ'.", lineNum)

        initExpr = parseWholeExpression(lineToks[3:], lineNum, "after variable initialization")

    # Register variable after successful validation
    state.declaredVariables.add(varTok.lexeme)
    return ("DECLARE", varTok.lexeme, initExpr)


# <var> R <expr>
def checkAssignment(lineToks, lineNum, state):
    expectVariable(lineToks[0], lineNum, "as target of assignment 'R'")

    if len(lineToks) == 2:
        raise SyntaxErrorDetail("Expected expression after 'R'.", lineNum)
    expr = parseWholeExpression(lineToks[2:], lineNum, "after assignment expression")
    return ("ASSIGN", lineToks[0].lexeme, expr)



# <var> IS NOW A <type>
def checkRecast(lineToks, lineNum, state):
    expectVariable(lineToks[0], lineNum, "before 'IS NOW A'")
    if len(lineToks) < 3:
        raise SyntaxErrorDetail("Expected type after 'IS NOW A'.", lineNum)
    if not isType(lineToks[2]):
        raise SyntaxErrorDetail(f"Invalid type '{lineToks[2].lexeme}' after 'IS NOW A'.", lineNum)
    if len(lineToks) > 3:
        raise SyntaxErrorDetail(f"Unexpected token '{lineToks[3].lexeme}' after type.", lineNum)
    return ("RECAST", lineToks[0].lexeme, lineToks[2].lexeme)



# VISIBLE <expr> [[+] <expr>]* [!]  ->  ("VISIBLE", [exprs], printNewline)
def checkVisible(lineToks, lineNum, state):
    cur = lineToks[1:]
    printNewline = True
    if cur and cur[-1].classification == "Newline Suppressor":
        cur = cur[:-1]
        printNewline = False
    if not cur:
        raise SyntaxErrorDetail("Expected expression after 'VISIBLE'.", lineNum)

    args = []
    while cur:
        expr, cur = parseExpression(cur)
        args.append(expr)
        if cur and cur[0].classification == "Output Separator":
            cur = cur[1:]
            if not cur:
                raise SyntaxErrorDetail("Expected expression after '+' in 'VISIBLE'.", lineNum)
    return ("VISIBLE", args, printNewline)


# GIMMEH <var>
def checkGimmeh(lineToks, lineNum, state):
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected variable identifier after 'GIMMEH'.", lineNum)
    if len(lineToks) > 2:
        raise SyntaxErrorDetail(f"Unexpected token '{lineToks[2].lexeme}' after 'GIMMEH <var>'.", lineNum)
    expectVariable(lineToks[1], lineNum, "after 'GIMMEH'")
    return ("GIMMEH", lineToks[1].lexeme)



# FOUND YR <expr>
def checkFoundYr(lineToks, lineNum, state):
    if not any(b[0] == 'FUNC' for b in state.blockStack):
        raise SyntaxErrorDetail("'FOUND YR' can only be used inside a function.", lineNum)

    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected expression after 'FOUND YR'.", lineNum)
    return ("FOUND YR", parseWholeExpression(lineToks[1:], lineNum, "after 'FOUND YR' expression"))



# GTFO
def checkGtfo(lineToks, lineNum, state):
    if not any(b[0] in ('LOOP', 'WTF?', 'FUNC') for b in state.blockStack):
        raise SyntaxErrorDetail("'GTFO' can only be used inside a loop, switch, or function.", lineNum)

    expectNoExtraTokens(lineToks, "GTFO", lineNum)
    return("GTFO",)


# Standalone expression (evaluates to IT)
def checkExpressionStatement(lineToks, lineNum, state):
    try:
        expr = parseWholeExpression(lineToks, lineNum, f"at line {lineNum}")
    except SyntaxErrorDetail:
        raise SyntaxErrorDetail(f"Invalid statement starting with '{lineToks[0].lexeme}'.", lineNum)
    return ("EXPR", expr)
