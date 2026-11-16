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
