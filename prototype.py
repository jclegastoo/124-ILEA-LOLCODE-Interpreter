import tkinter as tk
from tkinter import ttk, filedialog, font as tkfont
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


def formatCode(code):
    return code.expandtabs(4)


def openFile():
    filePath = filedialog.askopenfilename(title="Open LOLCODE File", filetypes=[("LOLCODE Files", "*.lol")])

    if filePath:
        with open(filePath, "r", encoding="utf-8") as file:
            code = file.read()

        code = formatCode(code)

        textEditor.delete("1.0", tk.END)
        textEditor.insert("1.0", code)

        fileSelector.set(os.path.basename(filePath))


def classifyIdentifier(word, previous):
    if word in types:
        return "Type Literal"

    if word == "WIN" or word == "FAIL":
        return "TROOF Literal"

    if previous == "HOW IZ I" or previous == "I IZ":
        return "Function Identifier"

    if previous == "IM IN YR" or previous == "IM OUTTA YR":
        return "Loop Identifier"

    if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', word):
        return "Variable Identifier"
        
    return "Unknown / Invalid Token"


def tokenize(code):
    tokens = []
    multilineComment = False
    previous = ""

    for line in code.splitlines():
        position = 0

        while position < len(line):

            # For a multiline comment
            if multilineComment:

                # Searches for TLDR and checks the characters before and after it
                end = re.search(r"(?<![A-Za-z0-9_])TLDR(?![A-Za-z0-9_])", line[position:])

                if end:
                    endPosition = position + end.start()

                    # Checks if there is a comment before TLDR
                    if endPosition > position:
                        tokens.append((line[position:endPosition], "Comment Text"))

                    tokens.append(("TLDR", "Multiline Comment End"))
                    position = position + end.end()
                    multilineComment = False
                else:
                    if line[position:]:
                        tokens.append((line[position:], "Comment Text"))

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
                tokens.append((word, keywords[word]))
                position = match.end()
                previous = word

                # If the keyword is BTW, means it is a comment
                if word == "BTW":
                    if position < len(line):
                        tokens.append((line[position:], "Comment Text"))

                    break

                # Sets the multiline comment flag to true
                if word == "OBTW":
                    multilineComment = True

                continue

            # If it is a ", detects that it is a YARN literal
            if line[position] == '"':
                match = re.match(r'"[^"]*"', line[position:])

                if match:
                    word = match.group()
                    tokens.append(('"', "String Delimiter"))
                    tokens.append((word[1:-1], "YARN Literal"))
                    tokens.append(('"', "String Delimiter"))
                    position += len(word)
                else:
                    tokens.append(('"', "Unrecognized Lexeme"))
                    position += 1

                previous = ""
                continue

            # Matches a number
            match = numberPattern.match(line, position)

            if match:
                word = match.group()

                # If it is a float NUMBAR, else NUMBR
                if "." in word:
                    tokens.append((word, "NUMBAR Literal"))
                else:
                    tokens.append((word, "NUMBR Literal"))

                position = match.end()
                previous = ""
                continue

            # Matches an identifier
            match = identifierPattern.match(line, position)

            if match:
                # Goes to the classifyIdentifier function and returns the corresponding classification
                word = match.group()
                classification = classifyIdentifier(word, previous)

                tokens.append((word, classification))
                position = match.end()
                previous = word
                continue

            # If unrecognized
            tokens.append((line[position], "Unrecognized Lexeme"))
            position += 1

    return tokens


def runLexer():
    code = textEditor.get("1.0", "end-1c")

    tokenTable.delete(*tokenTable.get_children())

    tokens = tokenize(code)

    for lexeme, classification in tokens:
        tokenTable.insert("", tk.END, values=(lexeme, classification))


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

root.mainloop()