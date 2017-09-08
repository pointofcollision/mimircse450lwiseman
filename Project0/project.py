#PROJECT 0
#! /usr/bin/env python3
import ply.lex as lex
from sys import stdin
import fileinput

#keywords reserved for the system, not usable as ID's
keywords = {
  'val' : 'TYPE', 
  'char' : 'TYPE',  
  'string' : 'TYPE', 
  'print' : 'COMMAND_PRINT', 
  'random' : 'COMMAND_RANDOM'
}
linecount = 0
tokens = ['STRING_LITERAL', 'WHITESPACE', 'ID', 'VAL_LITERAL', 'CHAR_LITERAL', 'ASCII_CHAR', 'ASSIGN_ADD', 'ASSIGN_SUB', 'ASSIGN_MULT', 'ASSIGN_DIV', 'COMP_EQU', 'COMP_NEQU', 'COMP_LESS', 'COMP_LTE', 'COMP_GTR', 'COMP_GTE', 'BOOL_AND', 'BOOL_OR', 'COMMENT', 'UNKNOWN'] + list(set(keywords.values()))
#method for the STRING_LITERAL token. A literal string: A double quote followed by a series of internal characters and ending in a second double quote. The internal characters can be anything except a double quote or a newline. Note: in a future project we will implement escape characters. Example: "This is my string"
def t_STRING_LITERAL(t):
    r'\"[^"\n]*\"'
    return t

#method for COMMENT token, anything on one line (no multi line comments for now following a pound sign '#', from the pound sign to the end of the line
def t_COMMENT(t):
    r'\#.*([\n]|$)'
    return t

#method for the ID token,A sequence beginning with a letter or underscore ('_'), followed by a sequence of zero or more characters that may contain letters, numbers and underscores. can be used for variables or function names in future
def t_ID(t):
    r'[_a-zA-Z]+[_a-zA-Z0-9]*'
    t.type = keywords.get(t.value,'ID')
    return t
#method for the VAL_LITERAL token. Any literal number. These consist of sequences of digits, with no other characters except a single, optional, decimal point; If a decimal point exists, it must be followed by at least one digit
def t_VAL_LITERAL(t):
    r'([0-9]+)(\.[0-9]+)?|(\.[0-9]+)'
    return t
   
#method for the CHAR_LITERAL token. Any literal character. These are a single quote followed by any single character, followed by another single quote. Example: 'c' 
def t_CHAR_LITERAL(t):
    r'\'.\''
    return t
#methods for Compound math operators: += -= *= /=
def t_ASSIGN_ADD(t):
    r'\+\='
    return t
def t_ASSIGN_SUB(t):
    r'\-\='
    return t
def t_ASSIGN_MULT(t):
    r'\*\='
    return t
def t_ASSIGN_DIV(t):
    r'\/\='
    return t
#methods for Comparison operators: == != < <= > >=
def t_COMP_EQU(t):
    r'\=\='
    return t
def t_COMP_NEQU(t):
    r'\!\='
    return t
def t_COMP_LTE(t):
    r'\<\='
    return t
def t_COMP_LESS(t):
    r'\<'
    return t
def t_COMP_GTE(t):
    r'\>\='
    return t
def t_COMP_GTR(t):
    r'\>'
    return t
#method for the ASCII_CHAR token. Single-character operators: + - * / ( ) = , { } [ ] . ;
def t_ASCII_CHAR(t):
    r'\+|\-|\*|\/|\(|\)|\=|\,|\{|\}|\[|\]|\.|\;'
    return t

#methods for the tokens BOOL_OR, BOOL_AND Boolean operators: && ||
def t_BOOL_OR(t):
    r'\|\|'
    return t
def t_BOOL_AND(t):
    r'\&\&'
    return t

#method for the WHITESPACE token, newlines, tabs or white space 
def t_WHITESPACE(t): 
    r'[ \t\n]'
    return t

#method for unknown remainders, random symbols, whatever
def t_UNKNOWN(t):
    r'.+'
    return t
  
def t_error(t):
    pass


data = '''#this = a comment123%,.()
variable_name print var char random
 1.34 .000452 15 4.20
 'a' 
  "this is my string" ""
  + - * / ( ) = , { } [ ] . ; 
  += -= *=  4/=2
  == != < <= > >=
  "&& ||" && || 
      "val x = random(1.44) + print('r') * @;"'''


# Build the lexer
#if __name__ == "__main__": no idea what this line does
lexer = lex.lex()

# Give the lexer some input
#re-enable once we want that
input_str = ""
for line in fileinput.input():
    if line[0]!="#":
        linecount+=1
    input_str+=line
lexer.input(input_str)


# Tokenize
while True:
    tok = lexer.token()
    if not tok:
        break  # No more input
    if tok.type == 'WHITESPACE':
        continue
    if tok.type == 'UNKNOWN':
        print(tok.type + ": " + tok.value)
        break
    if tok.type =='COMMENT':
        continue
    else:
        print(tok.type + ": " + tok.value)
print("Line Count: " + str(linecount))