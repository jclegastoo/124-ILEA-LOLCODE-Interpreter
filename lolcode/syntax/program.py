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




def checkComments(tokens):
    """Ensures multi-line comments (OBTW...TLDR) are well-formed and do not share lines with code."""
    linesWithCode = set()
    linesWithObtw = set()
    linesWithTldr = set()
    obtwCount = 0
    firstObtwLine = None


    for t in tokens:
        if t.classification not in commentClasses:
            linesWithCode.add(t.line)
        elif t.lexeme == "OBTW":
            linesWithObtw.add(t.line)
            obtwCount += 1
            if firstObtwLine is None:
                firstObtwLine = t.line
        elif t.lexeme == "TLDR":
            linesWithTldr.add(t.line)
            if obtwCount == 0:
                raise SyntaxErrorDetail("Found closing comment delimiter 'TLDR' without matching 'OBTW'.", t.line)
            obtwCount -= 1
            if obtwCount == 0:
                firstObtwLine = None


    # Check if OBTW shares a line with code
    obtwWithCode = linesWithObtw & linesWithCode
    if obtwWithCode:
        lineNum = min(obtwWithCode)
        raise SyntaxErrorDetail("Multi-line comment 'OBTW' cannot appear on the same line as code.", lineNum)


    # Check if TLDR shares a line with code
    tldrWithCode = linesWithTldr & linesWithCode
    if tldrWithCode:
        lineNum = min(tldrWithCode)
        raise SyntaxErrorDetail("Multi-line comment 'TLDR' cannot appear on the same line as code.", lineNum)


    # Check if OBTW and TLDR are on the same line
    sameLineBoth = linesWithObtw & linesWithTldr
    if sameLineBoth:
        lineNum = min(sameLineBoth)
        raise SyntaxErrorDetail("Multi-line comment 'OBTW' and 'TLDR' cannot appear on the same line.", lineNum)


    if obtwCount > 0:
        raise SyntaxErrorDetail(f"Unclosed multiline comment 'OBTW' starting at line {firstObtwLine} (missing 'TLDR').", firstObtwLine)




def checkSyntax(tokens):
    """Raises SyntaxErrorDetail on the first syntax error; returns True if the program is valid."""
    checkComments(tokens)


    execTokens = [t for t in tokens if t.classification not in commentClasses]


    haiTok, kthxTok, howizTok, saysoTok = checkProgramDelimiters(execTokens)


    state = CheckerState()
    for lineNum, lineToks in groupBodyLines(execTokens, haiTok, kthxTok):
        checkStatement(lineToks, lineNum, state)


    blocks.checkUnclosedBlocks(state)
    return True




def checkStatement(lineToks, lineNum, state):
    first = lineToks[0]


    # CAN HAS STDIO?
    if first.lexeme in ("CAN HAS STDIO?", "CAN HAS"):
        return statements.checkStdio(lineToks, lineNum, state)


    # WAZZUP ... BUHBYE block
    if first.lexeme == "WAZZUP":
        return statements.checkWazzup(lineToks, lineNum, state)
    if first.lexeme == "BUHBYE":
        return statements.checkBuhbye(lineToks, lineNum, state)
    if state.inWazzup and first.lexeme != "I HAS A":
        raise SyntaxErrorDetail(f"Only variable declarations ('I HAS A') are allowed inside 'WAZZUP'...'BUHBYE'. Found '{first.lexeme}'.", lineNum)


    if first.lexeme == "I HAS A":
        return statements.checkDeclaration(lineToks, lineNum, state)


    # Block-specific checks for statements inside O RLY? and WTF?
    if state.topBlockType() == 'O RLY?' and state.topBlockData()['stage'] == 'start' and first.lexeme != "YA RLY":
        raise SyntaxErrorDetail(f"Expected 'YA RLY' after 'O RLY?', found '{first.lexeme}'.", lineNum)
    if state.topBlockType() == 'WTF?' and state.topBlockData()['stage'] == 'start' and first.lexeme not in ("OMG", "OMGWTF"):
        raise SyntaxErrorDetail(f"Expected 'OMG' or 'OMGWTF' in switch block, found '{first.lexeme}'.", lineNum)


    # Mark that an executable statement has been encountered
    state.hasExecutedStatements = True


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
    howizTokens = [t for t in execTokens if t.lexeme in "HOW IZ I"]
    saysoTokens = [t for t in execTokens if t.lexeme == "IF U SAY SO"]


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
    howizTok = howizTokens[0]
    saysoTok = saysoTokens[0]


    if kthxTok.line < haiTok.line:
        raise SyntaxErrorDetail(f"Closing delimiter '{kthxTok.lexeme}' on line {kthxTok.line} cannot appear before 'HAI' on line {haiTok.line}.", kthxTok.line)


    # Check for executable code before HAI
    for t in execTokens:
        if t.line < haiTok.line:
            if t.line == howizTok.line:
                break
            else:
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
            if t.line == saysoTok.line:
                break
            else:
                raise SyntaxErrorDetail(f"Unexpected statement '{t.lexeme}' after closing '{kthxTok.lexeme}'.", t.line)


    return haiTok, kthxTok, howizTok, saysoTok

def groupBodyLines(execTokens, haiTok, kthxTok):
    """Returns [(lineNum, tokens)] for every line strictly between HAI and KTHXBYE."""
    linesDict = {}
    for t in execTokens:
        if haiTok.line < t.line < kthxTok.line:
            linesDict.setdefault(t.line, []).append(t)
    return sorted(linesDict.items())