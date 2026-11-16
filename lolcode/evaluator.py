"""
evaluator.py - Semantic Analyzer and Evaluator for LOLCODE (v1.2).

This module handles semantic analysis and evaluation for LOLCODE programs:
1. Type coercion helpers (toTroof, toNumeric, castToYarn, castValue, isEqual)
2. Expression evaluation:
   - Literals (NUMBR, NUMBAR, YARN, TROOF)
   - Variable lookups (VAR)
   - Arithmetic operations (SUM OF, DIFF OF, PRODUKT OF, QUOSHUNT OF, MOD OF, BIGGR OF, SMALLR OF)
   - Boolean operations (NOT, BOTH OF, EITHER OF, WON OF, ALL OF, ANY OF)
   - Comparison operations (BOTH SAEM, DIFFRINT)
   - Typecasting (MAEK)
   - String concatenation (SMOOSH)
3. Control statement and statement evaluation:
   - Variable declarations (I HAS A ... ITZ)
   - Variable assignments (R)
   - In-place recasting (IS NOW A)
   - Conditionals (O RLY? / YA RLY / MEBBE / NO WAI / OIC)
   - Switch-case (WTF? / OMG / OMGWTF / GTFO / OIC)
   - Standalone expressions (assigns to IT)
   - Output (VISIBLE) and Input (GIMMEH)
4. Symbol table population via program execution.
"""

import re
from .constants import commentClasses
from .expressions import parseExpression
from .symbol_table import SymbolTable


# =============================================================================
# 1. TYPE COERCION & COMPARISON HELPERS
# =============================================================================

def toTroof(value, valueType):
    """
    Converts a value and its LOLCODE type to Python boolean (TROOF).
    LOLCODE 1.2 truthiness rules:
      - NOOB: always FAIL (False)
      - TROOF: 'WIN' is True, 'FAIL' is False
      - NUMBR / NUMBAR: zero (0 / 0.0) is False, non-zero is True
      - YARN: empty string ("") is False, non-empty is True
    """
    if valueType == "NOOB" or value is None:
        return False
    if valueType == "TROOF":
        return value == "WIN" if isinstance(value, str) else bool(value)
    if valueType in ("NUMBR", "NUMBAR"):
        return float(value) != 0.0
    if valueType == "YARN":
        return str(value) != ""

    raise ValueError(f"Cannot convert type '{valueType}' to TROOF.")


def toNumeric(val, valType, opName):
    """
    Coerces an operand to a numeric value (int or float) and type ('NUMBR' or 'NUMBAR').
    Per LOLCODE 1.2 math specifications:
      - NUMBR and NUMBAR are used directly.
      - YARN is parsed as an int if purely digits, or float if containing a decimal point.
      - TROOF converts: WIN -> 1, FAIL -> 0 (NUMBR).
      - NOOB cannot be implicitly cast to numeric, raising ValueError.
    """
    if valType == "NUMBR":
        return int(val), "NUMBR"
    if valType == "NUMBAR":
        return float(val), "NUMBAR"
    if valType == "TROOF":
        return (1 if toTroof(val, valType) else 0), "NUMBR"
    if valType == "YARN":
        s = str(val).strip()
        if re.fullmatch(r"-?\d+", s):
            return int(s), "NUMBR"
        if re.fullmatch(r"-?\d+\.\d+", s):
            return float(s), "NUMBAR"
        raise ValueError(f"Cannot cast YARN '{val}' to numeric in '{opName}'.")
    raise ValueError(f"Cannot cast '{valType}' to numeric in '{opName}'.")


def castToYarn(value, valueType):
    """
    Converts any LOLCODE value to its string representation (YARN).
    """
    if valueType == "NOOB" or value is None:
        return ""
    if valueType == "TROOF":
        return "WIN" if toTroof(value, valueType) else "FAIL"
    if valueType == "NUMBAR":
        text = str(value)
        # Preserve standard float representation without redundant exponential formatting
        return text
    return str(value)


def castValue(value, valueType, targetType):
    """
    Explicitly casts a value to a target LOLCODE type (MAEK / IS NOW A).
    Supported target types: TROOF, NUMBR, NUMBAR, YARN, NOOB.
    """
    # 1. Cast to TROOF
    if targetType == "TROOF":
        result = toTroof(value, valueType)
        return ("WIN" if result else "FAIL"), "TROOF"

    # 2. Cast to NUMBR or NUMBAR
    if targetType in ("NUMBR", "NUMBAR"):
        if valueType == "YARN":
            s = str(value).strip()
            if not re.fullmatch(r"-?\d+(\.\d+)?", s):
                raise ValueError(f"Cannot convert YARN '{value}' to {targetType}.")
            num = float(s)
            if targetType == "NUMBR":
                return int(num), "NUMBR"
            return num, "NUMBAR"

        if valueType == "NOOB" or value is None:
            num = 0
        elif valueType == "TROOF":
            num = 1 if toTroof(value, valueType) else 0
        elif valueType in ("NUMBR", "NUMBAR"):
            num = value
        else:
            raise ValueError(f"Cannot convert '{valueType}' to {targetType}.")

        if targetType == "NUMBR":
            return int(float(num)), "NUMBR"
        return float(num), "NUMBAR"

    # 3. Cast to YARN
    if targetType == "YARN":
        return castToYarn(value, valueType), "YARN"

    # 4. Cast to NOOB
    if targetType == "NOOB":
        return None, "NOOB"

    raise ValueError(f"Invalid target type '{targetType}' in typecast.")


def isEqual(leftVal, leftType, rightVal, rightType):
    """
    Evaluates equality between two values according to LOLCODE 1.2 rules:
      - If both are numerical (NUMBR or NUMBAR), numerical comparison is used.
      - If both have the same type, values are compared directly.
      - Otherwise, strict type matching applies and equality evaluates to False
        (no automatic cross-type casting between non-numerics).
    """
    if leftType in ("NUMBR", "NUMBAR") and rightType in ("NUMBR", "NUMBAR"):
        return float(leftVal) == float(rightVal)
    if leftType == rightType:
        return leftVal == rightVal
    return False


# =============================================================================
# 2. EXPRESSION EVALUATION
# =============================================================================

def evaluateExpression(tree, table):
    """
    Recursively evaluates an AST expression node produced by parseExpression.
    Returns a tuple of (evaluatedValue, evaluatedType).
    """
    op = tree[0]

    # --- Literals ---
    if op == "NUMBR Literal":
        return int(tree[1]), "NUMBR"

    if op == "NUMBAR Literal":
        return float(tree[1]), "NUMBAR"

    if op == "YARN":
        return tree[1], "YARN"

    if op == "TROOF":
        return tree[1], "TROOF"

    # --- Variable Lookup ---
    if op == "VAR":
        varName = tree[1]
        symbol = table.lookup(varName)

        if symbol is None:
            raise ValueError(f"Undeclared variable '{varName}'.")

        if symbol.type == "NOOB":
            raise ValueError(f"Variable '{varName}' is uninitialized.")

        value = symbol.value
        if symbol.type == "NUMBR":
            value = int(value)
        elif symbol.type == "NUMBAR":
            value = float(value)

        return value, symbol.type

    # --- Arithmetic Operators ---
    # SUM OF, DIFF OF, PRODUKT OF, QUOSHUNT OF, MOD OF, BIGGR OF, SMALLR OF
    if op in ("SUM OF", "DIFF OF", "PRODUKT OF",
              "QUOSHUNT OF", "MOD OF", "BIGGR OF", "SMALLR OF"):

        leftRaw, leftTypeRaw = evaluateExpression(tree[1], table)
        rightRaw, rightTypeRaw = evaluateExpression(tree[2], table)

        left, leftType = toNumeric(leftRaw, leftTypeRaw, op)
        right, rightType = toNumeric(rightRaw, rightTypeRaw, op)

        # Division or modulo by zero check
        if op in ("QUOSHUNT OF", "MOD OF"):
            if right == 0:
                raise ZeroDivisionError(f"Division by zero in '{op}'.")

        # Integer math: if both operands are NUMBR, result is NUMBR
        if leftType == "NUMBR" and rightType == "NUMBR":
            if op == "SUM OF":
                res = left + right
            elif op == "DIFF OF":
                res = left - right
            elif op == "PRODUKT OF":
                res = left * right
            elif op == "QUOSHUNT OF":
                res = left // right
            elif op == "MOD OF":
                res = left % right
            elif op == "BIGGR OF":
                res = max(left, right)
            elif op == "SMALLR OF":
                res = min(left, right)
            return res, "NUMBR"

        # Floating-point math: if either operand is NUMBAR, result is NUMBAR
        l = float(left)
        r = float(right)
        if op == "SUM OF":
            res = l + r
        elif op == "DIFF OF":
            res = l - r
        elif op == "PRODUKT OF":
            res = l * r
        elif op == "QUOSHUNT OF":
            res = l / r
        elif op == "MOD OF":
            res = l % r
        elif op == "BIGGR OF":
            res = max(l, r)
        elif op == "SMALLR OF":
            res = min(l, r)
        return res, "NUMBAR"

    # --- Boolean Operators ---
    # Unary NOT
    if op == "NOT":
        val, valType = evaluateExpression(tree[1], table)
        res = not toTroof(val, valType)
        return ("WIN" if res else "FAIL"), "TROOF"

    # Binary Boolean: BOTH OF (AND), EITHER OF (OR), WON OF (XOR)
    if op in ("BOTH OF", "EITHER OF", "WON OF"):
        left, leftType = evaluateExpression(tree[1], table)
        right, rightType = evaluateExpression(tree[2], table)

        lBool = toTroof(left, leftType)
        rBool = toTroof(right, rightType)

        if op == "BOTH OF":
            res = lBool and rBool
        elif op == "EITHER OF":
            res = lBool or rBool
        elif op == "WON OF":
            res = (lBool != rBool)

        return ("WIN" if res else "FAIL"), "TROOF"

    # Infinite Arity Boolean: ALL OF, ANY OF
    if op in ("ALL OF", "ANY OF"):
        args = tree[1]
        if op == "ALL OF":
            for arg in args:
                val, vtype = evaluateExpression(arg, table)
                if not toTroof(val, vtype):
                    return "FAIL", "TROOF"
            return "WIN", "TROOF"
        else:  # ANY OF
            for arg in args:
                val, vtype = evaluateExpression(arg, table)
                if toTroof(val, vtype):
                    return "WIN", "TROOF"
            return "FAIL", "TROOF"

    # --- Comparison Operators ---
    # BOTH SAEM (==), DIFFRINT (!=)
    if op in ("BOTH SAEM", "DIFFRINT"):
        left, leftType = evaluateExpression(tree[1], table)
        right, rightType = evaluateExpression(tree[2], table)

        eq = isEqual(left, leftType, right, rightType)
        res = eq if op == "BOTH SAEM" else (not eq)
        return ("WIN" if res else "FAIL"), "TROOF"

    # --- Typecasting: MAEK <expr> [A] <type> ---
    if op == "MAEK":
        val, valType = evaluateExpression(tree[1], table)
        targetType = tree[2]
        return castValue(val, valType, targetType)

    # --- String Concatenation: SMOOSH ---
    if op == "SMOOSH":
        parts = []
        for arg in tree[1]:
            val, vtype = evaluateExpression(arg, table)
            parts.append(castToYarn(val, vtype))
        return "".join(parts), "YARN"

    raise NotImplementedError(f"Evaluation for '{op}' is not yet implemented.")


# =============================================================================
# 3. CONTROL STATEMENT BLOCK PARSERS
# =============================================================================

def parseORlyBlock(lines, startIdx):
    """
    Parses a conditional block starting at 'O RLY?' through its matching 'OIC'.
    Returns a dictionary with:
      - 'yaRly': list of (lineNum, lineToks) in YA RLY branch
      - 'mebbe': list of (exprToks, [(lineNum, lineToks)]) for each MEBBE branch
      - 'noWai': list of (lineNum, lineToks) in NO WAI branch (or None)
    and the index of the closing 'OIC'.
    Correctly accounts for nested conditional and switch blocks.
    """
    yaRlyLines = []
    mebbeBranches = []
    noWaiLines = None
    currentTarget = None
    nestedDepth = 0

    for j in range(startIdx + 1, len(lines)):
        lineNum, lineToks = lines[j]
        firstLex = lineToks[0].lexeme

        if firstLex in ("O RLY?", "WTF?"):
            nestedDepth += 1
            if currentTarget is not None:
                currentTarget.append(lines[j])
        elif firstLex == "OIC":
            if nestedDepth > 0:
                nestedDepth -= 1
                if currentTarget is not None:
                    currentTarget.append(lines[j])
            else:
                return {
                    "yaRly": yaRlyLines,
                    "mebbe": mebbeBranches,
                    "noWai": noWaiLines
                }, j
        elif nestedDepth == 0:
            if firstLex == "YA RLY":
                currentTarget = yaRlyLines
            elif firstLex == "MEBBE":
                branchLines = []
                # lineToks[1:] contains the MEBBE condition expression
                mebbeBranches.append((lineToks[1:], branchLines))
                currentTarget = branchLines
            elif firstLex == "NO WAI":
                noWaiLines = []
                currentTarget = noWaiLines
            else:
                if currentTarget is not None:
                    currentTarget.append(lines[j])
        else:
            if currentTarget is not None:
                currentTarget.append(lines[j])

    raise ValueError("Unclosed conditional block 'O RLY?' (missing 'OIC').")


def parseWtfBlock(lines, startIdx):
    """
    Parses a switch block starting at 'WTF?' through its matching 'OIC'.
    Returns a dictionary with:
      - 'cases': list of (caseValToks, [(lineNum, lineToks)]) for each OMG case
      - 'default': list of (lineNum, lineToks) in OMGWTF (or None)
    and the index of the closing 'OIC'.
    Correctly accounts for nested conditional and switch blocks.
    """
    cases = []
    defaultLines = None
    currentTarget = None
    nestedDepth = 0

    for j in range(startIdx + 1, len(lines)):
        lineNum, lineToks = lines[j]
        firstLex = lineToks[0].lexeme

        if firstLex in ("O RLY?", "WTF?"):
            nestedDepth += 1
            if currentTarget is not None:
                currentTarget.append(lines[j])
        elif firstLex == "OIC":
            if nestedDepth > 0:
                nestedDepth -= 1
                if currentTarget is not None:
                    currentTarget.append(lines[j])
            else:
                return {
                    "cases": cases,
                    "default": defaultLines
                }, j
        elif nestedDepth == 0:
            if firstLex == "OMG":
                caseLines = []
                # lineToks[1:] contains the literal case value
                cases.append((lineToks[1:], caseLines))
                currentTarget = caseLines
            elif firstLex == "OMGWTF":
                defaultLines = []
                currentTarget = defaultLines
            else:
                if currentTarget is not None:
                    currentTarget.append(lines[j])
        else:
            if currentTarget is not None:
                currentTarget.append(lines[j])

    raise ValueError("Unclosed switch block 'WTF?' (missing 'OIC').")


# =============================================================================
# 4. STATEMENT & PROGRAM EXECUTION
# =============================================================================

def executeStatements(lines, table, on_output=None, on_input=None):
    """
    Executes a sequence of (lineNum, lineToks) statements against the SymbolTable.
    Handles assignments, declarations, recasting, conditionals, switches, and expressions.
    Returns 'BREAK' if GTFO was executed (to break out of switch/case), else None.
    """
    i = 0
    while i < len(lines):
        lineNum, lineToks = lines[i]
        first = lineToks[0]

        # Ignore structural delimiter lines
        if first.lexeme in ("CAN HAS STDIO?", "CAN HAS", "WAZZUP", "BUHBYE"):
            i += 1
            continue

        # Break keyword: GTFO
        if first.lexeme == "GTFO":
            return "BREAK"

        # Variable Declaration: I HAS A <var> [ITZ <expr>]
        if first.lexeme == "I HAS A":
            varName = lineToks[1].lexeme
            table.declare(varName)
            if len(lineToks) > 2 and lineToks[2].lexeme == "ITZ":
                exprTree, remaining = parseExpression(lineToks[3:])
                if remaining:
                    raise ValueError(f"Unexpected tokens after initialization of '{varName}'.")
                val, valType = evaluateExpression(exprTree, table)
                table.assign(varName, val, valType)
            i += 1
            continue

        # Variable Assignment: <var> R <expr>
        if len(lineToks) >= 2 and lineToks[1].lexeme == "R":
            varName = lineToks[0].lexeme
            if not table.isDeclared(varName):
                raise ValueError(f"Cannot assign to undeclared variable '{varName}'.")
            exprTree, remaining = parseExpression(lineToks[2:])
            if remaining:
                raise ValueError(f"Unexpected tokens after assignment expression for '{varName}'.")
            val, valType = evaluateExpression(exprTree, table)
            table.assign(varName, val, valType)
            i += 1
            continue

        # Typecasting assignment: <var> IS NOW A <type>
        if len(lineToks) >= 3 and lineToks[1].lexeme == "IS NOW A":
            varName = lineToks[0].lexeme
            targetType = lineToks[2].lexeme
            sym = table.lookup(varName)
            if sym is None:
                raise ValueError(f"Cannot recast undeclared variable '{varName}'.")
            val, valType = castValue(sym.value, sym.type, targetType)
            table.assign(varName, val, valType)
            i += 1
            continue

        # Output statement: VISIBLE <expr>+ [!]
        if first.lexeme == "VISIBLE":
            cur = lineToks[1:]
            newline = bool(cur) and cur[-1].lexeme == "!"
            if newline:
                cur = cur[:-1]
            output = ""
            while cur:
                exprTree, cur = parseExpression(cur)
                val, valType = evaluateExpression(exprTree, table)
                # In LOLCODE 1.2, IT stores the result of the expression
                table.assign("IT", val, valType)
                output = output + castToYarn(val, valType)
            if newline:
                output = output + "\n"
            if on_output:
                on_output(output)
            i += 1
            continue

        # Input statement: GIMMEH <var>
        if first.lexeme == "GIMMEH":
            varName = lineToks[1].lexeme
            if not table.isDeclared(varName):
                raise ValueError(f"Cannot store input into undeclared variable '{varName}'.")
            value = on_input(varName) if on_input else ""
            table.assign(varName, value, "YARN")
            i += 1
            continue

        # Conditional Control Statement: O RLY?
        if first.lexeme == "O RLY?":
            blockInfo, endIdx = parseORlyBlock(lines, i)
            itSym = table.lookup("IT")
            condTruth = toTroof(itSym.value, itSym.type)

            if condTruth:
                signal = executeStatements(blockInfo["yaRly"], table)
                if signal == "BREAK":
                    return "BREAK"
            else:
                executed = False
                for mebbeExprToks, mebbeLines in blockInfo["mebbe"]:
                    exprTree, remaining = parseExpression(mebbeExprToks)
                    if remaining:
                        raise ValueError(f"Unexpected tokens after 'MEBBE' expression at line {lineNum}.")
                    mVal, mType = evaluateExpression(exprTree, table)
                    table.assign("IT", mVal, mType)  # MEBBE expression sets IT
                    if toTroof(mVal, mType):
                        signal = executeStatements(mebbeLines, table)
                        if signal == "BREAK":
                            return "BREAK"
                        executed = True
                        break

                if not executed and blockInfo["noWai"] is not None:
                    signal = executeStatements(blockInfo["noWai"], table)
                    if signal == "BREAK":
                        return "BREAK"

            i = endIdx + 1
            continue

        # Switch Control Statement: WTF?
        if first.lexeme == "WTF?":
            blockInfo, endIdx = parseWtfBlock(lines, i)
            itSym = table.lookup("IT")
            matched = False

            for caseValToks, caseLines in blockInfo["cases"]:
                if not matched:
                    cTree, remaining = parseExpression(caseValToks)
                    if remaining:
                        raise ValueError(f"Unexpected tokens after 'OMG' value at line {lineNum}.")
                    cVal, cType = evaluateExpression(cTree, table)
                    if isEqual(itSym.value, itSym.type, cVal, cType):
                        matched = True

                if matched:
                    signal = executeStatements(caseLines, table)
                    if signal == "BREAK":
                        break

            # If no OMG case matched, execute the default OMGWTF case
            if not matched and blockInfo["default"] is not None:
                executeStatements(blockInfo["default"], table)

            i = endIdx + 1
            continue

        # Standalone expression statement (evaluates and assigns result to IT)
        try:
            exprTree, remaining = parseExpression(lineToks)
            if not remaining:
                val, valType = evaluateExpression(exprTree, table)
                table.assign("IT", val, valType)
                i += 1
                continue
        except Exception:
            pass

        i += 1

    return None


def buildSymbolTable(tokens, on_output=None, on_input=None):
    """
    Executes the LOLCODE program represented by tokens and returns the populated SymbolTable.
    Executes declarations, assignments, arithmetic, boolean, comparisons, typecasting,
    and control statements (O RLY? / WTF?).
    """
    table = SymbolTable()

    execTokens = [t for t in tokens if t.classification not in commentClasses]

    # Find HAI and KTHXBYE boundaries if present
    startLine = None
    endLine = None
    for t in execTokens:
        if t.lexeme == "HAI" and startLine is None:
            startLine = t.line
        elif t.lexeme == "KTHXBYE":
            endLine = t.line

    linesDict = {}
    for t in execTokens:
        if startLine is not None and endLine is not None:
            if startLine < t.line < endLine:
                linesDict.setdefault(t.line, []).append(t)
        else:
            linesDict.setdefault(t.line, []).append(t)

    bodyLines = sorted(linesDict.items())
    executeStatements(bodyLines, table, on_output, on_input)

    return table

