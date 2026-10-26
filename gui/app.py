import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont

from lolcode import tokenize, formatCode, checkSyntax, buildSymbolTable, SyntaxErrorDetail


class LolcodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LOLCODE Interpreter")
        self.root.geometry("1100x750")
        self.root.minsize(700, 500)

        # Bottom widgets are packed first so they keep their space when the window shrinks
        self.buildFileSelector()
        self.buildStatusBar()
        self.buildRunButton()

        # Editor on top, tables below; the divider can be dragged
        mainPane = ttk.PanedWindow(self.root, orient="vertical")
        mainPane.pack(fill="both", expand=True)
        self.buildEditor(mainPane)
        self.buildTables(mainPane)

    #layout

    def buildFileSelector(self):
        fileFrame = tk.Frame(self.root)
        fileFrame.pack(fill="x", padx=5, pady=5)
        self.fileSelector = ttk.Combobox(fileFrame, state="readonly")
        self.fileSelector.pack(side="left", fill="x", expand=True)
        self.fileSelector.set("(None)")

        openButton = tk.Button(fileFrame, text="Open", command=self.openFile)
        openButton.pack(side="right", padx=5)

    def buildEditor(self, pane):
        editorFrame = tk.Frame(pane)
        pane.add(editorFrame, weight=1)
        editorFont = tkfont.Font(family="Consolas", size=12)
        tabWidth = editorFont.measure("    ")
        # height is in lines; kept small so the pane, not the text box, decides the size
        self.textEditor = tk.Text(editorFrame, font=editorFont, wrap="none", tabs=(tabWidth,), height=10)
        self.textEditor.tag_config("error_highlight", background="#ffcccc")
        self.textEditor.pack(fill="both", expand=True, padx=5, pady=5)

    def buildRunButton(self):
        runButton = tk.Button(self.root, text="Run", command=self.run)
        runButton.pack(side="bottom", fill="x", padx=5, pady=5)

    # Lexemes and symbol table side by side; the divider can be dragged
    def buildTables(self, pane):
        tablesPane = ttk.PanedWindow(pane, orient="horizontal")
        pane.add(tablesPane, weight=1)
        self.buildTokenTable(tablesPane)
        self.buildSymbolTable(tablesPane)

    def buildTokenTable(self, pane):
        tokenFrame = tk.LabelFrame(pane, text="LEXEMES")
        pane.add(tokenFrame, weight=3)
        self.tokenTable = ttk.Treeview(tokenFrame, columns=("Lexeme", "Classification"), show="headings", height=12)
        self.tokenTable.heading("Lexeme", text="Lexeme")
        self.tokenTable.heading("Classification", text="Classification")
        self.tokenTable.column("Lexeme", width=200)
        self.tokenTable.column("Classification", width=250)
        tokenScrollbar = ttk.Scrollbar(tokenFrame, orient="vertical", command=self.tokenTable.yview)
        self.tokenTable.configure(yscrollcommand=tokenScrollbar.set)
        tokenScrollbar.pack(side="right", fill="y")
        self.tokenTable.pack(fill="both", expand=True)

    def buildSymbolTable(self, pane):
        symbolFrame = tk.LabelFrame(pane, text="SYMBOL TABLE")
        pane.add(symbolFrame, weight=2)
        self.symbolTable = ttk.Treeview(symbolFrame, columns=("Identifier", "Value"), show="headings", height=12)
        self.symbolTable.heading("Identifier", text="Identifier")
        self.symbolTable.heading("Value", text="Value")
        self.symbolTable.column("Identifier", width=150)
        self.symbolTable.column("Value", width=200)
        symbolScrollbar = ttk.Scrollbar(symbolFrame, orient="vertical", command=self.symbolTable.yview)
        self.symbolTable.configure(yscrollcommand=symbolScrollbar.set)
        symbolScrollbar.pack(side="right", fill="y")
        self.symbolTable.pack(fill="both", expand=True)

    def buildStatusBar(self):
        self.statusBar = tk.Label(self.root, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor="w", padx=5)
        self.statusBar.pack(side="bottom", fill="x")

    # ---------- Actions ----------

    def openFile(self):
        filePath = filedialog.askopenfilename(
            title="Open LOLCODE File",
            filetypes=[("LOLCODE Files", "*.lol"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filePath:
            with open(filePath, "r", encoding="utf-8") as file:
                code = file.read()
            code = formatCode(code)
            self.textEditor.delete("1.0", tk.END)
            self.textEditor.insert("1.0", code)
            self.textEditor.tag_remove("error_highlight", "1.0", tk.END)
            self.fileSelector.set(os.path.basename(filePath))
            self.statusBar.config(text=f"Loaded {os.path.basename(filePath)}", fg="black")

    def run(self):
        self.textEditor.tag_remove("error_highlight", "1.0", tk.END)
        code = self.textEditor.get("1.0", "end-1c")
        self.tokenTable.delete(*self.tokenTable.get_children())
        self.symbolTable.delete(*self.symbolTable.get_children())
        tokens, lexErrors = tokenize(code)

        # Insert tokens into the table
        for lexeme, classification in tokens:
            self.tokenTable.insert("", tk.END, values=(lexeme, classification))

        # If lexical errors exist, report the first one
        if lexErrors:
            errMsg, errLine = lexErrors[0]
            self.showError(errMsg, errLine)
            return

        # Check syntax
        try:
            checkSyntax(tokens)
            self.statusBar.config(text="Status: Syntax is valid! No syntax errors detected.", fg="green")
        except SyntaxErrorDetail as e:
            self.showError(str(e), e.line)
            return

        # Fill the symbol table only for syntactically valid programs
        for symbol in buildSymbolTable(tokens):
            self.symbolTable.insert("", tk.END, values=(symbol.name, symbol.displayValue()))

    def showError(self, message, line):
        self.statusBar.config(text=f"Status: {message}", fg="red")
        if line is not None:
            self.textEditor.tag_add("error_highlight", f"{line}.0", f"{line}.end")
            self.textEditor.see(f"{line}.0")
        messagebox.showerror("Syntax Error", message)
