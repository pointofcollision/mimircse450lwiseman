#! /usr/bin/env python3
import sys
import ply.lex as lex
import ply.yacc as yacc
import re
#from bad_interpreter import run_bad_code_from_string

line_count = 1
number_of_lines = 0
scope = 0
#NOTE ABOUT THIS PROJECT: for future reference, this treats all variables as VALS past declaration, so it does not error check to see if you do addition with strings or chars. for future projects this will need to be changed.
#keywords reserved for the system, not usable as ID's
keywords = {
  'val' : 'TYPE', 
  'char' : 'TYPE',  
  'string' : 'TYPE',
  'array(char)' :'TYPE',
  'print' : 'COMMAND_PRINT', 
  'random' : 'COMMAND_RANDOM',
  'if' : 'IF',
  'else' : 'ELSE',
  'break' : 'BREAK',
  'while' : 'WHILE'
}
#first step: replace the tokens with some literals
tokens = ['STRING_LITERAL','WHITESPACE','NEWLINE', 'ID', 'VAL_LITERAL', 'CHAR_LITERAL', 'ASSIGN_ADD', 'ASSIGN_SUB', 'ASSIGN_MULT', 'ASSIGN_DIV', 'COMP_EQU', 'COMP_NEQU', 'COMP_LESS', 'COMP_LTE', 'COMP_GTR', 'COMP_GTE', 'BOOL_AND', 'BOOL_OR', 'BOOL_NOT','COMMENT'] + list(set(keywords.values()))

literals = ['-','+','*','(',')','=',';','/', ',','{','}'] #dont need [ ] yet

#eventually add precedence below
precedence = (
    ('right', '='),
    ('right', 'ASSIGN_SUB', 'ASSIGN_ADD','ASSIGN_DIV', 'ASSIGN_MULT'),
    ('left','BOOL_OR'),
    ('left','BOOL_AND'),
    ('nonassoc', 'COMP_EQU', 'COMP_GTR', 'COMP_GTE', 'COMP_NEQU', 
    'COMP_LESS', 'COMP_LTE'),
 ('left', '-', '+'),
  ('left', '*', '/'),
  ('left', '(', ')'),
  ('nonassoc', 'ELSE'),
  ('nonassoc','IF'),
  ('nonassoc','IF1'),
  ('nonassoc','IF2'),
  ('nonassoc','IF3'),
  ('nonassoc','IF4'),
  ('nonassoc','IF5'),
  ('nonassoc','IF6'),
  ('nonassoc', 'UMINUS'),
)
#method for the STRING_LITERAL token. A literal string: A double quote followed by a series of internal characters and ending in a second double quote. The internal characters can be anything except a double quote.
def t_STRING_LITERAL(t):
    r'\"[^"\n]*\"'
    return t
    #return t

#method for COMMENT token, anything on one line (no multi line comments for now following a pound sign '#', from the pound sign to the end of the line
def t_COMMENT(t):
    r'\#[^\n]*'
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
    #\'', '\\', 't', '\'', '=', 't', 'a', 'b', '\n', '\t'
    #r"\'([^\']|\n|\t|\'|\\)\'"
    r"'([^\\']|\\n|\\t|\\'|\\\\)'"
    #print(t.value)
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
def t_BOOL_NOT(t):
    r'\!'
    return t

#method for the WHITESPACE token, newlines, tabs or white space 
def t_WHITESPACE(t): 
    r'[ \t]'
    pass
def t_NEWLINE(t):
    r'\n'
    global line_count
    line_count +=1
    pass

#method for unknown remainders, random symbols, whatever
#def t_UNKNOWN(t):
#    r'.'
#    raise SyntaxError("ERROR("+str(line_count)+ "): unknown token '" + str(t) + #"'")

def t_error(t):
    raise SyntaxError("ERROR("+str(line_count)+ "): unknown token \'" + str(t.value[0]) + "\'")


GLOBAL_VARIABLES = {}

generated_global_variables = {}

bad_code_generated = [];
#START OF NODES

S_COUNT = 0
OR_COUNT = 0
AND_COUNT = 0
NOT_COUNT = 0
statement_count = 0
size_of_input = 0
BLOCK_COUNT = 0
BLOCK_ACTIVE = 0
IF_COUNT = 0
WHILE_COUNT = 0
#method to return an entry for a new memory value ('s#')
def get_entry():
    global S_COUNT
    entry = "s{}".format(S_COUNT)
    S_COUNT += 1
    return entry

#the if label will start after the criteria and end after the if block
def get_if_start():
    global IF_COUNT
    IF_COUNT += 1
    entry = "if_start{}".format(IF_COUNT)
    return entry

def get_if_stop():
    
    entry = "if_stop{}".format(IF_COUNT)
    return entry
    
def get_while_start():
    global WHILE_COUNT,WHILE_ACTIVE
    WHILE_COUNT += 1
    WHILE_ACTIVE +=1
    entry = "while_start{}".format(WHILE_COUNT)
    return entry

def retrieve_while_stop():
    global WHILE_ACTIVE
    entry = "while_stop{}".format(WHILE_ACTIVE)
    return entry

def get_while_stop():
    global WHILE_ACTIVE
    WHILE_ACTIVE -=1
    entry = "while_stop{}".format(WHILE_COUNT)
    return entry

def get_else_start():
    #bound to the last if statement, or error
    entry = "else_start{}".format(IF_COUNT)
    return entry

def get_block_start():
    global BLOCK_COUNT
    global BLOCK_ACTIVE
    entry = "block_start{}".format(BLOCK_COUNT)
    BLOCK_COUNT +=1
    BLOCK_ACTIVE = BLOCK_COUNT
    return entry

def predict_block_start():
    entry = "block_start{}".format(BLOCK_ACTIVE+1)
    return entry

def predict_block_end():
    entry = "block_end{}".format(BLOCK_ACTIVE)
    return entry 
    
def return_block_start():
    entry = "block_start{}".format(BLOCK_ACTIVE)
    return entry

def return_block_end():
    entry = "block_end{}".format(BLOCK_ACTIVE-1)
    return entry 
    
def get_block_end():
    global BLOCK_ACTIVE
    entry = "block_end{}".format(BLOCK_ACTIVE-1)
    BLOCK_ACTIVE -= 1
    return entry

def get_or_label():
    global OR_COUNT
    entry = "bool_or{}".format(OR_COUNT)
    OR_COUNT += 1
    return entry

def get_and_label():
    global AND_COUNT
    entry = "bool_and{}".format(AND_COUNT)
    AND_COUNT += 1
    return entry

def get_not_label():
    global NOT_COUNT
    entry = "bool_not{}".format(NOT_COUNT)
    NOT_COUNT += 1
    return entry
#BaseNode class from which all other classes inherit
class BaseNode:
    def __init__(self, children):
        self.children = children
        self.name = "BaseNode"

    def __str__(self):
        return "{}({})".format(self.name, self.children)

    __repr__ = __str__

    def generate_bad_code(self, scope):
        raise NotImplemented("BaseNode sucks.")

#class for a literal value node. contains one child (the value)
class ValLiteralNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "ValLiteralNode"
        self.type_="val"
        #print( str(self.children[0]))

    def generate_bad_code(self, scope):
        entry = get_entry()
        #print("{} = {}".format(entry, self.children[0]))
        generated_global_variables[entry] = [self.type_,self]
        print("Value for a val literal :" +str(generated_global_variables[entry]))
        bad_code_generated.append("val_copy {} {}".format(generated_global_variables[entry][-1].children[0],entry))
        return entry

class CharLiteralNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "CharLiteralNode"
        self.type_="char"
        #print( str(self.children[0]))
    def generate_bad_code(self, scope):
        entry = get_entry()
        #print("{} = {}".format(entry, self.children[0]))
        generated_global_variables[entry] = [self.type_,self]
        print("Value for a char literal :" +str(generated_global_variables[entry]))
        if (generated_global_variables[entry][-1].children[0] == "'\t'"):
            #print("Tab found")
            generated_global_variables[entry][-1].children[0] = "'\\t'"
        elif (generated_global_variables[entry][-1].children[0] == "'\n'"):
            #print("Newline found")
            generated_global_variables[entry][-1].children[0] = "'\\n'"
        elif (generated_global_variables[entry][-1].children[0] == "'\\'"):
            generated_global_variables[entry][-1].children[0] = "'\\\\'"
        elif (generated_global_variables[entry][-1].children[0] == "'\''"):
            generated_global_variables[entry][-1].children[0] = "'\\''"
        else:
            print("Normal character")
        bad_code_generated.append("val_copy {} {}".format(generated_global_variables[entry][-1].children[0],entry))
        return entry


#class to do the boolean AND operation ( '&&' )
#has 2 children, only executes the second to resolve condition if
#the first was not already false
class BooleanAndNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BooleanAndNode"

    def generate_bad_code(self, scope):
        entry = get_entry()
        Andlabel = get_and_label()
        child_0_entry = self.children[0].generate_bad_code(scope)
        bad_code_generated.append("val_copy {} {}".format("0",entry))
        bad_code_generated.append("jump_if_0 {} {}".format(child_0_entry, Andlabel))
        child_1_entry = self.children[1].generate_bad_code(scope)
        bad_code_generated.append("jump_if_0 {} {}".format(child_1_entry, Andlabel))
        bad_code_generated.append("val_copy {} {}".format("1",entry))
        bad_code_generated.append(Andlabel + ":")
        
        #only look at second entry if the first one is not false
        result = generated_global_variables[child_0_entry][-1].children[-1];
        #1 for true, 0 for false    
        generated_global_variables[entry] = ["val",ValLiteralNode([result])]
        print("stored value: " + str(generated_global_variables[entry]))
        return entry
#Node to do the boolean OR operation ( '||')
#this operation exits once it finds a true value
class BooleanOrNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BooleanOrNode"

    def generate_bad_code(self, scope):
        entry = get_entry()
        Orlabel = get_or_label()
        child_0_entry = self.children[0].generate_bad_code(scope)
        bad_code_generated.append("val_copy {} {}".format("1",entry))
        bad_code_generated.append("jump_if_n0 {} {}".format(child_0_entry, Orlabel))
        child_1_entry = self.children[1].generate_bad_code(scope)
        bad_code_generated.append("jump_if_n0 {} {}".format(child_1_entry, Orlabel))
        bad_code_generated.append("val_copy {} {}".format("0",entry))
        bad_code_generated.append(Orlabel + ":")
        #only look at second entry if the first one is not false
        result = generated_global_variables[child_0_entry][-1].children[-1];
        generated_global_variables[entry] = ["val",ValLiteralNode([result])]   
        return entry
#class for the boolean NOT operation. returns 1 if false, 0 if true
class BooleanNotNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BooleanNotNode"

    def generate_bad_code(self, scope):
        entry = get_entry()
        Notlabel = get_not_label()
        child_0_entry = self.children[0].generate_bad_code(scope)
        bad_code_generated.append("val_copy {} {}".format("1",entry))
        bad_code_generated.append("jump_if_0 {} {}".format(child_0_entry, Notlabel))
        bad_code_generated.append("val_copy {} {}".format("0",entry))
        bad_code_generated.append(Notlabel + ":")
        #only look at second entry if the first one is not false
        result = generated_global_variables[child_0_entry][-1].children[-1];
        generated_global_variables[entry] = ["val",ValLiteralNode([result])]   
        return entry

#Node to contain an 'if' conditional. must resolve to a value
class IfConditionNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "IfConditionNode"

    def generate_bad_code(self, scope):
        entry = get_entry()
        iflabel = get_if_start()
        endlabel = get_if_stop()
        else_start = get_else_start()
        #startblock = predict_block_start();
        #endblock = predict_block_end();
        print("Inside if node")
        child_0_entry = self.children[0].generate_bad_code(scope)
        result = generated_global_variables[child_0_entry][-1].children[-1];
        generated_global_variables[entry] = ["val",ValLiteralNode([result])]
        type_0 = ""
        if (len(generated_global_variables[child_0_entry]) >3):
            type_0 = generated_global_variables[child_0_entry][1]
        else:
            type_0 = generated_global_variables[child_0_entry][0]
        if(type_0 != "val"): 
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): operand must resolve to a 'val' for if condition (lhs='"+type_0+"')")
        bad_code_generated.append(iflabel + ":")
        bad_code_generated.append("val_copy {} {}".format(child_0_entry,entry))
        #if there is an else statement length is 3
        if(len(self.children) == 2):
            bad_code_generated.append("jump_if_0 {} {}".format(entry, endlabel))
        else:
            bad_code_generated.append("jump_if_0 {} {}".format(entry,get_else_start()))
        child_1_entry = self.children[1].generate_bad_code(scope)
        if(len(self.children) == 3):
            child_2_entry = self.children[2].generate_bad_code(scope,endlabel)
        bad_code_generated.append(endlabel + ":")
        
class ElseConditionNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "ElseConditionNode"

    def generate_bad_code(self, scope,iflabel):
        print("Inside else block")
        entry = get_entry()
        elselabel = get_else_start()
        bad_code_generated.append("jump " + iflabel)
        bad_code_generated.append(elselabel + ":")
        child_0_entry = self.children[0].generate_bad_code(scope)

class BreakNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BreakNode"
        #print("break initialized")

    def generate_bad_code(self, scope):
        #print("Inside break block")
        while_stop = retrieve_while_stop()
        #print(str(while_stop[-1]))
        num = int(while_stop[-1])
        #print(str(num))
        if(num == 0):
            print("inside error raise portion")
            raise ValueError("ERROR("+str(size_of_input-statement_count)+"): Break command not allowed outside of while loop")
        bad_code_generated.append("jump " + while_stop)

#Node to contain a 'while' conditional. must resolve to a value.  
class WhileConditionNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "WhileConditionNode"

    def generate_bad_code(self, scope):
        entry = get_entry()
        whilelabel = get_while_start()
        end_label = retrieve_while_stop()
        bad_code_generated.append(whilelabel + ":")
        child_0_entry = self.children[0].generate_bad_code(scope)
        type_0 = ""
        if (len(generated_global_variables[child_0_entry]) >3):
            type_0 = generated_global_variables[child_0_entry][1]
        else:
            type_0 = generated_global_variables[child_0_entry][0]
        if(type_0 != "val"):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): operand must resolve to a 'val' for while condition (lhs='"+type_0+"'")
        
        bad_code_generated.append("val_copy {} {}".format(child_0_entry,entry))
        bad_code_generated.append("jump_if_0 {} {}".format(entry ,end_label))
        child_1_entry = self.children[1].generate_bad_code(scope)
        bad_code_generated.append("jump {}".format(whilelabel))
        bad_code_generated.append(end_label + ":")
        get_while_stop()

#Node to do binary comparisons and return 1 or 0 as result
class BinaryComparisonNode(BaseNode):
    def __init__(self, children, operator):
        BaseNode.__init__(self,children)
        self.name = "BinaryComparisonNode{}".format(operator)
        self.operator = operator

    def generate_bad_code(self, scope):
        entry = get_entry()
        child_0_entry = self.children[0].generate_bad_code(scope)
        child_1_entry = self.children[1].generate_bad_code(scope)
        type_0 = ""
        type_1 = ""
        if (len(generated_global_variables[child_0_entry]) >3):
            type_0 = generated_global_variables[child_0_entry][1]
        else:
            type_0 = generated_global_variables[child_0_entry][0]
        if (len(generated_global_variables[child_1_entry]) >3):
            type_1 = generated_global_variables[child_1_entry][1]
        else:
            type_1 = generated_global_variables[child_1_entry][0]
        if(type_0 != type_1):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for relationship operator (lhs='"+type_0+"', rhs='"+type_1+"')")
        if (self.operator == "=="):
            bad_code_generated.append("test_equ {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing ==")
            #print(str(generated_global_variables[child_0_entry][-1]))
            #print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] == generated_global_variables[child_1_entry][-1].children[-1])
            #print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
            #equal to
        elif (self.operator == ">="):
            #greater than or equal to
            bad_code_generated.append("test_gte {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing >=")
            #print(str(generated_global_variables[child_0_entry][-1]))
            #print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] >= generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
        elif (self.operator == "<="):
            #less than or equal to 
            bad_code_generated.append("test_lte {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing <=")
            #print(str(generated_global_variables[child_0_entry][-1]))
            #print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] <= generated_global_variables[child_1_entry][-1].children[-1])
            #print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
        elif (self.operator == "<"):
            #less than
            bad_code_generated.append("test_less {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing <")
            #print(str(generated_global_variables[child_0_entry][-1]))
            #print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] < generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
        elif (self.operator == ">"):
            #greater than 
            bad_code_generated.append("test_gtr {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing >")
            #print(str(generated_global_variables[child_0_entry][-1]))
            #print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] > generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
        elif (self.operator == "!="):
            #not equal to
            bad_code_generated.append("test_nequ {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing !=")
            #print(str(generated_global_variables[child_0_entry][-1]))
            #print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] != generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
        
        return entry

#Class for binary addition/subtraction/multiplication or division
class BinaryMathNode(BaseNode):
    #covers addition, division, multiplication, subtraction
    def __init__(self, children, operator):
        BaseNode.__init__(self,children)
        self.name = "BinaryMathNode{}".format(operator)
        self.operator = operator
        #print(self.name)
        #print("add/sub/mult/div nodes");

    def generate_bad_code(self, scope):
        child_0_entry = self.children[0].generate_bad_code(scope)
        child_1_entry = self.children[1].generate_bad_code(scope)
        type_1 = ""
        type_0 = ""
        if (len(generated_global_variables[child_0_entry]) >3):
            type_0 = generated_global_variables[child_0_entry][1]
        else:
            type_0 = generated_global_variables[child_0_entry][0]
        if (len(generated_global_variables[child_1_entry]) >3):
            type_1 = generated_global_variables[child_1_entry][1]
        else:
            type_1 = generated_global_variables[child_1_entry][0]
        if(type_0 != "val" or type_1 != "val"):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types are not values for math operator (lhs='"+type_0+"', rhs='"+type_1+"')")
        entry = get_entry()
        print("{} = {} {} {}".format(
                entry, child_0_entry, self.operator, child_1_entry))
        if (self.operator == '*'):
            #mult s0 s9 s10
            #multiplication
            bad_code_generated.append("mult {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("mult {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("# Done with multiplying {}".format(self))
            #print(str(generated_global_variables[child_0_entry][-1]))
            #print(str( generated_global_variables[child_1_entry][-1]))
            result = generated_global_variables[child_0_entry][-1].children[-1] * generated_global_variables[child_1_entry][-1].children[-1]
            print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
        elif (self.operator == '+'):
            bad_code_generated.append("add {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("add {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print(str(generated_global_variables[child_0_entry][-1]))
            #print(str( generated_global_variables[child_1_entry][-1]))
            result = generated_global_variables[child_0_entry][-1].children[-1] + generated_global_variables[child_1_entry][-1].children[-1]
            #print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
            #addition 
        elif (self.operator == '-'):
            #print(str(generated_global_variables[child_0_entry][-1]))
            #print(str( generated_global_variables[child_1_entry][-1]))
            bad_code_generated.append("sub {} {} {}".format(child_0_entry, child_1_entry, entry))
            result = generated_global_variables[child_0_entry][-1].children[-1] - generated_global_variables[child_1_entry][-1].children[-1]
            #print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
            print("sub {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("# Done with subtracting {}".format(self))
            #subtraction 
        elif (self.operator == '/'):
            bad_code_generated.append("div {} {} {}".format(child_0_entry, child_1_entry, entry))
            result = generated_global_variables[child_0_entry][-1].children[-1] / generated_global_variables[child_1_entry][-1].children[-1]
            #print(result)
            generated_global_variables[entry] = ["val",ValLiteralNode([result])]
            print("div {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("# Done with dividing {}".format(self))
            #division 
        
        
        print("# Done with adding {}".format(self))
        return entry


class StatementNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "StatementNode"
        print("Statement node initialized")

    def generate_bad_code(self, scope):
        print("statement Node")
        child_entries = []
        print(str(len(self.children)))
        if(isinstance(self.children[0],str)):
            print("empty Statement, string contained")
        else:
            for child in self.children:
                child_entry = child.generate_bad_code(scope)
                child_entries.append(child_entry)
        return 

class BlockNode(BaseNode):
    def __init__(self, children,scope = 0):
        BaseNode.__init__(self,children)
        self.name = "BlockNode"
        self.scope = scope
        #Conditional will be essentially a child node, only executed once
        #then the actual bad code would loop if needed when it was executed

    def generate_bad_code(self, scope):
        self.scope = scope + 1;
        print("Inside block node, deciding to use conditionor not")
        print("Scope in block node: " + str(self.scope))
        print("called scope: " + str(scope))
        block_start = get_block_start();
        block_end = return_block_end()
        bad_code_generated.append(block_start+ ":")
        for child in self.children:
            child.generate_bad_code(self.scope)
        block_end_hold = get_block_end()
        bad_code_generated.append(block_end + ":")
        self.deactivate_scoped_variables(self.scope)
       
    #this method will also remove the registers from the map, as it just slow
    #s it down to have that many cluttering it up. or it WOULD, but we can 
    #ignore this for now and update it to that to make it faster
    def deactivate_scoped_variables(self,scope):
        #print("deactivating scope")
        keys_to_remove = []
        for key in generated_global_variables:
            if (len(generated_global_variables[key])>3 and generated_global_variables[key][2]==scope):
                #print("found an in-scope variable: " + str(generated_global_variables[key][0]))
                generated_global_variables[key][3] = False
            elif (len(generated_global_variables[key])<=3):
                #print("extraneous register found")
                keys_to_remove.append(key)
        for item in keys_to_remove:
            generated_global_variables.pop(item)
                

class DeclarationNode(BaseNode):
    def __init__(self,children,var_type,ID):
        BaseNode.__init__(self,children)
        self.type_name = var_type
        self.ID = ID
        self.name = "DeclarationNode"
    def generate_bad_code(self, scope):
        print("declaring variable")
        entry = get_entry()
        #there will only be one child ever given to this method
        new_value = 0
        for key in generated_global_variables:
            if (len(generated_global_variables[key])>3 and generated_global_variables[key][0] == self.ID and generated_global_variables[key][2]==scope and generated_global_variables[key][3]== True):
                print("Id already existed in declaration")
                raise NameError("ERROR("+ str(size_of_input-statement_count) +"): variable already declared in this scope '"+ str(self.ID) +"' ")
        
        for child in self.children:
            if (isinstance(child,ValLiteralNode) or isinstance(child,CharLiteralNode)):
                new_value = child.generate_bad_code(scope)
                type_1 = ""
                if (len(generated_global_variables[new_value]) ==3):
                    type_1 = generated_global_variables[new_value][1]
                else:
                    type_1 = generated_global_variables[new_value][0]
                if(self.type_name != type_1):
                    raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for declaring (lhs='"+self.type_name+"', rhs='"+type_1+"')")
                print(new_value)
                #print("stored value for this: " + str(generated_global_variables[new_value][-1]))
                bad_code_generated.append("val_copy {} {}".format(new_value,entry))
            else:
                print("new value {} = {}".format(entry, self.children[0]))
                new_value = self.children[0].generate_bad_code(scope)
                type_1 = ""
                if (len(generated_global_variables[new_value]) ==3):
                    type_1 = generated_global_variables[new_value][1]
                else:
                    type_1 = generated_global_variables[new_value][0]
                if(self.type_name != type_1):
                    raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for declaring (lhs='"+self.type_name+"', rhs='"+type_1+"')")
                print(new_value)
                print("Value stored here: " + str(generated_global_variables[new_value][-1]))
                bad_code_generated.append("val_copy {} {}".format(new_value,entry))
        #value, type, id, scope here, if var active (entrytag for key)
        #it ceases being active when its block stops
        new_table_entry = [self.ID,self.type_name,scope,True,generated_global_variables[new_value][-1]]
        #for now doing by entryname
        generated_global_variables[entry] = new_table_entry
        return entry 

#node for accessing an ID. a node with a single child, the ID's value    
#returns the entry in the table where its value is. this can be used
#for both updating and querying it
class IdAccessNode(BaseNode):
    def __init__(self, children,ID):
        BaseNode.__init__(self,children)
        self.ID = ID
        self.name = "IdAccessNode"

    def generate_bad_code(self, scope):
        best_scope = 0;
        entry = ""
        for key in generated_global_variables:
            
            if (len(generated_global_variables[key])>3 and generated_global_variables[key][0] == self.ID and generated_global_variables[key][2]<=scope):
                print("found ID: ")
                if (generated_global_variables[key][2]>=best_scope and generated_global_variables[key][3] == True):
                    best_scope = generated_global_variables[key][2]
                    entry = key
                
        #print("accessing id: " + entry)
        #print("{} = {}".format(entry, self.children[0]))
        if (entry == ""):
            raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(self.ID) +"' ")
        return entry
        
#node class to allow assigning values to variables after declaration
#the generate method returns the id of the variable in the generated table,
#so essentially its new value.
#should have 2 children, an idaccessnode and an expression to set equal to
class IdAssignmentNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "IdAssignmentNode"
    def generate_bad_code(self,scope):
        entry = self.children[0].generate_bad_code(scope)
        #print("accessing id: " + entry)
        #print("{} = {}".format(entry, self.children[1]))
        print("id assignment")
        new_assign_value = self.children[1].generate_bad_code(scope)
        
        if (len(generated_global_variables[new_assign_value]) < 3):
            #it is a temp register not a variable
            type_1 = generated_global_variables[new_assign_value][0]
            if(type_1 != generated_global_variables[entry][1]):
                raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for declaring (rhs='"+type_1+"')")
            print(str(generated_global_variables[new_assign_value][0]))
            generated_global_variables[entry][-1] = generated_global_variables[new_assign_value][1]
            print("value stored for this variable: " +str(generated_global_variables[entry][-1]))
            #print("accessed a temp register to assign to")
        else:
            type_1 = generated_global_variables[new_assign_value][1]
            if(type_1 != generated_global_variables[entry][1]):
                raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for declaring (rhs='"+type_1+"')")
            print("value stored for this variable: " +str(generated_global_variables[entry][-1]))
            generated_global_variables[entry][-1] = generated_global_variables[new_assign_value][-1]
            #print("accessed a variable")
        bad_code_generated.append("val_copy {} {}".format(new_assign_value,entry));
        #print("val_copy {} {}".format(new_assign_value,entry));
        #assign the new value to this in the table, output its memory location
        
        return entry

#node type for printing values. For each parameter given, it out_val's it 
#or out_char's it if it is a CHAR_LITERAL
#at the end it prints a new line, with out_char '\n'
class PrintNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "PrintNode"

    def generate_bad_code(self, scope):
        child_entries = []
        for child in self.children:
            for i in range (0,len(self.children[0])):
                child_entry = child[i].generate_bad_code(scope)
                #returns the entry id
                type_name = ""
                if (len(generated_global_variables[child_entry]) >3):
                    type_name = generated_global_variables[child_entry][1]
                else:
                    type_name = generated_global_variables[child_entry][0]
                
                print("stored memes for this addr: " + str(generated_global_variables[child_entry]))
                #print("type_name")
                if (type_name == "val"):
                    bad_code_generated.append("out_val {}".format(child_entry))
                if (type_name == "char"):
                    bad_code_generated.append("out_char {}".format(child_entry))
        bad_code_generated.append("out_char '\\n'")
        print("done printing!")

#node to random a value. Randoms a value between 0 -> input, we just include the range. 
#Note: I assume the result is 1 for math computation purposes (locally)
class RandomNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "RandomNode"
        #print( str(self.children[0]))

    def generate_bad_code(self,scope):
        entry = get_entry()
        #print("{} = {}".format(entry, self.children[0]))
        
        generated_global_variables[entry] = ["val",ValLiteralNode([1])]
        child_0 = self.children[0].generate_bad_code(scope);
        type_0 = ""
        if (len(generated_global_variables[child_0]) >3):
            type_0 = generated_global_variables[child_0][1]
        else:
            type_0 = generated_global_variables[child_0][0]
        if (type_0 != "val"):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): random arguments are not type 'val' (rhs='"+type_0+"')")
        sweep_range = generated_global_variables[child_0][-1]
        print("Randoming range: " + str(sweep_range))
        
        bad_code_generated.append("random {} {}".format(sweep_range.children[0],entry))
        return entry
#END OF NODES
def p_program(p):
    """
    program : statements
    """
    p[1].generate_bad_code(-1)
    #print("bad code: ")
    #for element in bad_code_generated:
    #    print(element)
    #print("I'm a program!")


def p_zero_statements(p):
    """
    statements :
    """
    #print("Start of statements. for this block")
    p[0] = BlockNode([])


def p_statements(p):
    """
    statements : statements statement
    """
    block_node = p[1]
    block_node.children.append(p[2])
    p[0] = block_node


def p_statement(p):
    """
    statement : expr ';'
              | declaration ';'
              | break_arg ';'
              | ';'
    """
    #todo: expression node, declaration node
    #print("My statement's result: {}".format(p[1]))
    global statement_count
    statement_count +=1
    if(len(p) >1):
        #p[1].generate_bad_code(0)
        pn = StatementNode([p[1]])
    else:
        print("empty statement")
        pn = StatementNode([ValLiteralNode([0])])
    #print("Statement count: " + str(statement_count))
    p[0] = pn

def p_break(p):
    """
    break_arg : BREAK
    """
    print("break found")
    p[0] = BreakNode([p[1]])

def p_expr_char(p):
    """
    expr : CHAR_LITERAL
    """
    p[0] = CharLiteralNode([p[1]])

def p_expr_number(p):
    """
    expr : VAL_LITERAL
    """
    val = 0
    if ('.' in p[1]):
        val = float(p[1])
    else:
        val = int(p[1])
    #print(str(val))
    p[0] = ValLiteralNode([val])
    #print("Found a number")


def p_expr_addition(p):
    """
    expr : expr '+' expr
    """
    p[0] = BinaryMathNode([p[1], p[3]], "+")
    #val = p[1] + p[3]
    #print("Adding {} and {}".format(p[1], p[3]))


def p_expr_subtraction(p):
    """
    expr : expr '-' expr
    """
    #p[0] = p[1] - p[3]
    p[0] = BinaryMathNode([p[1], p[3]], "-")
    #print("Subtracting {} and {}".format(p[1], p[3]))

#unary minus operator, higher precedence than subtraction
def p_expr_uminus(p):
    """
    expr : '-' expr %prec UMINUS
    """
    p[0] = BinaryMathNode([p[2],ValLiteralNode([-1])],"*")

def p_expr_division(p):
    """
    expr : expr '/' expr
    """
    #val = p[1] / p[3]
    p[0] = BinaryMathNode([p[1], p[3]], "/")
    #print("Dividing {} and {}".format(p[1], p[3]))

def p_expr_multiplication(p):
    """
    expr : expr '*' expr
    """
    #val = p[1] * p[3]
    p[0] = BinaryMathNode([p[1], p[3]], "*")
    #print("Multiplying {} and {}".format(p[1], p[3]))
    
def p_parenthesis_expr(p):
    """
    expr : '(' expr ')'
    """
    p[0] = p[2]
# boolean operators && and || and !
def p_expr_boolean_and(p):
    """
    expr : expr BOOL_AND expr
    """
    p[0] = BooleanAndNode([p[1],p[3]])
    #p[1] and p[3]
    
def p_expr_boolean_or(p):
    """
    expr : expr BOOL_OR expr
    """
    p[0] = BooleanOrNode([p[1],p[3]])
    #p[1] or p[3]
def p_expr_boolean_not(p):
    """
    expr : BOOL_NOT expr %prec UMINUS
    """
    p[0] = BooleanNotNode([p[2]])
#compound assignments
#+=, -=, *=, /= (compound assignments)
def p_expr_cmpd_add(p):
    """
    expr : ID ASSIGN_ADD expr
    """
    #first the adding 
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(p[1]) +"' ")
    else:
        #print("variable += value")
        value = p[3]
        GLOBAL_VARIABLES[p[1]][0] = BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]],"-")
        p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]],"+")])

def p_expr_cmpd_sub(p):
    """
    expr : ID ASSIGN_SUB expr
    """
    #first the adding 
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(p[1]) +"' ")
    else:
        #print("variable -= value")
        # x = x - 1 (x-=1)
        #an assign node with a child IdAccessNode and a BinaryMathNode(-)
        value = p[3]
        GLOBAL_VARIABLES[p[1]][0] = BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]],"-")
        p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]],"-")])

def p_expr_cmpd_mult(p):
    """
    expr : ID ASSIGN_MULT expr
    """
    #first the adding 
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(p[1]) +"' ")
    else:
        #print("variable *= value")
        value = p[3]
        GLOBAL_VARIABLES[p[1]][0] = BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]],"-")
        p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]],"*")])

def p_expr_cmpd_div(p):
    """
    expr : ID ASSIGN_DIV expr
    """
    #first the adding 
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(p[1]) +"' ")
    else:
        #print("variable \= value")
        value = p[3]
        GLOBAL_VARIABLES[p[1]][0] = BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]],"-")
        p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]],"/")])
        
#==, !=, <, <=, >, >= comparisons
def p_compare_eq(p):
    """
    expr : expr COMP_EQU expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],"==")
    #p[1] == p[3]
    
def p_compare_neq(p):
    """
    expr : expr COMP_NEQU expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],"!=")
    #p[1] != p[3]

def p_compare_gt(p):
    """
    expr : expr COMP_GTR expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],">")
    #p[1] > p[3]
    
def p_compare_gte(p):
    """
    expr : expr COMP_GTE expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],">=")
    #p[1] >= p[3]

def p_compare_lt(p):
    """
    expr : expr COMP_LESS expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],"<")
    #p[1] < p[3]

def p_compare_lte(p):
    """
    expr : expr COMP_LTE expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],"<=")
    #p[1] <= p[3]
    
#system functions  COMMAND_PRINT and COMMAND_RANDOM
#print would be the only thing callable in its statement,
#unlike random, which returns a value
def p_print(p):
    """
    statement : COMMAND_PRINT '(' function_args ')' ';'
    """
    array = []
    for element in p[3]:
        array.append(element)
    #    print(str(element))
    p[0] = PrintNode([array])

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
    #random Node
    p[0] = RandomNode([p[3]])   

#the variable declaration rule. Allows the variable to be initialized to
#either a literal value or a preexisting ID, checks to see the value you are trying to create is not in namespace already, and if you are setting it equal to an ID, that the ID exists in the namespace
def p_var_declaration(p):
    """
    declaration : TYPE ID '=' expr
                | TYPE ID
    """
    #print("scope at declare: " +str(scope))
    #if (p[2] in GLOBAL_VARIABLES):
    #    raise NameError("ERROR("+ str(size_of_input-statement_count) +"): redeclaration of variable '"+ str(p[2]) +"' ")
    #re implement above in parse tree
    #returns the value assigned
    param_size = len(p)
    if (param_size > 3):
        GLOBAL_VARIABLES[p[2]] = [p[4]]
        val = p[4]
        p[0] = DeclarationNode([p[4]],p[1],p[2])
    else:
        GLOBAL_VARIABLES[p[2]] = [0];
        if (p[1] == "val"):
            p[0] = DeclarationNode([ValLiteralNode([0])],p[1],p[2])
        else:
            p[0] = DeclarationNode([CharLiteralNode([''])],p[1],p[2])
        #p[0] = 0
        
def p_id_access(p):
    """
    expr : ID
    """
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(p[1]) +"' ")
    else:
        #print("Accessing variable")
        value = GLOBAL_VARIABLES[p[1]][0]
        #children, ID
        #literalls only for now, later add the char stuff
        p[0] = IdAccessNode([value],p[1])

def p_assignment(p):
    """
    expr : ID '=' expr
    """
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(p[1]) +"' ")
    #print("Assigning to variable {} the value {}.".format(p[1], p[3]))
    #print(str(p[3]))
    p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]])
    GLOBAL_VARIABLES[p[1]][0] = p[3]
    #p[0] = p[3]

#for generic scope blocks without conditionals
def p_scope_block_enter(p):
    """
    statements : statements '{' statements '}'
    """
    #print("Entering scope block")
    #print("Scope before new: " + str(p[1].scope))
    block_node = p[1]
    p[3].scope = p[1].scope +1;
    block_node.children.append(p[3])
    p[0] = block_node
    
def p_if_block_enter(p):
    """
    statements : statements if_conditional '{' statements '}' %prec IF2
    """
    print("Entering if block")
    #print("Scope before new: " + str(p[1].scope))
    block_node = p[1]
    p[4].scope = p[1].scope + 1
    
    #p[4].conditional = p[2]
    p[2].children.append(p[4])
    #block_node.children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node
    
def p_if_else_block_enter(p):
    """
    statements : statements if_conditional '{' statements '}' else_conditional '{' statements '}' %prec IF6
    """
    print("Entering if/else block")
    #print("Scope before new: " + str(p[1].scope))
    block_node = p[1]
    
    #p[4].conditional = p[2]
    p[6].children.append(p[8])
    p[2].children.append(p[4])
    p[2].children.append(p[6])
    #block_node.children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node
    
def p_if_else_block_enter2(p):
    """
    statements : statements if_conditional statement else_conditional statement %prec IF3
    """
    print("Entering if/else block")
    #print("Scope before new: " + str(p[1].scope))
    block_node = p[1]
    
    #p[4].conditional = p[2]
    p[4].children.append(p[5])
    p[2].children.append(p[3])
    p[2].children.append(p[4])
    #block_node.children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node
    
def p_if_else_block_enter3(p):
    """
    statements : statements if_conditional '{' statements '}' else_conditional statement %prec IF5
    """
    print("Entering if/else block")
    #print("Scope before new: " + str(p[1].scope))
    block_node = p[1]
    
    #p[4].conditional = p[2]
    p[6].children.append(p[7])
    p[2].children.append(p[4])
    p[2].children.append(p[6])
    #block_node.children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node
    
def p_if_else_block_enter4(p):
    """
    statements : statements if_conditional statement else_conditional '{' statements '}' %prec IF4
    """
    print("Entering if/else block")
    #print("Scope before new: " + str(p[1].scope))
    block_node = p[1]
    
    #p[4].conditional = p[2]
    p[4].children.append(p[6])
    p[2].children.append(p[3])
    p[2].children.append(p[4])
    #block_node.children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node


def p_if_block_enter_2(p):
    """
    statements : statements if_conditional statement %prec IF1
    """
    print("Entering if block")
    block_node = p[1]
    p[2].children.append(p[3])
    block_node.children.append(p[2])
    p[0] = block_node

def p_if_conditional(p):
    """
    if_conditional : IF '(' expr ')'
    """
    print("If conditional node")
    p[0] = IfConditionNode([p[3]])

def p_else_conditional(p):
    """
    else_conditional : ELSE
    """
    p[0] = ElseConditionNode([])
    

def p_while_block_enter(p):
    """
    statements : statements while_conditional '{' statements '}' %prec IF1
    """
    #print("Entering scope block")
    #print("Scope before new: " + str(p[1].scope))
    block_node = p[1]
    p[4].scope = p[1].scope + 1
    
    #p[4].conditional = p[2]
    p[2].children.append(p[4])
    #block_node.children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node

def p_while_block_enter2(p):
    """
    statements : statements while_conditional statement %prec IF2
    """
    #print("Entering scope block")
    #print("Scope before new: " + str(p[1].scope))
    block_node = p[1]
    
    #p[4].conditional = p[2]
    p[2].children.append(p[3])
    #block_node.children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node

def p_while_conditional(p):
    """
    while_conditional : WHILE '(' expr ')'
    """
    print("While conditional node")
    p[0] = WhileConditionNode([p[3]])

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
# If on a char
if ('a') print(1);
"""
def generate_bad_code_from_string(input_):
    generated_global_variables.clear()
    GLOBAL_VARIABLES.clear()
    global bad_code_generated
    global S_COUNT, WHILE_COUNT, WHILE_ACTIVE
    global OR_COUNT
    global AND_COUNT
    global NOT_COUNT
    global line_count
    global size_of_input
    global statement_count, scope, BLOCK_COUNT, IF_COUNT,BLOCK_ACTIVE
    S_COUNT = 0; OR_COUNT = 0; AND_COUNT = 0; NOT_COUNT = 0;statement_count = 0;
    size_of_input = 0; scope = 0; BLOCK_COUNT =0;BLOCK_ACTIVE =0; IF_COUNT =0;
    WHILE_COUNT = 0; WHILE_ACTIVE =0
    bad_code_generated = []
    size_of_input= len(re.split('\n',input_))
    print("size of input: " + str(size_of_input));
    
    lexer = lex.lex()
    parser = yacc.yacc()
    try:
        program = parser.parse(input_, lexer=lexer)
    except ValueError:
        raise SyntaxError("ERROR("+str(size_of_input-statement_count)+"): Break command not allowed outside of while loop")
    output = bad_code_generated
    bad_code_return = """"""
    #print("bad code: ")
    for element in bad_code_generated:
        bad_code_return += (element + '\n')
        #print(element)
    return bad_code_return

if __name__ == "__main__":
    #parse_string(input_)
    #source = sys.stdin.read()
    #result = generate_bad_code_from_string(input_)
    #print("Output from parse: ")
    #print(result)
    print("bad code compiler")
    #output = run_bad_code_from_string(result)
    #print(output)
    #if (output == "'\\t'=tab\n\ttabbed!\n"):
    #    print("Equal to expected")
    
