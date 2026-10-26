import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
import os
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
keywordPattern = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(word) for word in sorted(keywords, key=len, reverse=True)) + r")(?![A-Za-z0-9_])")
numberPattern = re.compile(r"-?[0-9]+(?:\.[0-9]+)?(?![A-Za-z0-9_.])")
identifierPattern = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
wordPattern = re.compile(r'[^\s"!,]+')

class Token:
    def __init__(self, lexeme, classification, line):
        self.lexeme = lexeme
        self.classification = classification
        self.line = line

    def __iter__(self):
        yield self.lexeme
        yield self.classification

    def __getitem__(self, index):
        return (self.lexeme, self.classification, self.line)[index]

    def __repr__(self):
        return f"Token({self.lexeme!r}, {self.classification!r}, line={self.line})"

class SyntaxErrorDetail(Exception):
    def __init__(self, message, line=None):
        super().__init__(message)
        self.message = message
        self.line = line

    def __str__(self):
        if self.line is not None:
            return f"Syntax Error at line {self.line}: {self.message}"
        return f"Syntax Error: {self.message}"

def formatCode(code):
    return code.expandtabs(4)

def openFile():
    filePath = filedialog.askopenfilename(
        title="Open LOLCODE File",
        filetypes=[("LOLCODE Files", "*.lol"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filePath:
        with open(filePath, "r", encoding="utf-8") as file:
            code = file.read()
        code = formatCode(code)
        textEditor.delete("1.0", tk.END)
        textEditor.insert("1.0", code)
        textEditor.tag_remove("error_highlight", "1.0", tk.END)
        fileSelector.set(os.path.basename(filePath))
        statusBar.config(text=f"Loaded {os.path.basename(filePath)}", fg="black")

def isValidIdentifier(word):
    return identifierPattern.fullmatch(word) is not None

def classifyIdentifier(word, previous):
    if not isValidIdentifier(word):
        return "Unrecognized Lexeme"
    if word in types:
        return "Type Literal"
    if word == "WIN" or word == "FAIL":
        return "TROOF Literal"
    if previous == "HOW IZ I" or previous == "I IZ":
        return "Function Identifier"
    if previous == "IM IN YR" or previous == "IM OUTTA YR":
        return "Loop Identifier"
    return "Variable Identifier"

def tokenize(code):
    tokens = []
    multilineComment = False
    multilineStartLine = None
    lex_errors = []

    for line_num, line in enumerate(code.splitlines(), start=1):
        position = 0
        previous = ""
        while position < len(line):
            # For a multiline comment
            if multilineComment:
                # Searches for TLDR and checks the characters before and after it
                end = re.search(r"(?<![A-Za-z0-9_])TLDR(?![A-Za-z0-9_])", line[position:])
                if end:
                    endPosition = position + end.start()
                    # Checks if there is a comment before TLDR
                    if endPosition > position:
                        tokens.append(Token(line[position:endPosition], "Comment Text", line_num))
                    tokens.append(Token("TLDR", "Multiline Comment End", line_num))
                    position = position + end.end()
                    multilineComment = False
                else:
                    if line[position:]:
                        tokens.append(Token(line[position:], "Comment Text", line_num))
                    break
                continue

            # Skips the position if it is a space
            if line[position].isspace():
                position += 1
                continue

            # Matches a keyword 
            match = keywordPattern.match(line, position)
            if match:
                word = match.group()
                tokens.append(Token(word, keywords[word], line_num))
                position = match.end()
                previous = word

                # If the keyword is BTW, means it is a comment
                if word == "BTW":
                    if position < len(line):
                        tokens.append(Token(line[position:], "Comment Text", line_num))
                    break

                # Sets the multiline comment flag to true
                if word == "OBTW":
                    multilineComment = True
                    multilineStartLine = line_num
                continue

            # If it is a ", detects that it is a YARN literal
            if line[position] == '"':
                match = re.match(r'"[^"]*"', line[position:])
                if match:
                    word = match.group()
                    tokens.append(Token('"', "String Delimiter", line_num))
                    tokens.append(Token(word[1:-1], "YARN Literal", line_num))
                    tokens.append(Token('"', "String Delimiter", line_num))
                    position += len(word)
                else:
                    lex_errors.append((f"Lexical Error at line {line_num}: Unclosed string literal.", line_num))
                    tokens.append(Token('"', "Unrecognized Lexeme", line_num))
                    position += 1
                previous = ""
                continue

            # Matches a number
            match = numberPattern.match(line, position)
            if match:
                word = match.group()
                # If it is a float NUMBAR, else NUMBR
                if "." in word:
                    tokens.append(Token(word, "NUMBAR Literal", line_num))
                else:
                    tokens.append(Token(word, "NUMBR Literal", line_num))
                position = match.end()
                previous = ""
                continue

            # Matches an identifier
            match = wordPattern.match(line, position)
            if match:
                word = match.group()
                classification = classifyIdentifier(word, previous)
                tokens.append(Token(word, classification, line_num))
                position = match.end()
                if classification == "Unrecognized Lexeme":
                    lex_errors.append((f"Lexical Error at line {line_num}: Unrecognized lexeme '{word}'.", line_num))
                    previous = ""
                else:
                    previous = word
                continue

            # If unrecognized
            ch = line[position]
            lex_errors.append((f"Lexical Error at line {line_num}: Unrecognized lexeme '{ch}'.", line_num))
            tokens.append(Token(ch, "Unrecognized Lexeme", line_num))
            position += 1
            previous = ""

    if multilineComment:
        lex_errors.append((f"Syntax Error: Unclosed multiline comment 'OBTW' starting at line {multilineStartLine} (missing 'TLDR').", multilineStartLine))

    return tokens, lex_errors

def parseExpression(toks):
    if not toks:
        raise SyntaxErrorDetail("Expected expression, but line ended unexpectedly.")

    tok = toks[0]

    # YARN literal (with string delimiters or standalone)
    if tok.lexeme == '"':
        if len(toks) >= 3 and toks[1].classification == "YARN Literal" and toks[2].lexeme == '"':
            return ("YARN", toks[1].lexeme), toks[3:]
        raise SyntaxErrorDetail("Malformed string literal.", tok.line)

    if tok.classification == "YARN Literal":
        return ("YARN", tok.lexeme), toks[1:]

    # NUMBR / NUMBAR
    if tok.classification in ("NUMBR Literal", "NUMBAR Literal"):
        return (tok.classification, tok.lexeme), toks[1:]

    # TROOF Literal (WIN / FAIL)
    if tok.classification == "TROOF Literal" or tok.lexeme in ("WIN", "FAIL"):
        return ("TROOF", tok.lexeme), toks[1:]

    # Type Literal
    if tok.classification == "Type Literal" or tok.lexeme in types:
        return ("TYPE", tok.lexeme), toks[1:]

    # Variable Identifier or IT
    if tok.classification in ("Variable Identifier", "Implicit Variable") or tok.lexeme == "IT" or isValidIdentifier(tok.lexeme):
        return ("VAR", tok.lexeme), toks[1:]

    # Unary NOT
    if tok.lexeme == "NOT":
        expr, rest = parseExpression(toks[1:])
        return ("NOT", expr), rest

    # Binary arithmetic / logic / comparison
    binary_ops = {
        "SUM OF", "DIFF OF", "PRODUKT OF", "QUOSHUNT OF", "MOD OF",
        "BIGGR OF", "SMALLR OF", "BOTH OF", "EITHER OF", "WON OF",
        "BOTH SAEM", "DIFFRINT"
    }
    if tok.lexeme in binary_ops:
        op = tok.lexeme
        e1, rest1 = parseExpression(toks[1:])
        if not rest1:
            raise SyntaxErrorDetail(f"'{op}' expects 2 operands separated by 'AN'.", tok.line)
        if rest1[0].lexeme != "AN":
            raise SyntaxErrorDetail(f"Expected 'AN' after first operand of '{op}', found '{rest1[0].lexeme}'.", rest1[0].line)
        e2, rest2 = parseExpression(rest1[1:])
        return (op, e1, e2), rest2

    # MAEK <expr> [A] <type>
    if tok.lexeme == "MAEK":
        e, rest = parseExpression(toks[1:])
        if rest and rest[0].lexeme == "A":
            rest = rest[1:]
        if not rest:
            raise SyntaxErrorDetail("Expected type in 'MAEK' expression.", tok.line)
        type_tok = rest[0]
        if type_tok.lexeme not in types and type_tok.classification != "Type Literal":
            raise SyntaxErrorDetail(f"Invalid type '{type_tok.lexeme}' in 'MAEK' expression.", type_tok.line)
        return ("MAEK", e, type_tok.lexeme), rest[1:]

    # SMOOSH <expr> [AN <expr>]* [MKAY]
    if tok.lexeme == "SMOOSH":
        cur_toks = toks[1:]
        args = []
        e, cur_toks = parseExpression(cur_toks)
        args.append(e)
        while cur_toks:
            if cur_toks[0].lexeme == "MKAY":
                cur_toks = cur_toks[1:]
                break
            if cur_toks[0].lexeme == "AN":
                cur_toks = cur_toks[1:]
            try:
                e, cur_toks = parseExpression(cur_toks)
                args.append(e)
            except SyntaxErrorDetail:
                break
        return ("SMOOSH", args), cur_toks

    # ALL OF / ANY OF <expr> [AN <expr>]* MKAY
    if tok.lexeme in ("ALL OF", "ANY OF"):
        op = tok.lexeme
        cur_toks = toks[1:]
        args = []
        e, cur_toks = parseExpression(cur_toks)
        args.append(e)
        while cur_toks and cur_toks[0].lexeme != "MKAY":
            if cur_toks[0].lexeme == "AN":
                cur_toks = cur_toks[1:]
            e, cur_toks = parseExpression(cur_toks)
            args.append(e)
        if not cur_toks or cur_toks[0].lexeme != "MKAY":
            raise SyntaxErrorDetail(f"Expected 'MKAY' to close '{op}'.", tok.line)
        return (op, args), cur_toks[1:]

    # Function call: I IZ <func> [YR <arg> [AN YR <arg>]*] [MKAY]
    if tok.lexeme == "I IZ":
        cur_toks = toks[1:]
        if not cur_toks or not isValidIdentifier(cur_toks[0].lexeme):
            raise SyntaxErrorDetail("Expected function identifier after 'I IZ'.", tok.line)
        func_name = cur_toks[0].lexeme
        cur_toks = cur_toks[1:]
        args = []
        while cur_toks and cur_toks[0].lexeme != "MKAY":
            if cur_toks[0].lexeme == "YR":
                cur_toks = cur_toks[1:]
            elif cur_toks[0].lexeme == "AN":
                cur_toks = cur_toks[1:]
                if cur_toks and cur_toks[0].lexeme == "YR":
                    cur_toks = cur_toks[1:]
            else:
                break
            arg_expr, cur_toks = parseExpression(cur_toks)
            args.append(arg_expr)
        if cur_toks and cur_toks[0].lexeme == "MKAY":
            cur_toks = cur_toks[1:]
        return ("CALL", func_name, args), cur_toks

    raise SyntaxErrorDetail(f"Unexpected token '{tok.lexeme}' in expression.", tok.line)

def checkSyntax(tokens):
    comment_classes = {
        "Single Line Comment",
        "Multiline Comment Start",
        "Multiline Comment End",
        "Comment Text"
    }

    # Executable tokens
    exec_tokens = [t for t in tokens if t.classification not in comment_classes]

    if not exec_tokens:
        raise SyntaxErrorDetail("Program is empty. Expected 'HAI' and 'KTHXBYE'.")

    # Locate HAI and KTHXBYE 
    hai_tokens = [t for t in exec_tokens if t.lexeme == "HAI"]
    kthx_tokens = [t for t in exec_tokens if t.lexeme in ("KTHXBYE")]

    if not hai_tokens and not kthx_tokens:
        raise SyntaxErrorDetail(f"Program must start with 'HAI' and end with 'KTHXBYE'. First token '{exec_tokens[0].lexeme}' found on line {exec_tokens[0].line}.", exec_tokens[0].line)

    if not hai_tokens:
        raise SyntaxErrorDetail(f"Found closing delimiter '{kthx_tokens[0].lexeme}' at line {kthx_tokens[0].line} without opening 'HAI'.", kthx_tokens[0].line)

    if not kthx_tokens:
        raise SyntaxErrorDetail(f"Program starts with 'HAI' at line {hai_tokens[0].line}, but is missing closing 'KTHXBYE'.", hai_tokens[0].line)

    if len(hai_tokens) > 1:
        raise SyntaxErrorDetail("Multiple 'HAI' code delimiters found.", hai_tokens[1].line)

    if len(kthx_tokens) > 1:
        raise SyntaxErrorDetail(f"Multiple '{kthx_tokens[1].lexeme}' code delimiters found.", kthx_tokens[1].line)

    hai_tok = hai_tokens[0]
    kthx_tok = kthx_tokens[0]

    if kthx_tok.line < hai_tok.line:
        raise SyntaxErrorDetail(f"Closing delimiter '{kthx_tok.lexeme}' on line {kthx_tok.line} cannot appear before 'HAI' on line {hai_tok.line}.", kthx_tok.line)

    # Check for executable code before HAI
    for t in exec_tokens:
        if t.line < hai_tok.line:
            raise SyntaxErrorDetail(f"Unexpected statement '{t.lexeme}' before 'HAI'.", t.line)

    # Tokens on HAI line
    hai_line_tokens = [t for t in exec_tokens if t.line == hai_tok.line]
    if hai_line_tokens[0] != hai_tok:
        raise SyntaxErrorDetail(f"Unexpected token '{hai_line_tokens[0].lexeme}' before 'HAI'.", hai_tok.line)

    if len(hai_line_tokens) > 2:
        raise SyntaxErrorDetail(f"Unexpected tokens after 'HAI' on line {hai_tok.line}.", hai_tok.line)
    elif len(hai_line_tokens) == 2:
        version_tok = hai_line_tokens[1]
        if version_tok.classification not in ("NUMBAR Literal", "NUMBR Literal"):
            raise SyntaxErrorDetail(f"Invalid LOLCODE version '{version_tok.lexeme}' after 'HAI'. Expected a number.", hai_tok.line)

    # Tokens on KTHXBYE line
    kthx_line_tokens = [t for t in exec_tokens if t.line == kthx_tok.line]
    if len(kthx_line_tokens) > 1:
        other = [t for t in kthx_line_tokens if t != kthx_tok][0]
        raise SyntaxErrorDetail(f"Unexpected token '{other.lexeme}' on '{kthx_tok.lexeme}' line.", kthx_tok.line)

    # Check for executable code after KTHXBYE
    for t in exec_tokens:
        if t.line > kthx_tok.line:
            raise SyntaxErrorDetail(f"Unexpected statement '{t.lexeme}' after closing '{kthx_tok.lexeme}'.", t.line)

    # Group lines between HAI and KTHXBYE
    lines_dict = {}
    for t in exec_tokens:
        if hai_tok.line < t.line < kthx_tok.line:
            lines_dict.setdefault(t.line, []).append(t)

    # Parse statements
    in_wazzup = False
    wazzup_line = None
    block_stack = []

    for line_num in sorted(lines_dict.keys()):
        line_toks = lines_dict[line_num]
        if not line_toks:
            continue

        first = line_toks[0]

        # WAZZUP block
        if first.lexeme == "WAZZUP":
            if in_wazzup:
                raise SyntaxErrorDetail("Nested 'WAZZUP' is not allowed.", line_num)
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'WAZZUP'.", line_num)
            in_wazzup = True
            wazzup_line = line_num
            continue

        if first.lexeme == "BUHBYE":
            if not in_wazzup:
                raise SyntaxErrorDetail("'BUHBYE' found without matching 'WAZZUP'.", line_num)
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'BUHBYE'.", line_num)
            in_wazzup = False
            continue

        if in_wazzup and first.lexeme != "I HAS A":
            raise SyntaxErrorDetail(f"Only variable declarations ('I HAS A') are allowed inside 'WAZZUP'...'BUHBYE'. Found '{first.lexeme}'.", line_num)

        # I HAS A <var> [ITZ <expr>]
        if first.lexeme == "I HAS A":
            if len(line_toks) < 2:
                raise SyntaxErrorDetail("Expected variable identifier after 'I HAS A'.", line_num)
            var_tok = line_toks[1]
            if not isValidIdentifier(var_tok.lexeme) or var_tok.classification not in ("Variable Identifier", "Loop Identifier", "Function Identifier"):
                raise SyntaxErrorDetail(f"Invalid variable identifier '{var_tok.lexeme}'.", line_num)

            if len(line_toks) > 2:
                if line_toks[2].lexeme != "ITZ":
                    raise SyntaxErrorDetail(f"Unexpected token '{line_toks[2].lexeme}' in variable declaration. Expected 'ITZ' or newline.", line_num)
                if len(line_toks) == 3:
                    raise SyntaxErrorDetail("Expected expression after 'ITZ'.", line_num)
                expr, rest = parseExpression(line_toks[3:])
                if rest:
                    raise SyntaxErrorDetail(f"Unexpected token '{rest[0].lexeme}' after variable initialization.", line_num)
            continue

        # <var> R <expr>
        if len(line_toks) >= 2 and line_toks[1].lexeme == "R":
            if first.classification != "Variable Identifier" and not isValidIdentifier(first.lexeme):
                raise SyntaxErrorDetail(f"Invalid target '{first.lexeme}' for assignment 'R'.", line_num)
            if len(line_toks) == 2:
                raise SyntaxErrorDetail("Expected expression after 'R'.", line_num)
            expr, rest = parseExpression(line_toks[2:])
            if rest:
                raise SyntaxErrorDetail(f"Unexpected token '{rest[0].lexeme}' after assignment expression.", line_num)
            continue

        # <var> IS NOW A <type>
        if len(line_toks) >= 2 and line_toks[1].lexeme == "IS NOW A":
            if len(line_toks) < 3:
                raise SyntaxErrorDetail("Expected type after 'IS NOW A'.", line_num)
            if line_toks[2].lexeme not in types and line_toks[2].classification != "Type Literal":
                raise SyntaxErrorDetail(f"Invalid type '{line_toks[2].lexeme}' after 'IS NOW A'.", line_num)
            if len(line_toks) > 3:
                raise SyntaxErrorDetail(f"Unexpected token '{line_toks[3].lexeme}' after type.", line_num)
            continue

        # VISIBLE <expr>+ [!]
        if first.lexeme == "VISIBLE":
            if len(line_toks) < 2:
                raise SyntaxErrorDetail("Expected expression after 'VISIBLE'.", line_num)
            cur = line_toks[1:]
            if cur[-1].lexeme == "!":
                cur = cur[:-1]
                if not cur:
                    raise SyntaxErrorDetail("Expected expression before '!' in 'VISIBLE'.", line_num)

            while cur:
                expr, cur = parseExpression(cur)
            continue

        # GIMMEH <var>
        if first.lexeme == "GIMMEH":
            if len(line_toks) < 2:
                raise SyntaxErrorDetail("Expected variable identifier after 'GIMMEH'.", line_num)
            if len(line_toks) > 2:
                raise SyntaxErrorDetail(f"Unexpected token '{line_toks[2].lexeme}' after 'GIMMEH <var>'.", line_num)
            if first.classification != "Variable Identifier" and not isValidIdentifier(line_toks[1].lexeme):
                raise SyntaxErrorDetail(f"Invalid variable identifier '{line_toks[1].lexeme}'.", line_num)
            continue

        # Conditionals: O RLY?
        if first.lexeme == "O RLY?":
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'O RLY?'.", line_num)
            block_stack.append(('O RLY?', line_num, {'stage': 'start'}))
            continue

        if first.lexeme == "YA RLY":
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'YA RLY'.", line_num)
            if not block_stack or block_stack[-1][0] != 'O RLY?':
                raise SyntaxErrorDetail("'YA RLY' found without matching 'O RLY?'.", line_num)
            if block_stack[-1][2]['stage'] != 'start':
                raise SyntaxErrorDetail("Unexpected 'YA RLY' in conditional block.", line_num)
            block_stack[-1][2]['stage'] = 'ya_rly'
            continue

        if first.lexeme == "MEBBE":
            if not block_stack or block_stack[-1][0] != 'O RLY?':
                raise SyntaxErrorDetail("'MEBBE' found without matching 'O RLY?'.", line_num)
            if block_stack[-1][2]['stage'] not in ('ya_rly', 'mebbe'):
                raise SyntaxErrorDetail("'MEBBE' cannot appear before 'YA RLY' or after 'NO WAI'.", line_num)
            if len(line_toks) < 2:
                raise SyntaxErrorDetail("Expected expression after 'MEBBE'.", line_num)
            expr, rest = parseExpression(line_toks[1:])
            if rest:
                raise SyntaxErrorDetail(f"Unexpected token '{rest[0].lexeme}' after 'MEBBE' expression.", line_num)
            block_stack[-1][2]['stage'] = 'mebbe'
            continue

        if first.lexeme == "NO WAI":
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'NO WAI'.", line_num)
            if not block_stack or block_stack[-1][0] != 'O RLY?':
                raise SyntaxErrorDetail("'NO WAI' found without matching 'O RLY?'.", line_num)
            if block_stack[-1][2]['stage'] not in ('ya_rly', 'mebbe'):
                raise SyntaxErrorDetail("'NO WAI' cannot appear before 'YA RLY' or after another 'NO WAI'.", line_num)
            block_stack[-1][2]['stage'] = 'no_wai'
            continue

        # Switch WTF?
        if first.lexeme == "WTF?":
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'WTF?'.", line_num)
            block_stack.append(('WTF?', line_num, {'stage': 'start'}))
            continue

        if first.lexeme == "OMG":
            if not block_stack or block_stack[-1][0] != 'WTF?':
                raise SyntaxErrorDetail("'OMG' found without matching 'WTF?' switch block.", line_num)
            if block_stack[-1][2]['stage'] == 'omgwtf':
                raise SyntaxErrorDetail("'OMG' cannot appear after 'OMGWTF'.", line_num)
            if len(line_toks) < 2:
                raise SyntaxErrorDetail("Expected value after 'OMG'.", line_num)
            expr, rest = parseExpression(line_toks[1:])
            if rest:
                raise SyntaxErrorDetail(f"Unexpected token '{rest[0].lexeme}' after 'OMG' value.", line_num)
            block_stack[-1][2]['stage'] = 'omg'
            continue

        if first.lexeme == "OMGWTF":
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'OMGWTF'.", line_num)
            if not block_stack or block_stack[-1][0] != 'WTF?':
                raise SyntaxErrorDetail("'OMGWTF' found without matching 'WTF?' switch block.", line_num)
            if block_stack[-1][2]['stage'] == 'omgwtf':
                raise SyntaxErrorDetail("Duplicate 'OMGWTF' default case.", line_num)
            block_stack[-1][2]['stage'] = 'omgwtf'
            continue

        # OIC closes O RLY? or WTF?
        if first.lexeme == "OIC":
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'OIC'.", line_num)
            if not block_stack or block_stack[-1][0] not in ('O RLY?', 'WTF?'):
                raise SyntaxErrorDetail("'OIC' found without matching 'O RLY?' or 'WTF?'.", line_num)
            block_stack.pop()
            continue

        # Loops: IM IN YR <label>
        if first.lexeme == "IM IN YR":
            if len(line_toks) < 2:
                raise SyntaxErrorDetail("Expected loop label after 'IM IN YR'.", line_num)
            label = line_toks[1].lexeme
            cur = line_toks[2:]
            # Optional operation: UPPIN / NERFIN YR <var>
            if cur and cur[0].lexeme in ("UPPIN", "NERFIN"):
                if len(cur) < 3 or cur[1].lexeme != "YR":
                    raise SyntaxErrorDetail(f"Expected 'YR <var>' after '{cur[0].lexeme}'.", line_num)
                cur = cur[3:]
            # Optional condition: TIL / WILE <expr>
            if cur and cur[0].lexeme in ("TIL", "WILE"):
                cond_type = cur[0].lexeme
                cur = cur[1:]
                if not cur:
                    raise SyntaxErrorDetail(f"Expected expression after '{cond_type}'.", line_num)
                expr, cur = parseExpression(cur)
            if cur:
                raise SyntaxErrorDetail(f"Unexpected tokens in loop header: '{cur[0].lexeme}'.", line_num)
            block_stack.append(('LOOP', line_num, {'label': label}))
            continue

        if first.lexeme == "IM OUTTA YR":
            if len(line_toks) < 2:
                raise SyntaxErrorDetail("Expected loop label after 'IM OUTTA YR'.", line_num)
            if len(line_toks) > 2:
                raise SyntaxErrorDetail(f"Unexpected tokens after 'IM OUTTA YR {line_toks[1].lexeme}'.", line_num)
            if not block_stack or block_stack[-1][0] != 'LOOP':
                raise SyntaxErrorDetail("'IM OUTTA YR' found without matching 'IM IN YR'.", line_num)
            expected_label = block_stack[-1][2]['label']
            if line_toks[1].lexeme != expected_label:
                raise SyntaxErrorDetail(f"Loop label mismatch: 'IM IN YR {expected_label}' closed by 'IM OUTTA YR {line_toks[1].lexeme}'.", line_num)
            block_stack.pop()
            continue

        # Functions: HOW IZ I <name>
        if first.lexeme == "HOW IZ I":
            if len(line_toks) < 2:
                raise SyntaxErrorDetail("Expected function identifier after 'HOW IZ I'.", line_num)
            func_name = line_toks[1].lexeme
            cur = line_toks[2:]
            while cur:
                if cur[0].lexeme == "YR":
                    cur = cur[1:]
                elif cur[0].lexeme == "AN" and len(cur) > 1 and cur[1].lexeme == "YR":
                    cur = cur[2:]
                else:
                    raise SyntaxErrorDetail(f"Unexpected token '{cur[0].lexeme}' in function parameter list.", line_num)
                if not cur or not isValidIdentifier(cur[0].lexeme):
                    raise SyntaxErrorDetail("Expected parameter identifier.", line_num)
                cur = cur[1:]
            block_stack.append(('FUNC', line_num, {'name': func_name}))
            continue

        if first.lexeme == "IF U SAY SO":
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'IF U SAY SO'.", line_num)
            if not block_stack or block_stack[-1][0] != 'FUNC':
                raise SyntaxErrorDetail("'IF U SAY SO' found without matching 'HOW IZ I'.", line_num)
            block_stack.pop()
            continue

        if first.lexeme == "FOUND YR":
            if len(line_toks) < 2:
                raise SyntaxErrorDetail("Expected expression after 'FOUND YR'.", line_num)
            expr, rest = parseExpression(line_toks[1:])
            if rest:
                raise SyntaxErrorDetail(f"Unexpected token '{rest[0].lexeme}' after 'FOUND YR' expression.", line_num)
            continue

        if first.lexeme == "GTFO":
            if len(line_toks) > 1:
                raise SyntaxErrorDetail("Unexpected tokens after 'GTFO'.", line_num)
            continue

        # Otherwise, check if it is a standalone expression (evaluates to IT)
        try:
            expr, rest = parseExpression(line_toks)
            if rest:
                raise SyntaxErrorDetail(f"Unexpected token '{rest[0].lexeme}' at line {line_num}.", line_num)
            continue
        except SyntaxErrorDetail:
            raise SyntaxErrorDetail(f"Invalid statement starting with '{first.lexeme}'.", line_num)

    if in_wazzup:
        raise SyntaxErrorDetail(f"Unclosed variable declaration block 'WAZZUP' starting at line {wazzup_line} (missing 'BUHBYE').", wazzup_line)

    if block_stack:
        block_type, start_line, data = block_stack[-1]
        if block_type == 'O RLY?':
            raise SyntaxErrorDetail(f"Unclosed conditional block 'O RLY?' starting at line {start_line} (missing 'OIC').", start_line)
        elif block_type == 'WTF?':
            raise SyntaxErrorDetail(f"Unclosed switch block 'WTF?' starting at line {start_line} (missing 'OIC').", start_line)
        elif block_type == 'LOOP':
            loop_label = data['label']
            raise SyntaxErrorDetail(f"Unclosed loop 'IM IN YR {loop_label}' starting at line {start_line}.", start_line)
        elif block_type == 'FUNC':
            func_name = data['name']
            raise SyntaxErrorDetail(f"Unclosed function declaration 'HOW IZ I {func_name}' starting at line {start_line}.", start_line)

    return True

def runLexer():
    textEditor.tag_remove("error_highlight", "1.0", tk.END)
    code = textEditor.get("1.0", "end-1c")
    tokenTable.delete(*tokenTable.get_children())
    tokens, lex_errors = tokenize(code)

    # Insert tokens into the table
    for lexeme, classification in tokens:
        tokenTable.insert("", tk.END, values=(lexeme, classification))

    # If lexical errors exist, report them
    if lex_errors:
        err_msg, err_line = lex_errors[0]
        statusBar.config(text=f"Status: {err_msg}", fg="red")
        if err_line is not None:
            textEditor.tag_add("error_highlight", f"{err_line}.0", f"{err_line}.end")
            textEditor.see(f"{err_line}.0")
        messagebox.showerror("Syntax Error", err_msg)
        return

    # Check syntax
    try:
        checkSyntax(tokens)
        statusBar.config(text="Status: Syntax is valid! No syntax errors detected.", fg="green")
    except SyntaxErrorDetail as e:
        statusBar.config(text=f"Status: {e}", fg="red")
        if e.line is not None:
            textEditor.tag_add("error_highlight", f"{e.line}.0", f"{e.line}.end")
            textEditor.see(f"{e.line}.0")
        messagebox.showerror("Syntax Error", str(e))

root = tk.Tk()
root.title("LOLCODE Interpreter")
root.geometry("900x650")

# File selector
fileFrame = tk.Frame(root)
fileFrame.pack(fill="x", padx=5, pady=5)
fileSelector = ttk.Combobox(fileFrame, state="readonly")
fileSelector.pack(side="left", fill="x", expand=True)
fileSelector.set("(None)")

openButton = tk.Button(fileFrame, text="Open", command=openFile)
openButton.pack(side="right", padx=5)

# Text editor
editorFont = tkfont.Font(family="Consolas", size=12)
tabWidth = editorFont.measure("    ")
textEditor = tk.Text(root, font=editorFont, wrap="none", tabs=(tabWidth,))
textEditor.tag_config("error_highlight", background="#ffcccc")
textEditor.pack(fill="both", expand=True, padx=5, pady=5)

# Run button
runButton = tk.Button(root, text="Run", command=runLexer)
runButton.pack(pady=5)

# List of Tokens
tokenFrame = tk.LabelFrame(root, text="LEXEMES")
tokenFrame.pack(fill="both", expand=True, padx=5, pady=5)
tokenTable = ttk.Treeview(tokenFrame, columns=("Lexeme", "Classification"), show="headings")
tokenTable.heading("Lexeme", text="Lexeme")
tokenTable.heading("Classification", text="Classification")
tokenTable.column("Lexeme", width=200)
tokenTable.column("Classification", width=250)
tokenScrollbar = ttk.Scrollbar(tokenFrame, orient="vertical", command=tokenTable.yview)
tokenTable.configure(yscrollcommand=tokenScrollbar.set)
tokenScrollbar.pack(side="right", fill="y")
tokenTable.pack(fill="both", expand=True)

# Status bar
statusBar = tk.Label(root, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor="w", padx=5)
statusBar.pack(side="bottom", fill="x")

if __name__ == "__main__":
    root.mainloop()