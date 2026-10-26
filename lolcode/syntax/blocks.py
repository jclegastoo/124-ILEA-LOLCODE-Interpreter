from ..expressions import parseExpression
from ..lexer import isValidIdentifier
from ..tokens import SyntaxErrorDetail
from .helpers import expectNoExtraTokens, parseWholeExpression


# ---------- Conditionals: O RLY? / YA RLY / MEBBE / NO WAI ----------

def checkORly(lineToks, lineNum, state):
    expectNoExtraTokens(lineToks, "O RLY?", lineNum)
    state.blockStack.append(('O RLY?', lineNum, {'stage': 'start'}))


def checkYaRly(lineToks, lineNum, state):
    expectNoExtraTokens(lineToks, "YA RLY", lineNum)
    if state.topBlockType() != 'O RLY?':
        raise SyntaxErrorDetail("'YA RLY' found without matching 'O RLY?'.", lineNum)
    if state.topBlockData()['stage'] != 'start':
        raise SyntaxErrorDetail("Unexpected 'YA RLY' in conditional block.", lineNum)
    state.topBlockData()['stage'] = 'ya_rly'


def checkMebbe(lineToks, lineNum, state):
    if state.topBlockType() != 'O RLY?':
        raise SyntaxErrorDetail("'MEBBE' found without matching 'O RLY?'.", lineNum)
    if state.topBlockData()['stage'] not in ('ya_rly', 'mebbe'):
        raise SyntaxErrorDetail("'MEBBE' cannot appear before 'YA RLY' or after 'NO WAI'.", lineNum)
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected expression after 'MEBBE'.", lineNum)
    parseWholeExpression(lineToks[1:], lineNum, "after 'MEBBE' expression")
    state.topBlockData()['stage'] = 'mebbe'


def checkNoWai(lineToks, lineNum, state):
    expectNoExtraTokens(lineToks, "NO WAI", lineNum)
    if state.topBlockType() != 'O RLY?':
        raise SyntaxErrorDetail("'NO WAI' found without matching 'O RLY?'.", lineNum)
    if state.topBlockData()['stage'] not in ('ya_rly', 'mebbe'):
        raise SyntaxErrorDetail("'NO WAI' cannot appear before 'YA RLY' or after another 'NO WAI'.", lineNum)
    state.topBlockData()['stage'] = 'no_wai'


# ---------- Switch: WTF? / OMG / OMGWTF ----------

def checkWtf(lineToks, lineNum, state):
    expectNoExtraTokens(lineToks, "WTF?", lineNum)
    state.blockStack.append(('WTF?', lineNum, {'stage': 'start'}))


def checkOmg(lineToks, lineNum, state):
    if state.topBlockType() != 'WTF?':
        raise SyntaxErrorDetail("'OMG' found without matching 'WTF?' switch block.", lineNum)
    if state.topBlockData()['stage'] == 'omgwtf':
        raise SyntaxErrorDetail("'OMG' cannot appear after 'OMGWTF'.", lineNum)
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected value after 'OMG'.", lineNum)
    parseWholeExpression(lineToks[1:], lineNum, "after 'OMG' value")
    state.topBlockData()['stage'] = 'omg'


def checkOmgWtf(lineToks, lineNum, state):
    expectNoExtraTokens(lineToks, "OMGWTF", lineNum)
    if state.topBlockType() != 'WTF?':
        raise SyntaxErrorDetail("'OMGWTF' found without matching 'WTF?' switch block.", lineNum)
    if state.topBlockData()['stage'] == 'omgwtf':
        raise SyntaxErrorDetail("Duplicate 'OMGWTF' default case.", lineNum)
    state.topBlockData()['stage'] = 'omgwtf'


# OIC closes O RLY? or WTF?
def checkOic(lineToks, lineNum, state):
    expectNoExtraTokens(lineToks, "OIC", lineNum)
    if state.topBlockType() not in ('O RLY?', 'WTF?'):
        raise SyntaxErrorDetail("'OIC' found without matching 'O RLY?' or 'WTF?'.", lineNum)
    state.blockStack.pop()


# ---------- Loops: IM IN YR / IM OUTTA YR ----------

# IM IN YR <label> [UPPIN|NERFIN YR <var>] [TIL|WILE <expr>]
def checkLoopStart(lineToks, lineNum, state):
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected loop label after 'IM IN YR'.", lineNum)
    label = lineToks[1].lexeme
    cur = lineToks[2:]
    # Optional operation: UPPIN / NERFIN YR <var>
    if cur and cur[0].lexeme in ("UPPIN", "NERFIN"):
        if len(cur) < 3 or cur[1].lexeme != "YR":
            raise SyntaxErrorDetail(f"Expected 'YR <var>' after '{cur[0].lexeme}'.", lineNum)
        cur = cur[3:]
    # Optional condition: TIL / WILE <expr>
    if cur and cur[0].lexeme in ("TIL", "WILE"):
        condType = cur[0].lexeme
        cur = cur[1:]
        if not cur:
            raise SyntaxErrorDetail(f"Expected expression after '{condType}'.", lineNum)
        expr, cur = parseExpression(cur)
    if cur:
        raise SyntaxErrorDetail(f"Unexpected tokens in loop header: '{cur[0].lexeme}'.", lineNum)
    state.blockStack.append(('LOOP', lineNum, {'label': label}))


# IM OUTTA YR <label>
def checkLoopEnd(lineToks, lineNum, state):
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected loop label after 'IM OUTTA YR'.", lineNum)
    if len(lineToks) > 2:
        raise SyntaxErrorDetail(f"Unexpected tokens after 'IM OUTTA YR {lineToks[1].lexeme}'.", lineNum)
    if state.topBlockType() != 'LOOP':
        raise SyntaxErrorDetail("'IM OUTTA YR' found without matching 'IM IN YR'.", lineNum)
    expectedLabel = state.topBlockData()['label']
    if lineToks[1].lexeme != expectedLabel:
        raise SyntaxErrorDetail(f"Loop label mismatch: 'IM IN YR {expectedLabel}' closed by 'IM OUTTA YR {lineToks[1].lexeme}'.", lineNum)
    state.blockStack.pop()


# ---------- Functions: HOW IZ I / IF U SAY SO ----------

# HOW IZ I <name> [YR <param> [AN YR <param>]*]
def checkFunctionStart(lineToks, lineNum, state):
    if len(lineToks) < 2:
        raise SyntaxErrorDetail("Expected function identifier after 'HOW IZ I'.", lineNum)
    funcName = lineToks[1].lexeme
    cur = lineToks[2:]
    while cur:
        if cur[0].lexeme == "YR":
            cur = cur[1:]
        elif cur[0].lexeme == "AN" and len(cur) > 1 and cur[1].lexeme == "YR":
            cur = cur[2:]
        else:
            raise SyntaxErrorDetail(f"Unexpected token '{cur[0].lexeme}' in function parameter list.", lineNum)
        if not cur or not isValidIdentifier(cur[0].lexeme):
            raise SyntaxErrorDetail("Expected parameter identifier.", lineNum)
        cur = cur[1:]
    state.blockStack.append(('FUNC', lineNum, {'name': funcName}))


def checkFunctionEnd(lineToks, lineNum, state):
    expectNoExtraTokens(lineToks, "IF U SAY SO", lineNum)
    if state.topBlockType() != 'FUNC':
        raise SyntaxErrorDetail("'IF U SAY SO' found without matching 'HOW IZ I'.", lineNum)
    state.blockStack.pop()


def checkUnclosedBlocks(state):
    if state.inWazzup:
        raise SyntaxErrorDetail(f"Unclosed variable declaration block 'WAZZUP' starting at line {state.wazzupLine} (missing 'BUHBYE').", state.wazzupLine)

    if state.blockStack:
        blockType, startLine, data = state.blockStack[-1]
        if blockType == 'O RLY?':
            raise SyntaxErrorDetail(f"Unclosed conditional block 'O RLY?' starting at line {startLine} (missing 'OIC').", startLine)
        elif blockType == 'WTF?':
            raise SyntaxErrorDetail(f"Unclosed switch block 'WTF?' starting at line {startLine} (missing 'OIC').", startLine)
        elif blockType == 'LOOP':
            raise SyntaxErrorDetail(f"Unclosed loop 'IM IN YR {data['label']}' starting at line {startLine}.", startLine)
        elif blockType == 'FUNC':
            raise SyntaxErrorDetail(f"Unclosed function declaration 'HOW IZ I {data['name']}' starting at line {startLine}.", startLine)
