from .constants import (
    keywords, types, keywordPattern, numberPattern, identifierPattern,
    wordPattern, multilineEndPattern, stringPattern
)
from .tokens import Token


def formatCode(code):
    return code.expandtabs(4)


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
    """Returns (tokens, lexErrors) where lexErrors is a list of (message, line)."""
    tokens = []
    multilineComment = False
    multilineStartLine = None
    lexErrors = []

    for lineNum, line in enumerate(code.splitlines(), start=1):
        position = 0
        previous = ""
        while position < len(line):
            # For a multiline comment
            if multilineComment:
                # Searches for TLDR and checks the characters before and after it
                end = multilineEndPattern.search(line[position:])
                if end:
                    endPosition = position + end.start()
                    # Checks if there is a comment before TLDR
                    if endPosition > position:
                        tokens.append(Token(line[position:endPosition], "Comment Text", lineNum))
                    tokens.append(Token("TLDR", "Multiline Comment End", lineNum))
                    position = position + end.end()
                    multilineComment = False
                else:
                    if line[position:]:
                        tokens.append(Token(line[position:], "Comment Text", lineNum))
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
                tokens.append(Token(word, keywords[word], lineNum))
                position = match.end()
                previous = word

                # If the keyword is BTW, means it is a comment
                if word == "BTW":
                    if position < len(line):
                        tokens.append(Token(line[position:], "Comment Text", lineNum))
                    break

                # Sets the multiline comment flag to true
                if word == "OBTW":
                    multilineComment = True
                    multilineStartLine = lineNum
                continue

            # If it is a ", detects that it is a YARN literal
            if line[position] == '"':
                match = stringPattern.match(line, position)
                if match:
                    word = match.group()
                    tokens.append(Token('"', "String Delimiter", lineNum))
                    tokens.append(Token(word[1:-1], "YARN Literal", lineNum))
                    tokens.append(Token('"', "String Delimiter", lineNum))
                    position += len(word)
                else:
                    lexErrors.append((f"Lexical Error at line {lineNum}: Unclosed string literal.", lineNum))
                    tokens.append(Token('"', "Unrecognized Lexeme", lineNum))
                    position += 1
                previous = ""
                continue

            # Matches a number
            match = numberPattern.match(line, position)
            if match:
                word = match.group()
                # If it is a float NUMBAR, else NUMBR
                if "." in word:
                    tokens.append(Token(word, "NUMBAR Literal", lineNum))
                else:
                    tokens.append(Token(word, "NUMBR Literal", lineNum))
                position = match.end()
                previous = ""
                continue

            # Matches an identifier
            match = wordPattern.match(line, position)
            if match:
                word = match.group()
                classification = classifyIdentifier(word, previous)
                tokens.append(Token(word, classification, lineNum))
                position = match.end()
                if classification == "Unrecognized Lexeme":
                    lexErrors.append((f"Lexical Error at line {lineNum}: Unrecognized lexeme '{word}'.", lineNum))
                    previous = ""
                else:
                    previous = word
                continue

            # If unrecognized
            ch = line[position]
            lexErrors.append((f"Lexical Error at line {lineNum}: Unrecognized lexeme '{ch}'.", lineNum))
            tokens.append(Token(ch, "Unrecognized Lexeme", lineNum))
            position += 1
            previous = ""

    if multilineComment:
        lexErrors.append((f"Syntax Error: Unclosed multiline comment 'OBTW' starting at line {multilineStartLine} (missing 'TLDR').", multilineStartLine))

    return tokens, lexErrors
