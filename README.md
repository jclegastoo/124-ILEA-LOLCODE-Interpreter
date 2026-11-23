# LOLCODE Interpreter

A LOLCODE Interpreter made in Python. Features a simple graphical user interface (GUI) which allows users to write and run LOLCODE programs. The program identifies and interprets LOLCODE tokens and executes the code if no errors were found.

## Requirements
-Python 3
-Tkinter (Usually included with most python installations)

## How to run
1. Install Python 3 onto your system / make sure it's installed
2. Download and extract the ZIP file
3. Open the extracted main project folder in your terminal
4. Run the following command:
'python main.py'

## How to use
1. Run the interpreter using the steps above
2. Type your LOLCODE directly into the window on the left side
    -You may also click the Open button to load an existing file
3. Click the Run button
4. If the code is valid, the program will execute your code and display the output in the console
5. The Lexemes and Symbol Table sections will display your code's tokens and variables

## Features
1. Tokenization
    - Identifies keywords, strings, numbers, identifiers, and other tokens
2. File Loading
    - Lets users open pre existing .lol and .txt files
3. Syntax Checking
    - Checks if the written LOLCODE has valid syntax
4. Code Execution
    - Executes valid LOLCODE in the terminal
5. Lexeme Display and Symbol Table
    - Shows tokens and their classifications, alongside declared variables and their values
6. Error Handling
    - Displays syntax and evaluation errors found in your code, and highlights them for the user
7. Input and Output
    - Supports input and output from the user