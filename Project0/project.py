#PROJECT 0
#! /usr/bin/env python3
import ply.lex as lex
from sys import stdin

words = {
  'cat' : 'NOUN', 
  'ferret' : 'NOUN',  
  'dog' : 'NOUN', 
  'human' : 'NOUN', 
  'MSU' : 'NOUN', 
  'Daenerys' : 'NOUN', 
  'Ghost' : 'NOUN', 
  'Josh' : 'NOUN', 
  'you' : 'NOUN',
  'is' : 'VERB',
  'chases' : 'VERB',
  'loves' : 'VERB'
}

tokens = ['UNKNOWN', 'PUNCTUATION', 'WHITESPACE'] + list(set(words.values()))

def t_PUNCTUATION(t):
  r'!'
  return t

def t_UNKNOWN(t):
  r'[^( \t\n!)]+'
  t.type = words.get(t.value,'UNKNOWN')
  return t
    
def t_WHITESPACE(t): 
  r'[ \t\n]'
  return t

def t_error(t):
  pass


data = '''is loves !!! chases Ghost! ferretjosh piexD%%% house Mouse MOuse2
'''


# Build the lexer
#if __name__ == "__main__": no idea what this line does
lexer = lex.lex()

# Give the lexer some input
input_str = stdin.read()
lexer.input(input_str)

# Tokenize
while True:
    tok = lexer.token()
    if not tok:
        break  # No more input
    if tok.type == 'WHITESPACE':
        print(tok.type + " (" + tok.value + ")")
    else:
        print(tok.type + " (" + tok.value + ")")

