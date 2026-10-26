from ..constants import commentClasses
from ..tokens import SyntaxErrorDetail
from . import blocks, statements
from .helpers import CheckerState

# Statements identified by their first token
statementChecks = {
    "VISIBLE": statements.checkVisible,
    "GIMMEH": statements.checkGimmeh,
    "FOUND YR": statements.checkFoundYr,
    "GTFO": statements.checkGtfo,
    "O RLY?": blocks.checkORly,
    "YA RLY": blocks.checkYaRly,
    "MEBBE": blocks.checkMebbe,
    "NO WAI": blocks.checkNoWai,
    "WTF?": blocks.checkWtf,
    "OMG": blocks.checkOmg,
    "OMGWTF": blocks.checkOmgWtf,
    "OIC": blocks.checkOic,
    "IM IN YR": blocks.checkLoopStart,
    "IM OUTTA YR": blocks.checkLoopEnd,
    "HOW IZ I": blocks.checkFunctionStart,
    "IF U SAY SO": blocks.checkFunctionEnd,
}


def checkSyntax(tokens):
    """Raises SyntaxErrorDetail on the first syntax error; returns True if the program is valid."""
    execTokens = [t for t in tokens if t.classification not in commentClasses]

    haiTok, kthxTok = checkProgramDelimiters(execTokens)

    state = CheckerState()
    for lineNum, lineToks in groupBodyLines(execTokens, haiTok, kthxTok):
        checkStatement(lineToks, lineNum, state)

    blocks.checkUnclosedBlocks(state)
    return True


def checkStatement(lineToks, lineNum, state):
    first = lineToks[0]

    # WAZZUP ... BUHBYE block
    if first.lexeme == "WAZZUP":
        return statements.checkWazzup(lineToks, lineNum, state)
    if first.lexeme == "BUHBYE":
        return statements.checkBuhbye(lineToks, lineNum, state)
    if state.inWazzup and first.lexeme != "I HAS A":
        raise SyntaxErrorDetail(f"Only variable declarations ('I HAS A') are allowed inside 'WAZZUP'...'BUHBYE'. Found '{first.lexeme}'.", lineNum)

    if first.lexeme == "I HAS A":
        return statements.checkDeclaration(lineToks, lineNum, state)

    # Statements identified by their second token
    if len(lineToks) >= 2 and lineToks[1].lexeme == "R":
        return statements.checkAssignment(lineToks, lineNum, state)
    if len(lineToks) >= 2 and lineToks[1].lexeme == "IS NOW A":
        return statements.checkRecast(lineToks, lineNum, state)

    check = statementChecks.get(first.lexeme, statements.checkExpressionStatement)
    return check(lineToks, lineNum, state)


def checkProgramDelimiters(execTokens):
    """Validates HAI ... KTHXBYE placement and returns (haiTok, kthxTok)."""
    if not execTokens:
        raise SyntaxErrorDetail("Program is empty. Expected 'HAI' and 'KTHXBYE'.")

    # Locate HAI and KTHXBYE
    haiTokens = [t for t in execTokens if t.lexeme == "HAI"]
    kthxTokens = [t for t in execTokens if t.lexeme == "KTHXBYE"]

    if not haiTokens and not kthxTokens:
        raise SyntaxErrorDetail(f"Program must start with 'HAI' and end with 'KTHXBYE'. First token '{execTokens[0].lexeme}' found on line {execTokens[0].line}.", execTokens[0].line)

    if not haiTokens:
        raise SyntaxErrorDetail(f"Found closing delimiter '{kthxTokens[0].lexeme}' at line {kthxTokens[0].line} without opening 'HAI'.", kthxTokens[0].line)

    if not kthxTokens:
        raise SyntaxErrorDetail(f"Program starts with 'HAI' at line {haiTokens[0].line}, but is missing closing 'KTHXBYE'.", haiTokens[0].line)

    if len(haiTokens) > 1:
        raise SyntaxErrorDetail("Multiple 'HAI' code delimiters found.", haiTokens[1].line)

    if len(kthxTokens) > 1:
        raise SyntaxErrorDetail(f"Multiple '{kthxTokens[1].lexeme}' code delimiters found.", kthxTokens[1].line)

    haiTok = haiTokens[0]
    kthxTok = kthxTokens[0]

    if kthxTok.line < haiTok.line:
        raise SyntaxErrorDetail(f"Closing delimiter '{kthxTok.lexeme}' on line {kthxTok.line} cannot appear before 'HAI' on line {haiTok.line}.", kthxTok.line)

    # Check for executable code before HAI
    for t in execTokens:
        if t.line < haiTok.line:
            raise SyntaxErrorDetail(f"Unexpected statement '{t.lexeme}' before 'HAI'.", t.line)

    # Tokens on HAI line: HAI [version]
    haiLineTokens = [t for t in execTokens if t.line == haiTok.line]
    if haiLineTokens[0] != haiTok:
        raise SyntaxErrorDetail(f"Unexpected token '{haiLineTokens[0].lexeme}' before 'HAI'.", haiTok.line)

    if len(haiLineTokens) > 2:
        raise SyntaxErrorDetail(f"Unexpected tokens after 'HAI' on line {haiTok.line}.", haiTok.line)
    elif len(haiLineTokens) == 2:
        versionTok = haiLineTokens[1]
        if versionTok.classification not in ("NUMBAR Literal", "NUMBR Literal"):
            raise SyntaxErrorDetail(f"Invalid LOLCODE version '{versionTok.lexeme}' after 'HAI'. Expected a number.", haiTok.line)

    # Tokens on KTHXBYE line
    kthxLineTokens = [t for t in execTokens if t.line == kthxTok.line]
    if len(kthxLineTokens) > 1:
        other = [t for t in kthxLineTokens if t != kthxTok][0]
        raise SyntaxErrorDetail(f"Unexpected token '{other.lexeme}' on '{kthxTok.lexeme}' line.", kthxTok.line)

    # Check for executable code after KTHXBYE
    for t in execTokens:
        if t.line > kthxTok.line:
            raise SyntaxErrorDetail(f"Unexpected statement '{t.lexeme}' after closing '{kthxTok.lexeme}'.", t.line)

    return haiTok, kthxTok


def groupBodyLines(execTokens, haiTok, kthxTok):
    """Returns [(lineNum, tokens)] for every line strictly between HAI and KTHXBYE."""
    linesDict = {}
    for t in execTokens:
        if haiTok.line < t.line < kthxTok.line:
            linesDict.setdefault(t.line, []).append(t)
    return sorted(linesDict.items())
