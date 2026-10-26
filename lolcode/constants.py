import re

# LOLCODE keywords and classifications
keywords = {
    "HAI": "Code Delimiter",
    "KTHXBYE": "Code Delimiter",
    "WAZZUP": "Variable Declaration Start",
    "BUHBYE": "Variable Declaration End",
    "I HAS A": "Variable Declaration",
    "ITZ": "Variable Assignment",
    "R": "Assignment Operator",
    "VISIBLE": "Output Keyword",
    "GIMMEH": "Input Keyword",
    "SUM OF": "Addition Operator",
    "DIFF OF": "Subtraction Operator",
    "PRODUKT OF": "Multiplication Operator",
    "QUOSHUNT OF": "Division Operator",
    "MOD OF": "Modulo Operator",
    "BIGGR OF": "Maximum Operator",
    "SMALLR OF": "Minimum Operator",
    "BOTH OF": "AND Operator",
    "EITHER OF": "OR Operator",
    "WON OF": "XOR Operator",
    "NOT": "NOT Operator",
    "ANY OF": "Infinite Arity OR",
    "ALL OF": "Infinite Arity AND",
    "BOTH SAEM": "Equality Operator",
    "DIFFRINT": "Inequality Operator",
    "SMOOSH": "Concatenation Operator",
    "MAEK": "Typecast Operator",
    "A": "Type Keyword",
    "IS NOW A": "Typecast Operator",
    "AN": "Operand Separator",
    "IT": "Implicit Variable",
    "O RLY?": "If-Then Start",
    "YA RLY": "If Branch",
    "MEBBE": "Else-If Branch",
    "NO WAI": "Else Branch",
    "OIC": "Control Flow End",
    "WTF?": "Switch Start",
    "OMG": "Case Keyword",
    "OMGWTF": "Default Keyword",
    "IM IN YR": "Loop Start",
    "IM OUTTA YR": "Loop End",
    "UPPIN": "Increment Operator",
    "NERFIN": "Decrement Operator",
    "YR": "Parameter Keyword",
    "TIL": "Until Keyword",
    "WILE": "While Keyword",
    "HOW IZ I": "Function Declaration",
    "IF U SAY SO": "Function End",
    "I IZ": "Function Call",
    "FOUND YR": "Return Keyword",
    "GTFO": "Break Keyword",
    "MKAY": "Expression End",
    "BTW": "Single Line Comment",
    "OBTW": "Multiline Comment Start",
    "TLDR": "Multiline Comment End"
}

types = {"NOOB", "NUMBR", "NUMBAR", "YARN", "TROOF"}

# Token classes ignored by the syntax checker
commentClasses = {
    "Single Line Comment",
    "Multiline Comment Start",
    "Multiline Comment End",
    "Comment Text"
}

# Binary arithmetic / logic / comparison operators: <op> <expr> AN <expr>
binaryOperators = {
    "SUM OF", "DIFF OF", "PRODUKT OF", "QUOSHUNT OF", "MOD OF",
    "BIGGR OF", "SMALLR OF", "BOTH OF", "EITHER OF", "WON OF",
    "BOTH SAEM", "DIFFRINT"
}

# Longest keywords are tried first so "IM OUTTA YR" wins over "YR", etc.
keywordPattern = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(word) for word in sorted(keywords, key=len, reverse=True)) + r")(?![A-Za-z0-9_])")
numberPattern = re.compile(r"-?[0-9]+(?:\.[0-9]+)?(?![A-Za-z0-9_.])")
identifierPattern = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
wordPattern = re.compile(r'[^\s"!,]+')
multilineEndPattern = re.compile(r"(?<![A-Za-z0-9_])TLDR(?![A-Za-z0-9_])")
stringPattern = re.compile(r'"[^"]*"')
