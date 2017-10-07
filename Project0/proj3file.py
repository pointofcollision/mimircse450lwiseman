#! /usr/bin/env python3
import sys
import ply.lex as lex
import ply.yacc as yacc
#from bad_interpreter import run_bad_code_from_string


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
    ('right', '='),
    ('right', 'ASSIGN_SUB', 'ASSIGN_ADD','ASSIGN_DIV', 'ASSIGN_MULT'),
    ('left','BOOL_OR'),
    ('left','BOOL_AND'),
    ('nonassoc', 'COMP_EQU', 'COMP_GTR', 'COMP_GTE', 'COMP_NEQU', 
    'COMP_LESS', 'COMP_LTE'),
 ('left', '-', '+'),
  ('left', '*', '/'),
  ('left', '(', ')'),
  
  #('right', '-'),
)
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
def t_WHITESPACE(t): 
    r'[ \t\n]'
    pass

#method for unknown remainders, random symbols, whatever
#def t_UNKNOWN(t):
#    r'.'
#    return t
  
def t_error(t):
    raise SyntaxError(t)


GLOBAL_VARIABLES = {}

generated_global_variables = {}

bad_code_generated = [];
#START OF NODES

S_COUNT = 0
OR_COUNT = 0
AND_COUNT = 0
#method to return an entry for a new memory value ('s#')
def get_entry():
    global S_COUNT
    entry = "s{}".format(S_COUNT)
    S_COUNT += 1
    return entry

def get_or_label():
    global OR_COUNT
    entry = "stop_or{}".format(OR_COUNT)
    OR_COUNT += 1
    return entry

def get_and_label():
    global AND_COUNT
    entry = "stop_and{}".format(AND_COUNT)
    AND_COUNT += 1
    return entry
#BaseNode class from which all other classes inherit
class BaseNode:
    def __init__(self, children):
        self.children = children
        self.name = "BaseNode"

    def __str__(self):
        return "{}({})".format(self.name, self.children)

    __repr__ = __str__

    def generate_bad_code(self, bad_code):
        raise NotImplemented("BaseNode sucks.")

#class for a literal value node. contains one child (the value)
class ValLiteralNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "ValLiteralNode"
        #print( str(self.children[0]))

    def generate_bad_code(self, bad_code):
        entry = get_entry()
        #print("{} = {}".format(entry, self.children[0]))
        generated_global_variables[entry] = [self]
        bad_code_generated.append("val_copy {} {}".format(generated_global_variables[entry][-1].children[0],entry))
        return entry

#class to do the boolean AND operation ( '&&' )
#has 2 children, only executes the second to resolve condition if
#the first was not already false
class BooleanAndNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BooleanAndNode"

    def generate_bad_code(self, bad_code):
        entry = get_entry()
        child_0_entry = self.children[0].generate_bad_code(bad_code)
        #bad_code_generated.append("jump_if_0 {} {}".format(child_0_entry, Andlabel))
        #bad_code_generated.append(Andlabel + ":")
        
        #only look at second entry if the first one is not false
        result = generated_global_variables[child_0_entry][-1].children[-1];
        if (generated_global_variables[child_0_entry][-1].children[-1] == 1):
            print("first one true")
            child_1_entry = self.children[1].generate_bad_code(bad_code)
            if (generated_global_variables[child_1_entry][-1].children[-1] == 1):
                print("second one true")
                bad_code_generated.append("val_copy {} {}".format(child_1_entry,entry))
                result = generated_global_variables[child_1_entry][-1].children[-1];
            else:
                print("second one false")
                bad_code_generated.append("val_copy {} {}".format(child_1_entry,entry))
                result = generated_global_variables[child_1_entry][-1].children[-1];
            
        else:
            bad_code_generated.append("val_copy {} {}".format(child_0_entry,entry))
        #1 for true, 0 for false    
        generated_global_variables[entry] = [ValLiteralNode([result])]
        print("stored value: " + str(generated_global_variables[entry]))
        return entry
#Node to do the boolean OR operation ( '||')
#this operation exits once it finds a true value
class BooleanOrNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BooleanOrNode"

    def generate_bad_code(self, bad_code):
        entry = get_entry()
        child_0_entry = self.children[0].generate_bad_code(bad_code)
        #bad_code_generated.append("jump_if_n0 {} {}".format(child_0_entry, Orlabel))
        #bad_code_generated.append(Orlabel + ":")
        #only look at second entry if the first one is not false
        result = generated_global_variables[child_0_entry][-1].children[-1];
        if (generated_global_variables[child_0_entry][-1].children[-1] == 1):
            print("first Result was true")
            bad_code_generated.append("val_copy {} {}".format(child_0_entry,entry))
            
            print("val_copy {} {}".format(child_0_entry,entry ))
        else:
            child_1_entry = self.children[1].generate_bad_code(bad_code)
            if(generated_global_variables[child_1_entry][-1].children[-1] == 1):
                print("second result was true")
                bad_code_generated.append("val_copy {} {}".format(child_1_entry,entry))
                result = generated_global_variables[child_1_entry][-1].children[-1];
            else:
                print("neither true")
                bad_code_generated.append("val_copy {} {}".format(child_0_entry,entry))
        
        generated_global_variables[entry] = [ValLiteralNode([result])]   
        return entry

#Node to do binary comparisons and return 1 or 0 as result
class BinaryComparisonNode(BaseNode):
    def __init__(self, children, operator):
        BaseNode.__init__(self,children)
        self.name = "BinaryComparisonNode{}".format(operator)
        self.operator = operator

    def generate_bad_code(self, bad_code):
        entry = get_entry()
        bad_code.append("Comparing {}".format(self))
        child_0_entry = self.children[0].generate_bad_code(bad_code)
        child_1_entry = self.children[1].generate_bad_code(bad_code)
        if (self.operator == "=="):
            bad_code_generated.append("test_equ {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing ==")
            print(str(generated_global_variables[child_0_entry][-1]))
            print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] == generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
            #equal to
        elif (self.operator == ">="):
            #greater than or equal to
            bad_code_generated.append("test_gte {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing >=")
            print(str(generated_global_variables[child_0_entry][-1]))
            print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] >= generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
        elif (self.operator == "<="):
            #less than or equal to 
            bad_code_generated.append("test_lte {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing <=")
            print(str(generated_global_variables[child_0_entry][-1]))
            print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] <= generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
        elif (self.operator == "<"):
            #less than
            bad_code_generated.append("test_less {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing <")
            print(str(generated_global_variables[child_0_entry][-1]))
            print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] < generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
        elif (self.operator == ">"):
            #greater than 
            bad_code_generated.append("test_gtr {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing >")
            print(str(generated_global_variables[child_0_entry][-1]))
            print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] > generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
        elif (self.operator == "!="):
            #not equal to
            bad_code_generated.append("test_nequ {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("comparing !=")
            print(str(generated_global_variables[child_0_entry][-1]))
            print(str(generated_global_variables[child_1_entry][-1]))
            # 1 for true, 0 for false
            result = int(generated_global_variables[child_0_entry][-1].children[-1] != generated_global_variables[child_1_entry][-1].children[-1])
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
        
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

    def generate_bad_code(self, bad_code):
        #print("add/sub/mult/div nodes");
        #bad_code.append("# Adding {}".format(self))
        child_0_entry = self.children[0].generate_bad_code(bad_code)
        #if not (isinstance(ValLiteralNode,child_0_entry):
        #    child_0_entry = 
        child_1_entry = self.children[1].generate_bad_code(bad_code)
        entry = get_entry()
        print("{} = {} {} {}".format(
                entry, child_0_entry, self.operator, child_1_entry))
        if (self.operator == '*'):
            #mult s0 s9 s10
            #multiplication
            bad_code_generated.append("mult {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("mult {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("# Done with multiplying {}".format(self))
            print(str(generated_global_variables[child_0_entry][-1]))
            print(str( generated_global_variables[child_1_entry][-1]))
            result = generated_global_variables[child_0_entry][-1].children[-1] * generated_global_variables[child_1_entry][-1].children[-1]
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
        elif (self.operator == '+'):
            bad_code_generated.append("add {} {} {}".format(child_0_entry, child_1_entry, entry))
            print("add {} {} {}".format(child_0_entry, child_1_entry, entry))
            print(str(generated_global_variables[child_0_entry][-1]))
            print(str( generated_global_variables[child_1_entry][-1]))
            #print("# Done with adding {}".format(self))
            result = generated_global_variables[child_0_entry][-1].children[-1] + generated_global_variables[child_1_entry][-1].children[-1]
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
            #addition 
        elif (self.operator == '-'):
            print(str(generated_global_variables[child_0_entry][-1]))
            print(str( generated_global_variables[child_1_entry][-1]))
            bad_code_generated.append("sub {} {} {}".format(child_0_entry, child_1_entry, entry))
            result = generated_global_variables[child_0_entry][-1].children[-1] - generated_global_variables[child_1_entry][-1].children[-1]
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
            print("sub {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("# Done with subtracting {}".format(self))
            #subtraction 
        elif (self.operator == '/'):
            bad_code_generated.append("div {} {} {}".format(child_0_entry, child_1_entry, entry))
            result = generated_global_variables[child_0_entry][-1].children[-1] / generated_global_variables[child_1_entry][-1].children[-1]
            print(result)
            generated_global_variables[entry] = [ValLiteralNode([result])]
            print("div {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("# Done with dividing {}".format(self))
            #division 
        
        
        print("# Done with adding {}".format(self))
        return entry


class StatementNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "StatementNode"
        #print("Printing values")

    def generate_bad_code(self, bad_code):
        #bad_code.append("# Printing {}".format(self))
        print("statement Node")
        child_entries = []
        for child in self.children:
            child_entry = child.generate_bad_code(bad_code)
            child_entries.append(child_entry)
        return 
class BlockNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BlockNode"

    def generate_bad_code(self, bad_code):
        for child in self.children:
            child.generate_bad_code(bad_code)
    
class DeclarationNode(BaseNode):
    def __init__(self,children,var_type,ID):
        BaseNode.__init__(self,children)
        self.type_name = var_type
        self.ID = ID
        self.name = "DeclarationNode"
    def generate_bad_code(self, bad_code):
        print("declaring variable")
        entry = get_entry()
        #there will only be one child ever given to this method
        new_value = 0
        for child in self.children:
            if (isinstance(child,ValLiteralNode)):
                new_value = child.generate_bad_code(bad_code)
                print(new_value)
                print("stored value for this: " + str(generated_global_variables[new_value]))
                bad_code_generated.append("val_copy {} {}".format(new_value,entry))
            else:
                #bad_code.append("{} = {}".format(entry, self.children[0]))
                print("new value {} = {}".format(entry, self.children[0]))
                new_value = self.children[0].generate_bad_code(bad_code)
                print(new_value)
                print("Value stored here: " + str(generated_global_variables[new_value]))
                bad_code_generated.append("val_copy {} {}".format(new_value,entry))
        #should it have x as the key or the s1?
        #value, type, id, entrytag
        new_table_entry = [self.ID,self.type_name,generated_global_variables[new_value][-1]]
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

    def generate_bad_code(self, bad_code):
        entry = ""
        for key in generated_global_variables:
            if (len(generated_global_variables[key])>2 and generated_global_variables[key][0] == self.ID):
                #print("found ID: ")
                entry = key
        #print("accessing id: " + entry)
        #print("{} = {}".format(entry, self.children[0]))
        return entry
        
#node class to allow assigning values to variables after declaration
#the generate method returns the id of the variable in the generated table,
#so essentially its new value.
#should have 2 children, an idaccessnode and an expression to set equal to
class IdAssignmentNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "IdAssignmentNode"
    def generate_bad_code(self, bad_code):
        entry = self.children[0].generate_bad_code(bad_code)
        #print("accessing id: " + entry)
        print("{} = {}".format(entry, self.children[1]))
        print("id assignment")
        new_assign_value = self.children[1].generate_bad_code(bad_code)
        if (len(generated_global_variables[new_assign_value]) < 2):
            #it is a temp register not a variable
            generated_global_variables[entry][2] = generated_global_variables[new_assign_value][0]
            print("value stored for this variable: " +str(generated_global_variables[entry][2]))
            #print("accessed a temp register to assign to")
        else:
            print("value stored for this variable: " +str(generated_global_variables[entry][2]))
            generated_global_variables[entry][2] = generated_global_variables[new_assign_value][2]
            #print("accessed a variable")
        bad_code_generated.append("val_copy {} {}".format(new_assign_value,entry));
        print("val_copy {} {}".format(new_assign_value,entry));
        #assign the new value to this in the table, output its memory location
        
        return entry

#node type for printing values. For each parameter given, it out_val's it 
#at the end it prints a new line, with out_char '\n'
class PrintNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "PrintNode"

    def generate_bad_code(self, bad_code):
        child_entries = []
        for child in self.children:
            for i in range (0,len(self.children[0])):
                child_entry = child[i].generate_bad_code(bad_code)
                #returns the entry id
                bad_code_generated.append("out_val {}".format(child_entry))
        
        bad_code_generated.append("out_char '\\n'")
        print("done printing!")

#node to random a value. Randoms a value between 0 -> input, we just include the range. 
#Note: I assume the result is 1 for math computation purposes (locally)
class RandomNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "RandomNode"
        #print( str(self.children[0]))

    def generate_bad_code(self, bad_code):
        entry = get_entry()
        #print("{} = {}".format(entry, self.children[0]))
        
        generated_global_variables[entry] = [ValLiteralNode([1])]
        child_0 = self.children[0].generate_bad_code(bad_code);
        sweep_range = generated_global_variables[child_0][-1]
        print("Randoming range: " + str(sweep_range))
        
        bad_code_generated.append("random {} {}".format(sweep_range.children[0],entry))
        return entry
#END OF NODES
def p_program(p):
    """
    program : statements
    """
    bad_code = []
    p[1].generate_bad_code(bad_code)
    #print("bad code: ")
    #for element in bad_code_generated:
    #    print(element)
    #print("I'm a program!")


def p_zero_statements(p):
    """
    statements :
    """
    print("Start of statements.")
    p[0] = BlockNode([])
    #print("Done.")


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
    """
    #todo: expression node, declaration node
    #print("My statement's result: {}".format(p[1]))
    pn = StatementNode([p[1]])
    p[0] = pn

#for now no strings or such
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
    expr : '-' expr %prec '*'
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
# boolean operators && and ||
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
        GLOBAL_VARIABLES[p[1]] = BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),p[3]],"-")
        p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),p[3]],"+")])

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
        # x = x - 1 (x-=1)
        #an assign node with a child IdAccessNode and a BinaryMathNode(-)
        value = p[3]
        GLOBAL_VARIABLES[p[1]] = BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),p[3]],"-")
        p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),p[3]],"-")])

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
        GLOBAL_VARIABLES[p[1]] = BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),p[3]],"-")
        p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),p[3]],"*")])

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
        GLOBAL_VARIABLES[p[1]] = BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),p[3]],"-")
        p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),BinaryMathNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),p[3]],"/")])
        
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
        print(str(element))
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
    if (p[2] in GLOBAL_VARIABLES):
        raise NameError("Variable already defined in this scope")
    #returns the value assigned
    param_size = len(p)
    if (param_size > 3):
        GLOBAL_VARIABLES[p[2]] = p[4]
        val = p[4]
        p[0] = DeclarationNode([p[4]],p[1],p[2])
    else:
        GLOBAL_VARIABLES[p[2]] = 0;
        p[0] = DeclarationNode([ValLiteralNode([0])],p[1],p[2])
        #p[0] = 0
        
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
        #children, ID
        #literalls only for now, later add the char stuff
        p[0] = IdAccessNode([value],p[1])

def p_assignment(p):
    """
    expr : ID '=' expr
    """
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("Trying to access nonexistant variable")
    #print("Assigning to variable {} the value {}.".format(p[1], p[3]))
    
    print("assigning to a variable in prod. rules")
    print(str(p[3]))
    p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]]],p[1]),p[3]])
    GLOBAL_VARIABLES[p[1]] = p[3]
    #p[0] = p[3]

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
print(1 < 2 && 3 < 4,
      1 > 2 && 3 < 4,
      1 < 2 && 3 > 4,
      1 > 2 && 3 > 4);
print(5 < 6 || 7 < 8,
      5 > 6 || 7 < 8,
      5 < 6 || 7 > 8,
      5 > 6 || 7 > 8);
"""

def generate_bad_code_from_string(input_):
    S_COUNT = 0
    generated_global_variables.clear()
    GLOBAL_VARIABLES.clear()
    global bad_code_generated
    bad_code_generated = []
    lexer = lex.lex()
    parser = yacc.yacc()
    program = parser.parse(input_, lexer=lexer)

    output = bad_code_generated
    bad_code_return = """"""
    print("bad code: ")
    for element in bad_code_generated:
        bad_code_return += (element + '\n')
        #print(element)
    #program.generate_bad_code(output)
    return bad_code_return


if __name__ == "__main__":
    #parse_string(input_)
    #source = sys.stdin.read()
    #result = generate_bad_code_from_string(input_)
   # print(result)
   # output = run_bad_code_from_string(result)
    print("Output from bad code compiler: ")
    #print(output)
    #print("hello")
