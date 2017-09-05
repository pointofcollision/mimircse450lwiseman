import ply.lex as lex
from sys import stdin

tokens = ('NEWLINE', 'CHARACTER')


def t_NEWLINE(t):
    r'\n'
    return t


def t_CHARACTER(t):
    r'.'
    return t


def t_error(t):
    pass


data = '''3 + 4 * 10
129 + 32
'''


# Build the lexer
lexer = lex.lex()

# Give the lexer some input
input_str = stdin.read()
lexer.input(input_str)

# Tokenize
while True:
    tok = lexer.token()
    if not tok:
        break  # No more input
    if tok.type == 'NEWLINE':
        print(tok.type)
    else:
        print(tok.value, tok.type)
