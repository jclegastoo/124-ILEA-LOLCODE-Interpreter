from .constants import types, binaryOperators
from .tokens import SyntaxErrorDetail


def parseExpression(toks, isNested=False):
    """Parses one expression from the front of toks. Returns (tree, remainingToks)."""
    if not toks:
        raise SyntaxErrorDetail("Expected expression, but line ended unexpectedly.")

    tok = toks[0]

    # Nested check for infinite-arity expressions
    if tok.lexeme in ("ALL OF", "ANY OF", "SMOOSH") and isNested:
        raise SyntaxErrorDetail(f"Nested '{tok.lexeme}' is not allowed.", tok.line)

    # YARN literal (with string delimiters or standalone)
    if tok.lexeme == '"':
        if len(toks) >= 3 and toks[1].classification == "YARN Literal" and toks[2].lexeme == '"':
            return ("YARN", toks[1].lexeme), toks[3:]
        raise SyntaxErrorDetail("Malformed string literal.", tok.line)

    if tok.classification == "YARN Literal":
        return ("YARN", tok.lexeme), toks[1:]

    # NUMBR / NUMBAR
    if tok.classification in ("NUMBR Literal", "NUMBAR Literal"):
        return (tok.classification.split()[0], tok.lexeme), toks[1:]

    # TROOF Literal (WIN / FAIL)
    if tok.classification == "TROOF Literal":
        return ("TROOF", tok.lexeme), toks[1:]

    

    if tok.lexeme == "NOT":
        return parseNot(toks, isNested)
    if tok.lexeme in binaryOperators:
        return parseBinary(toks, isNested)
    if tok.lexeme == "MAEK":
        return parseMaek(toks, isNested)
    if tok.lexeme == "SMOOSH":
        return parseSmoosh(toks, isNested)
    if tok.lexeme in ("ALL OF", "ANY OF"):
        return parseInfiniteArity(toks, isNested)
    if tok.lexeme == "I IZ":
        return parseFunctionCall(toks, isNested=isNested)
    #Variable Identifier or IT
    if tok.classification in ("Variable Identifier", "Implicit Variable"):
        return ("VAR", tok.lexeme), toks[1:]

    raise SyntaxErrorDetail(f"Unexpected token '{tok.lexeme}' in expression.", tok.line)



# NOT <expr>
def parseNot(toks, isNested=False):
    expr, rest = parseExpression(toks[1:], isNested=True)
    return ("NOT", expr), rest


# <op> <expr> AN <expr>
def parseBinary(toks, isNested=False):
    tok = toks[0]
    op = tok.lexeme
    e1, rest1 = parseExpression(toks[1:], isNested=True)
    if not rest1:
        raise SyntaxErrorDetail(f"'{op}' expects 2 operands separated by 'AN'.", tok.line)
    if rest1[0].lexeme != "AN":
        raise SyntaxErrorDetail(f"Expected 'AN' after first operand of '{op}', found '{rest1[0].lexeme}'.", rest1[0].line)
    e2, rest2 = parseExpression(rest1[1:], isNested=True)
    return (op, e1, e2), rest2


# MAEK <expr> [A] <type>
def parseMaek(toks, isNested=False):
    tok = toks[0]
    e, rest = parseExpression(toks[1:], isNested=True)
    if rest and rest[0].lexeme == "A":
        rest = rest[1:]
    if not rest:
        raise SyntaxErrorDetail("Expected type in 'MAEK' expression.", tok.line)
    typeTok = rest[0]
    if typeTok.lexeme not in types and typeTok.classification != "Type Literal":
        raise SyntaxErrorDetail(f"Invalid type '{typeTok.lexeme}' in 'MAEK' expression.", typeTok.line)
    return ("MAEK", e, typeTok.lexeme), rest[1:]


# SMOOSH <expr> [AN <expr>]* [MKAY]
def parseSmoosh(toks, isNested=False):
    curToks = toks[1:]
    args = []
    e, curToks = parseExpression(curToks, isNested=True)
    args.append(e)
    while curToks and curToks[0].lexeme == "AN":
        e, curToks = parseExpression(curToks[1:], isNested=True)
        args.append(e)
    if curToks and curToks[0].lexeme == "MKAY":
        curToks = curToks[1:]
    return ("SMOOSH", args), curToks


# ALL OF / ANY OF <expr> [AN <expr>]* MKAY
def parseInfiniteArity(toks, isNested=False):
    tok = toks[0]
    op = tok.lexeme
    curToks = toks[1:]
    args = []
    e, curToks = parseExpression(curToks, isNested=True)
    args.append(e)
    while curToks and curToks[0].lexeme != "MKAY":
        if curToks[0].lexeme != "AN":
            raise SyntaxErrorDetail(f"Expected 'AN' between '{op}' operands. found '{curToks[0].lexeme}'.", curToks[0].line)
        curToks = curToks[1:]
        e, curToks = parseExpression(curToks, isNested=True)
        args.append(e)
    if not curToks or curToks[0].lexeme != "MKAY":
        raise SyntaxErrorDetail(f"Expected 'MKAY' to close '{op}'.", tok.line)
    return (op, args), curToks[1:]


# I IZ <func> [YR <arg> [AN YR <arg>]*] [MKAY]
def parseFunctionCall(toks, isNested=False):
    tok = toks[0]
    curToks = toks[1:]
    if not curToks or curToks[0].classification != "Function Identifier":
        raise SyntaxErrorDetail("Expected function identifier after 'I IZ'.", tok.line)
    funcName = curToks[0].lexeme
    curToks = curToks[1:]
    args = []
    if curToks and curToks[0].lexeme == "YR":
        argExpr, curToks = parseExpression(curToks[1:], isNested=isNested)
        args.append(argExpr)
        while len(curToks) >= 2 and curToks[0].lexeme == "AN" and curToks[1].lexeme == "YR":
            argExpr, curToks = parseExpression(curToks[2:], isNested=isNested)
            args.append(argExpr)
    if not curToks or curToks[0].lexeme != "MKAY":
        raise SyntaxErrorDetail(f"Expected 'MKAY' to close call to '{funcName}'.", tok.line)
    curToks = curToks[1:]

    return ("CALL", funcName, args), curToks
