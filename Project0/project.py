#project 0 version
import sys
import ply.lex as lex
import ply.yacc as yacc

#NOTE ABOUT THIS PROJECT: for future reference, this treats all variables as VALS past declaration, so it does not error check to see if you do addition with strings or chars. for future projects this will need to be changed.
#keywords reserved for the system, not usable as ID's
keywords = {
  'val' : 'TYPE', 
  'char' : 'TYPE',  
  'string' : 'TYPE', 
  'print' : 'COMMAND_PRINT', 
  'random' : 'COMMAND_RANDOM'
}
#first step: replace the tokens with some literals
tokens = ['STRING_LITERAL','WHITESPACE', 'ID', 'VAL_LITERAL', 'CHAR_LITERAL', 'ASSIGN_ADD', 'ASSIGN_SUB', 'ASSIGN_MULT', 'ASSIGN_DIV', 'COMP_EQU', 'COMP_NEQU', 'COMP_LESS', 'COMP_LTE', 'COMP_GTR', 'COMP_GTE', 'BOOL_AND', 'BOOL_OR', 'COMMENT'] + list(set(keywords.values()))

literals = ['-','+','*','(',')','=',';','/', ','] #dont need [ ] or { } yet

#eventually add precedence below
precedence = (
    ('nonassoc', 'ASSIGN_SUB', 'ASSIGN_ADD','ASSIGN_DIV', 'ASSIGN_MULT'),
    ('left','BOOL_AND','BOOL_OR'),
    ('nonassoc', 'COMP_EQU', 'COMP_GTR', 'COMP_GTE', 'COMP_NEQU', 
    'COMP_LESS', 'COMP_LTE'),
 ('left', '-', '+'),
  ('left', '*', '/'),
  ('left', '(', ')'),
  ('left', '='),
  #('right', '-'),
)
linecount = 0
#method for the STRING_LITERAL token. A literal string: A double quote followed by a series of internal characters and ending in a second double quote. The internal characters can be anything except a double quote or a newline. Note: in a future project we will implement escape characters. Example: "This is my string"
def t_STRING_LITERAL(t):
    r'\"[^"\n]*\"'
    return t

#method for COMMENT token, anything on one line (no multi line comments for now following a pound sign '#', from the pound sign to the end of the line
def t_COMMENT(t):
    r'\#.*([\n]|$)'
    pass

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

#methods for the tokens BOOL_OR, BOOL_AND Boolean operators: && ||
def t_BOOL_OR(t):
    r'\|\|'
    return t
def t_BOOL_AND(t):
    r'\&\&'
    return t

#method for the WHITESPACE token, newlines, tabs or white space 
#method for the WHITESPACE token, newlines, tabs or white space 
def t_WHITESPACE(t): 
    r'[ \t\n]'
    pass

#method for unknown remainders, random symbols, whatever
#def t_UNKNOWN(t):
#    r'.'
#    return t
  
def t_error(t):
    pass


GLOBAL_VARIABLES = {}



def p_program(p):
    """
    program : statements
    """
    #print("I'm a program!")


def p_zero_statements(p):
    """
    statements :
    """
    #print("Done.")


def p_statements(p):
    """
    statements : statement statements
    """
    pass


def p_statement(p):
    """
    statement : expr ';'
              | declaration ';'
    """
    #print("My statement's result: {}".format(p[1]))
    p[0] = p[1]


#for now no strings or such
def p_expr_number(p):
    """
    expr : VAL_LITERAL
    """
    if ('.' in p[1]):
        p[0] = float(p[1])
    else:
        p[0] = int(p[1])
    #print("Found a number")


def p_expr_addition(p):
    """
    expr : expr '+' expr
    """
    p[0] = p[1] + p[3]
    #print("Adding {} and {}".format(p[1], p[3]))


def p_expr_subtraction(p):
    """
    expr : expr '-' expr
    """
    p[0] = p[1] - p[3]
    #print("Subtracting {} and {}".format(p[1], p[3]))

#unary minus operator, higher precedence than subtraction
def p_expr_uminus(p):
    """
    expr : '-' expr %prec '*'
    """
    p[0] = -p[2]

def p_expr_division(p):
    """
    expr : expr '/' expr
    """
    p[0] = p[1] / p[3]
    #print("Dividing {} and {}".format(p[1], p[3]))

def p_expr_multiplication(p):
    """
    expr : expr '*' expr
    """
    p[0] = p[1] * p[3]
    #print("Multiplying {} and {}".format(p[1], p[3]))
    
def p_parenthesis_expr(p):
    """
    expr : '(' expr ')'
    """
    p[0] = p[2]
# boolean operators && and ||
def p_expr_boolean_and(p):
    """
    expr : expr BOOL_AND expr
    """
    p[0] = p[1] and p[3]
    
def p_expr_boolean_or(p):
    """
    expr : expr BOOL_OR expr
    """
    p[0] = p[1] or p[3]

#compound assignments
#+=, -=, *=, /= (compound assignments)
def p_expr_cmpd_add(p):
    """
    expr : ID ASSIGN_ADD expr
    """
    #first the adding 
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("Variable not defined")
    else:
        #print("variable += value")
        value = p[3]
        GLOBAL_VARIABLES[p[1]] = GLOBAL_VARIABLES[p[1]] + value
        p[0] = GLOBAL_VARIABLES[p[1]]

def p_expr_cmpd_sub(p):
    """
    expr : ID ASSIGN_SUB expr
    """
    #first the adding 
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("Variable not defined")
    else:
        #print("variable -= value")
        value = p[3]
        GLOBAL_VARIABLES[p[1]] = GLOBAL_VARIABLES[p[1]] - value
        p[0] = GLOBAL_VARIABLES[p[1]]

def p_expr_cmpd_mult(p):
    """
    expr : ID ASSIGN_MULT expr
    """
    #first the adding 
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("Variable not defined")
    else:
        #print("variable *= value")
        value = p[3]
        GLOBAL_VARIABLES[p[1]] = GLOBAL_VARIABLES[p[1]] * value
        p[0] = GLOBAL_VARIABLES[p[1]]

def p_expr_cmpd_div(p):
    """
    expr : ID ASSIGN_DIV expr
    """
    #first the adding 
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("Variable not defined")
    else:
        #print("variable \= value")
        value = p[3]
        GLOBAL_VARIABLES[p[1]] = GLOBAL_VARIABLES[p[1]] / value
        p[0] = GLOBAL_VARIABLES[p[1]]

#==, !=, <, <=, >, >= comparisons
def p_compare_eq(p):
    """
    expr : expr COMP_EQU expr
    """
    p[0] = p[1] == p[3]
    
def p_compare_neq(p):
    """
    expr : expr COMP_NEQU expr
    """
    p[0] = p[1] != p[3]

def p_compare_gt(p):
    """
    expr : expr COMP_GTR expr
    """
    p[0] = p[1] > p[3]
    
def p_compare_gte(p):
    """
    expr : expr COMP_GTE expr
    """
    p[0] = p[1] >= p[3]

def p_compare_lt(p):
    """
    expr : expr COMP_LESS expr
    """
    p[0] = p[1] < p[3]

def p_compare_lte(p):
    """
    expr : expr COMP_LTE expr
    """
    p[0] = p[1] <= p[3]
    
#system functions  COMMAND_PRINT and COMMAND_RANDOM
#print would be the only thing callable in its statement,
#unlike random, which returns a value
def p_print(p):
    """
    statement : COMMAND_PRINT '(' function_args ')' ';'
    """
    array = ""
    #for element in p[3]:
    #    print(element)

def p_function_args(p):
    """
    function_args : function_args ',' expr
                  | expr
    """
    arguments_array = []
    length = len(p)
    if (length > 2 ):
        new_array = p[1]
        new_array.append(p[3])
        p[0] = p[1]
    else:
        array = []
        array.append(p[1])
        p[0] = array
# doesnt matter what this does now, in proj 3 will produce
# a random int 0<= x < expr
def p_random(p):
    """
    expr : COMMAND_RANDOM '(' expr ')'
    """
    #print("randomed")
    p[0] = p[3]    
#the variable declaration rule. Allows the variable to be initialized to
#either a literal value or a preexisting ID, checks to see the value you are trying to create is not in namespace already, and if you are setting it equal to an ID, that the ID exists in the namespace
def p_var_declaration(p):
    """
    declaration : TYPE ID '=' expr
                | TYPE ID
    """
    if (p[2] in GLOBAL_VARIABLES):
        raise NameError("Variable already defined in this scope")
    #returns the value assigned
    param_size = len(p)
    if (param_size > 3):
        GLOBAL_VARIABLES[p[2]] = p[4]
        p[0] = p[4]
    else:
        GLOBAL_VARIABLES[p[2]] = 0;
        p[0] = 0
 
def p_id_access(p):
    """
    expr : ID
    """
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("Variable not defined")
    else:
        #print("Accessing variable")
        value = GLOBAL_VARIABLES[p[1]]
        p[0] = GLOBAL_VARIABLES[p[1]]

def p_assignment(p):
    """
    expr : ID '=' expr
    """
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("Trying to access nonexistant variable")
    #print("Assigning to variable {} the value {}.".format(p[1], p[3]))
    GLOBAL_VARIABLES[p[1]] = p[3]
    p[0] = p[3]

def p_error(p):
    raise SyntaxError(p)


def parse_string(input_):
    GLOBAL_VARIABLES.clear()
    #yacc.yacc(errorlog=yacc.NullLogger())
    #there are a bunch of unused tokens right now, I realize this.
    lex.lex()
    parser = yacc.yacc(errorlog=yacc.NullLogger())
    parser.parse(input_)
    return True


input_ = """
val x;
val a = 5;
val b = (a *= 2);
val z = (a==b) && (a!=b);# && (1>0);
print( (a==b) && (a!=b) && (1>0));
#print((a == b) && (a != b) && (a < b) && (a <= b) && (a > b) && (a >= b));
#print((a == b) || (a != b) || (a < b) || (a <= b) || (a > b) || (a >= b));

"""


if __name__ == "__main__":
    parse_string(input_)
    parse_string(input_)