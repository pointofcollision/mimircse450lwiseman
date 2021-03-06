#! /usr/bin/env python3
import sys
import ply.lex as lex
import ply.yacc as yacc
import re
#from bad_and_ugly_interpreter import run_ugly_code_from_string
#from bad_and_ugly_interpreter import run_bad_code_from_string

line_count = 1
number_of_lines = 0
scope = 0
function_scope = 0
active_function_id = None

#keywords reserved for the system, not usable as ID's
keywords = {
  'array': 'SPEC_TYPE',
  'val' : 'TYPE', 
  'char' : 'TYPE',  
  'string' : 'TYPE',
  'print' : 'COMMAND_PRINT', 
  'random' : 'COMMAND_RANDOM',
  'if' : 'IF',
  'else' : 'ELSE',
  'break' : 'BREAK',
  'while' : 'WHILE',
  'define' : 'FUNCTION_DEFINE',
  'return' : 'FUNCTION_RETURN'
}
#first step: replace the tokens with some literals
tokens = ['STRING_LITERAL','WHITESPACE','NEWLINE', 'ID', 'VAL_LITERAL', 'CHAR_LITERAL', 'ASSIGN_ADD', 'ASSIGN_SUB', 'ASSIGN_MULT', 'ASSIGN_DIV', 'COMP_EQU', 'COMP_NEQU', 'COMP_LESS', 'COMP_LTE', 'COMP_GTR', 'COMP_GTE', 'BOOL_AND', 'BOOL_OR', 'BOOL_NOT','COMMENT','COMMAND_RESIZE','COMMAND_SIZE'] + list(set(keywords.values()))

literals = ['-','+','*','(',')','=',';','/', ',','{','}','[',']']
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
  ('nonassoc','FN1'),
  ('nonassoc','FN2'),
  ('nonassoc', 'UMINUS'),
)
#method for the STRING_LITERAL token. A literal string: A double quote followed by a series of internal characters and ending in a second double quote. The internal characters can be anything except a double quote.
def t_STRING_LITERAL(t):
    #r'\"[^"\n]*\"'
    r"\"(\\\"|[^\"])*\""
    return t

#method for COMMENT token, anything on one line (no multi line comments for now following a pound sign '#', from the pound sign to the end of the line
def t_COMMENT(t):
    r'\#[^\n]*'
    pass

def t_COMMAND_RESIZE(t):
    r'\.resize'
    return t

def t_COMMAND_SIZE(t):
    r'\.size'
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

def t_error(t):
    raise SyntaxError("ERROR("+str(line_count)+ "): unknown token \'" + str(t.value[0]) + "\'")


GLOBAL_VARIABLES = {}
generated_global_variables = {}
global_functions = {}
global_function_stack = []
function_registers = []

#your normal code in here, at the end we add labels to start/stop of function code, and add the function block at the end.
bad_code_generated_global = [];

#starts with jump function_section_stop
#(bunch of function data)
#function_section_stop:
#functions will call generate bad code on their children via this 
#array, instead of bad_code_generated. this will require a few changes
function_code_generated_global = [];
S_COUNT = 1
OR_COUNT = 0
AND_COUNT = 0
NOT_COUNT = 0
statement_count = 0
size_of_input = 0
BLOCK_COUNT = 0
BLOCK_ACTIVE = 0
IF_COUNT = 0
WHILE_COUNT = 0
RETURN_AFTER_CALL = 0

#method to return an entry for a new memory value ('s#')
def get_entry():
    global S_COUNT
    entry = "s{}".format(S_COUNT)
    S_COUNT += 1
    return entry

#method to return a 'bad' id for an array index
def get_array_entry():
    global S_COUNT
    entry = "a{}".format(S_COUNT)
    S_COUNT +=1
    return entry

def get_function_return():
    global RETURN_AFTER_CALL
    entry = "return_after_call{}".format(RETURN_AFTER_CALL)
    RETURN_AFTER_CALL += 1
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
    entry = "while_stop{}".format(WHILE_COUNT)
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
    
def get_label():
    global NOT_COUNT
    entry = NOT_COUNT
    NOT_COUNT +=1;
    return entry;

#list for an array(char) type
def convertString(string_to_convert):
    return_array = [];
    i = 0;
    myiter = iter(range(1,len(string_to_convert)-1))
    for z in myiter:
        if (string_to_convert[z] == "\\"):
            print("escape char found")
            if (string_to_convert[z+1] == "n"):
                #print("newline found")
                #store in a form recognizable by the char literal node
                val = "'\\n'"
                next(myiter,None)
                #print(val)
                return_array.append(CharLiteralNode([val]))
            elif (string_to_convert[z+1] == "\\"):
               # print("escaped slashes")
                val = "'\\\\'";
                next(myiter,None)
                #print(val)
                return_array.append(CharLiteralNode([val]))
            elif (string_to_convert[z+1] == "\""):
                #print("escaped double quotes")
                val = "'\"'"
                next(myiter,None)
                #print(val)
                return_array.append(CharLiteralNode([val]))
            elif(string_to_convert[z+1] == "t"):
                #print("tab")
                val = "'\\t'"
                next(myiter,None)
                #print(val)
                return_array.append(CharLiteralNode([val]))
            else:
                print("just an escaped slash")
                val = "'\\'"
                #print(val)
                return_array.append(CharLiteralNode([val]))
        elif(string_to_convert[z] == "'"):
            val = "'\\''"
            #print(val)
            return_array.append(CharLiteralNode([val]))
        else:
            #print("Normal character")
            val = "'" + string_to_convert[z] + "'"
            #print(val)
            return_array.append(CharLiteralNode([val]))
    return return_array
#BaseNode class from which all other classes inherit
class BaseNode:
    def __init__(self, children):
        self.children = children
        self.name = "BaseNode"

    def __str__(self):
        return "{}({})".format(self.name, self.children)

    __repr__ = __str__

    def generate_bad_code(self, scope, bad_code_generated):
        raise NotImplemented("BaseNode sucks.")

#class to contain the information necessary to call a function
#can be partially filled out when the parser sees the function, 
#the return type, name, and number of parameters, and their entry numbers
class FunctionEntry():
    def __init__(self, fn_name, return_type_, num_params,return_entry = None):
        self.name = "FunctionEntry"
        self.ID = fn_name
        self.return_type = return_type_
        #can't know what types its parameters are until the function node is
        #processed, i.e. if a call comes before a fn declare it wont know this
        self.param_types = None
        self.num_params = num_params
        self.parameter_slots = None
        self.return_entry = return_entry
        
#a table entry class, to make this symbol table a lot more understandable
#, readable, and EXPANDABLE.
class TableEntry():
    def __init__(self,type_, value,scope = 1, active = True, var_name= None, size = None,array_type = False,array_index=None,array_parent = None):
        self.name = "TableEntry"
        self.type_ = type_
        self.value = value
        self.ID = var_name
        self.size = size
        self.scope = scope
        self.active = active
        #secret elements for an array index
        self.fn_id = ""
        self.array_type = array_type
        self.array_index = array_index
        self.array_parent = array_parent
        
#class for a literal value node. contains one child (the value)
class ValLiteralNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "ValLiteralNode"
        self.type_="val"

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        generated_global_variables[entry] = TableEntry(self.type_,self)
        #print("Value for a val literal :" +str(generated_global_variables[entry].value))
        bad_code_generated.append("val_copy {} {}".format(generated_global_variables[entry].value.children[0],entry))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry

class CharLiteralNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "CharLiteralNode"
        self.type_="char"
    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        generated_global_variables[entry] = TableEntry(self.type_,self)
        #print("Value for a char literal :" +str(generated_global_variables[entry].value))
        if (generated_global_variables[entry].value.children[0] == "'\t'"):
            generated_global_variables[entry].value.children[0] = "'\\t'"
        elif (generated_global_variables[entry].value.children[0] == "'\n'"):
            generated_global_variables[entry].value.children[0] = "'\\n'"
        elif (generated_global_variables[entry].value.children[0] == "'\\'"):
            generated_global_variables[entry].value.children[0] = "'\\\\'"
        elif (generated_global_variables[entry].value.children[0] == "'\''"):
            generated_global_variables[entry].value.children[0] = "'\\''"
        #else:
            #print("Normal character")
        bad_code_generated.append("val_copy {} {}".format(generated_global_variables[entry].value.children[0],entry))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry

#class for an array of vals
class ArrayValNode(BaseNode):
    def __init__(self,children):
        BaseNode.__init__(self,children)
        self.name = "ArrayValNode"
        self.type_ = "array(val)"
    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_array_entry();
        generated_global_variables[entry] = TableEntry(
            self.type_, self.children[0],scope, True, None, ValLiteralNode([len(self.children[0])]), False)
        #(self,type_, value,scope = 1, active = True, var_name= None, size = None,array_type = False,array_index=None,array_parent = None):
        print(str(self.children[0]))
        #create array via set size
        array_size = generated_global_variables[entry].size.children[-1]
        #print("array size: " + str(array_size))
        bad_code_generated.append("ar_set_size {} {}".format(entry,array_size))
        for i in range(0,len(self.children[0])):
            new_entry = get_entry();
            child_entry = self.children[0][i].generate_bad_code(scope, bad_code_generated)
            #(self,type_, value,scope = 1, active = True, var_name= None, size = None,array_type = False,array_index=None,array_parent = None):
            bad_code_generated.append("ar_set_idx {} {} {}".format(entry,i, child_entry))
        #print("generating array_val bad code")
        if(function_scope ==1):
            function_registers.append(entry)
        return entry

#class for an array of chars (string)
class ArrayCharNode(BaseNode):
    def __init__(self,children):
        BaseNode.__init__(self,children)
        self.name = "ArrayCharNode"
        self.type_ = "array(char)"
    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_array_entry();
        #(self,type_, value,scope = 1, active = True, var_name= None, size = None,array_type = False,array_index=None,array_parent = None):
        generated_global_variables[entry] = TableEntry(
            self.type_, self.children[0],scope, True, None, ValLiteralNode([len(self.children[0])]), False) 
        
        print(str(self.children[0]))
        #create array via set size
        array_size = generated_global_variables[entry].size.children[-1]
        #print("array size: " + str(array_size))
        bad_code_generated.append("ar_set_size {} {}".format(entry,array_size))
        #now set each element in the array equal to its correct value
        for i in range(0,len(self.children[0])):
            #get new ID
            new_entry = get_entry();
            child_entry = self.children[0][i].generate_bad_code(scope, bad_code_generated)
            bad_code_generated.append("ar_set_idx {} {} {}".format(entry,i, child_entry))
        #print("generating array_char bad code")
        if(function_scope ==1):
            function_registers.append(entry)
        return entry

#class to do the boolean AND operation ( '&&' )
#has 2 children, only executes the second to resolve condition if
#the first was not already false
class BooleanAndNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BooleanAndNode"

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        Andlabel = get_and_label()
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        bad_code_generated.append("val_copy {} {}".format("0",entry))
        bad_code_generated.append("jump_if_0 {} {}".format(child_0_entry, Andlabel))
        child_1_entry = self.children[1].generate_bad_code(scope, bad_code_generated)
        bad_code_generated.append("jump_if_0 {} {}".format(child_1_entry, Andlabel))
        bad_code_generated.append("val_copy {} {}".format("1",entry))
        bad_code_generated.append(Andlabel + ":")
        
        #only look at second entry if the first one is not false
        result = generated_global_variables[child_0_entry].value.children[-1];
        #1 for true, 0 for false    
        generated_global_variables[entry] = TableEntry("val",ValLiteralNode([result]))
        print("stored value: " + str(generated_global_variables[entry].value))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry
#Node to do the boolean OR operation ( '||')
#this operation exits once it finds a true value
class BooleanOrNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BooleanOrNode"

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        Orlabel = get_or_label()
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        bad_code_generated.append("val_copy {} {}".format("1",entry))
        bad_code_generated.append("jump_if_n0 {} {}".format(child_0_entry, Orlabel))
        child_1_entry = self.children[1].generate_bad_code(scope, bad_code_generated)
        bad_code_generated.append("jump_if_n0 {} {}".format(child_1_entry, Orlabel))
        bad_code_generated.append("val_copy {} {}".format("0",entry))
        bad_code_generated.append(Orlabel + ":")
        result = generated_global_variables[child_0_entry].value.children[-1];
        generated_global_variables[entry] = TableEntry("val",ValLiteralNode([result]))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry
#class for the boolean NOT operation. returns 1 if false, 0 if true
class BooleanNotNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BooleanNotNode"

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        Notlabel = get_not_label()
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        bad_code_generated.append("val_copy {} {}".format("1",entry))
        bad_code_generated.append("jump_if_0 {} {}".format(child_0_entry, Notlabel))
        bad_code_generated.append("val_copy {} {}".format("0",entry))
        bad_code_generated.append(Notlabel + ":")
        #only look at second entry if the first one is not false
        result = generated_global_variables[child_0_entry].value.children[-1];
        generated_global_variables[entry] = TableEntry("val",ValLiteralNode([result]))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry

class FunctionCallNode(BaseNode):
    def __init__(self, children, function_id):
        BaseNode.__init__(self,children)
        self.name = "FunctionCallNode"
        self.fn_id = function_id
    
    def generate_bad_code(self, scope, bad_code_generated):
        #need to push current position onto the stack somehow
        
        #test to see if we should even test for recursion or not
        global function_scope
        function_prev = function_scope
        if(self.fn_id != active_function_id):
            print("non active function call")
            function_scope = 0;
                        
        
        function_return_label = get_function_return();
        
        function_base = global_functions[self.fn_id]
        children_count = 0;
        if (function_base.num_params == 0 and len(self.children) == 0):
            print("zero parameters expected, zero recieved")
        else:
            if (len(self.children[0]) != function_base.num_params):
                    raise ValueError("ERROR("+str(size_of_input-statement_count)+"incorrect number of parameters for function call (expected: "+ str(function_base.num_params)+ ", recieved: "+ str(len(self.children))+")")
            
            # ***** push function parameters onto stack ***** #
            active_children = []
            
            for child in self.children[0]:
                child_entry_temp = child.generate_bad_code(scope, bad_code_generated);
                print("executed return value: " + child_entry_temp)
                active_children.append(child_entry_temp)
                param_slot = function_base.parameter_slots[children_count]
                if (function_scope == 1):
                    function_registers.append(param_slot)
                children_count += 1
            #if(function_scope == 1):
                #print("recursive function call")
                #for i in range(0, len(function_registers)):
                #    print(function_registers[i])
                #print("end of recursive entries")   
            second_count = 0
            
            # *** push register values onto stack *** #
            if (function_scope == 1):
                for i in range(0,len(function_registers)):
                    if(function_registers[i][0] =="s"):
                        bad_code_generated.append("push {}".format(function_registers[i]))
                    else:
                        bad_code_generated.append("ar_push {}".format(function_registers[i]))
            # *** push register values onto stack concluded *** #      
            for child in self.children[0]:
                print("position in active children array: " + str(second_count))
                # ***** begin parameter initialization ****** #
                child_entry = active_children[second_count]
                #print("child in function call: " + child_entry)
                child_type = generated_global_variables[child_entry].type_
                if(function_base.param_types[second_count] != child_type):
                    raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for function call (expected='"+function_base.param_types[second_count]+"', recieved='"+child_type+"')")
               
                #copy values from the param to the value in the function call.
                #this is after the type validation, so type 1 == type 2
                param_slot = function_base.parameter_slots[second_count]
                
                if (child_type == "array(char)" or child_type == "array(val)"):
                    bad_code_generated.append("ar_copy {} {}".format(child_entry,param_slot))
                else:
                    bad_code_generated.append("val_copy {} {}".format(child_entry,param_slot))
            
                second_count = second_count + 1
            
                # ****** conclude parameter initialization ***** #
        
        bad_code_generated.append("push {}".format(function_return_label))
        bad_code_generated.append("jump {}".format(self.fn_id))
        bad_code_generated.append(function_return_label + ":")
        
        # *** pop out the new values from the stack *** #
        if (function_scope == 1):
                for item in reversed(function_registers):
                    if(item[0] =="s"):
                        bad_code_generated.append("pop {}".format(item))
                    else:
                        bad_code_generated.append("ar_pop {}".format(item))
        # ***** return the entry for the function return ***** #
        if(self.fn_id != active_function_id):
            print("non active function call")
            function_scope = function_prev;
        return function_base.return_entry

class FunctionNode(BaseNode):
    def __init__(self, children, type_, ID):
        BaseNode.__init__(self,children)
        self.name = "FunctionNode"
        self.type_ = type_
        self.ID = ID
        count = 0;
        global_functions[ID].parameter_slots = [];
        global_functions[ID].param_types = [];
        for child in children:
            #when the function is first seen initialize its parameter slots and 
            #parameter_types
            param_object = children[count]
            type_2 = param_object.type_name
            #initialize the function nodes parameter type and slot arrays
            param_entry = get_entry() if (type_2 != "array(char)" and type_2 != "array(val)") else get_array_entry()
            global_functions[ID].param_types.append(param_object.type_name)
            global_functions[ID].parameter_slots.append(param_entry)
            count += 1
        
        # ***** initialize return pointer in symbol table ***** #
        return_pointer = get_entry()if(self.type_ != "array(char)" and self.type_ != "array(val)") else get_array_entry()
        if (self.type_ == "array(char)" or self.type_ == "array(val)"):
            new_table_entry = TableEntry(self.type_, 0, scope, True, self.ID,0, True,None, None)
        else:
            new_table_entry = TableEntry(self.type_, 0, scope, True, self.ID,None, False,None, None)
        generated_global_variables[return_pointer] = new_table_entry
        
        # ***** conclude initialization of return pointer in symbol table **** #
        
        global_functions[ID].return_entry = return_pointer;
        
    def generate_bad_code(self, scope, bad_code_generated):
        global function_scope
        function_scope = 1
        global active_function_id
        active_function_id = self.ID
        #is a function node, find its entry in the function table.
        function_found = global_functions[self.ID]
        global function_code_generated_global
        function_code_generated_global.append(self.ID + ":")
        
        
        #need a stack of function calls to know which one is being returned.
        
        global global_function_stack
        global_function_stack.append(self.ID);
        #FunctionNode children : [ parameters..., block ]
        #get_entry for return value (for pop)
        count = 0;
        #global_functions[self.ID].parameter_slots = [];
        #global_functions[self.ID].param_types = [];
        for i in range(0, len(self.children) - 1):
            #counts as being in a new scope already
            #print("function arg")
            #print(str(self.children[i]))
            param_entry = self.children[i].generate_bad_code(scope + 1, function_code_generated_global, global_functions[self.ID].parameter_slots[i])
            #this is an entry that was generated:
            #instead of returning a new thing its copying the old one here
            #moved to init ----
            #global_functions[self.ID].parameter_slots.append(param_entry);
            #param_type = generated_global_variables[param_entry].type_

            #moved to init ----
            #global_functions[self.ID].param_types.append(param_type) 
        #execute function block 
        self.children[-1].generate_bad_code(scope+1, function_code_generated_global)
        function_scope = 0;
        function_registers.clear();
        global_function_stack.pop(0); #reset stack slot
        active_function_id = None;
        
#Node to contain an 'if' conditional. must resolve to a value
class IfConditionNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "IfConditionNode"

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        iflabel = get_if_start()
        endlabel = get_if_stop()
        else_start = get_else_start()
        #print("Inside if node")
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        if(function_scope ==1):
            function_registers.append(entry)
        result = generated_global_variables[child_0_entry].value.children[-1];
        generated_global_variables[entry] = TableEntry("val",ValLiteralNode([result]))
        type_0 = generated_global_variables[child_0_entry].type_
        if(type_0 != "val"): 
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): operand must resolve to a 'val' for if condition (lhs='"+type_0+"')")
        bad_code_generated.append(iflabel + ":")
        bad_code_generated.append("val_copy {} {}".format(child_0_entry,entry))
        if(len(self.children) == 2):
            bad_code_generated.append("jump_if_0 {} {}".format(entry, endlabel))
        else:
            bad_code_generated.append("jump_if_0 {} {}".format(entry,get_else_start()))
        child_1_entry = self.children[1].generate_bad_code(scope, bad_code_generated)
        if(len(self.children) == 3):
            child_2_entry = self.children[2].generate_bad_code(scope,endlabel, bad_code_generated)
        bad_code_generated.append(endlabel + ":")
        
class ElseConditionNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "ElseConditionNode"

    def generate_bad_code(self, scope,iflabel, bad_code_generated):
        #print("Inside else block")
        #entry = get_entry()
        elselabel = get_else_start()
        bad_code_generated.append("jump " + iflabel)
        bad_code_generated.append(elselabel + ":")
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)

class BreakNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "BreakNode"

    def generate_bad_code(self, scope, bad_code_generated):
        while_stop = retrieve_while_stop()
        num = int(while_stop[-1])
        if(num == 0):
            #print("inside error raise portion")
            raise ValueError("ERROR("+str(size_of_input-statement_count)+"): Break command not allowed outside of while loop")
        bad_code_generated.append("jump " + while_stop)

#node to Return from a function. copies a value to the function segment provided it is the correct type.
class ReturnNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "ReturnNode"

    def generate_bad_code(self, scope, bad_code_generated):
        num = function_scope
        if(num == 0):
            #print("return used outside of function")
            raise ValueError("ERROR("+str(size_of_input-statement_count)+"): Return command not allowed outside of function")
        value_to_return = self.children[0].generate_bad_code( scope, bad_code_generated)
        #print("value to return: " + value_to_return)
        #step 1 : compare types to see if the return is valid
        value_type = generated_global_variables[value_to_return].type_
        #print("return node, comparing types")
        fn_return_type = global_functions[global_function_stack[0]].return_type
        #print("return type: " + fn_return_type)
        #print("value type: " + value_type)
        if (value_type != fn_return_type):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for function return (lhs='"+value_type+"', rhs='"+fn_return_type+"')")
        #step 2 : copy the value from the expr to the fn return entry
        fn_return_slot = global_functions[global_function_stack[0]].return_entry
        #print(fn_return_slot)
        if(fn_return_type == "array(char)" or fn_return_type == "array(val)"):
            bad_code_generated.append("ar_copy {} {}".format(value_to_return, fn_return_slot))
        else:
            bad_code_generated.append("val_copy {} {}".format(value_to_return, fn_return_slot))
        return_label = get_entry();
        if (function_scope == 1):
            function_registers.append(return_label);
        bad_code_generated.append("pop {}".format(return_label));
        bad_code_generated.append("jump {}".format(return_label));
        

#Node to contain a 'while' conditional. must resolve to a value.  
class WhileConditionNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "WhileConditionNode"

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        whilelabel = get_while_start()
        end_label = retrieve_while_stop()
        bad_code_generated.append(whilelabel + ":")
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        type_0 = generated_global_variables[child_0_entry].type_
        if(type_0 != "val"):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): operand must resolve to a 'val' for while condition (lhs='"+type_0+"'")
        
        bad_code_generated.append("val_copy {} {}".format(child_0_entry,entry))
        bad_code_generated.append("jump_if_0 {} {}".format(entry ,end_label))
        child_1_entry = self.children[1].generate_bad_code(scope, bad_code_generated)
        bad_code_generated.append("jump {}".format(whilelabel))
        bad_code_generated.append(end_label + ":")
        get_while_stop()

#Node to do binary comparisons and return 1 or 0 as result
class BinaryComparisonNode(BaseNode):
    def __init__(self, children, operator):
        BaseNode.__init__(self,children)
        self.name = "BinaryComparisonNode{}".format(operator)
        self.operator = operator

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        child_1_entry = self.children[1].generate_bad_code(scope, bad_code_generated)
        type_0 = generated_global_variables[child_0_entry].type_
        type_1 = generated_global_variables[child_1_entry].type_
        if(type_0 != type_1):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for relationship operator (lhs='"+type_0+"', rhs='"+type_1+"')")
        if (self.operator == "=="):
            bad_code_generated.append("test_equ {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("comparing ==")
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1])) #type is all that matters instead of result
            #equal to
        elif (self.operator == ">="):
            #greater than or equal to
            bad_code_generated.append("test_gte {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("comparing >=")
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1]))
        elif (self.operator == "<="):
            #less than or equal to 
            bad_code_generated.append("test_lte {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("comparing <=")
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1]))
        elif (self.operator == "<"):
            #less than
            bad_code_generated.append("test_less {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("comparing <")
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1]))
        elif (self.operator == ">"):
            #greater than 
            bad_code_generated.append("test_gtr {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("comparing >")
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1]))
        elif (self.operator == "!="):
            #not equal to
            bad_code_generated.append("test_nequ {} {} {}".format(child_0_entry, child_1_entry, entry))
            #print("comparing !=")
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1]))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry

#Class for binary addition/subtraction/multiplication or division
class BinaryMathNode(BaseNode):
    #covers addition, division, multiplication, subtraction
    def __init__(self, children, operator):
        BaseNode.__init__(self,children)
        self.name = "BinaryMathNode{}".format(operator)
        self.operator = operator

    def generate_bad_code(self, scope, bad_code_generated):
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        child_1_entry = self.children[1].generate_bad_code(scope, bad_code_generated)
        type_1 = generated_global_variables[child_0_entry].type_
        type_0 = generated_global_variables[child_1_entry].type_
        if(type_0 != "val" or type_1 != "val"):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types are not values for math operator (lhs='"+type_0+"', rhs='"+type_1+"')")
        entry = get_entry()
        #print("{} = {} {} {}".format(
               #entry, child_0_entry, self.operator, child_1_entry))
        if (self.operator == '*'):
            #mult s0 s9 s10
            #multiplication
            bad_code_generated.append("mult {} {} {}".format(child_0_entry, child_1_entry, entry))
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1])) #instead of result, just use the types anyway
        elif (self.operator == '+'):
            bad_code_generated.append("add {} {} {}".format(child_0_entry, child_1_entry, entry))
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1]))
            #addition 
        elif (self.operator == '-'):
            bad_code_generated.append("sub {} {} {}".format(child_0_entry, child_1_entry, entry))
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1]))
        elif (self.operator == '/'):
            bad_code_generated.append("div {} {} {}".format(child_0_entry, child_1_entry, entry))
            generated_global_variables[entry] = TableEntry("val",ValLiteralNode([1]))
        #print("# Done with math node {}".format(self))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry


class StatementNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "StatementNode"

    def generate_bad_code(self, scope, bad_code_generated):
        child_entries = []
        if(isinstance(self.children[0],str)):
            print("empty Statement, string contained")
        else:
            for child in self.children:
                child_entry = child.generate_bad_code(scope, bad_code_generated)
                child_entries.append(child_entry)
        return 

class BlockNode(BaseNode):
    def __init__(self, children,scope = 0):
        BaseNode.__init__(self,children)
        self.name = "BlockNode"
        self.scope = scope

    def generate_bad_code(self, scope, bad_code_generated,function_ID = None):
        self.scope = scope + 1;
        #print("Scope in block node: " + str(self.scope))
        #print("called scope: " + str(scope))
        block_start = get_block_start();
        block_end = return_block_end()
        bad_code_generated.append(block_start+ ":")
        for child in self.children:
            child.generate_bad_code(self.scope, bad_code_generated)
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
            if (generated_global_variables[key].ID != None and generated_global_variables[key].scope == scope):
                generated_global_variables[key].active = False
            elif (generated_global_variables[key].ID == None):
                #extraneous register found
                #print("register to remove: " + key)
                keys_to_remove.append(key)
        #for item in keys_to_remove:
            #generated_global_variables.pop(item)
            
#class for parameters of a function definition. They, unlike normal declarations, can repeat names already used, and never have an initial value.
class ParamDeclareNode(BaseNode):
    def __init__(self,var_type,ID):
        BaseNode.__init__(self,None)
        self.type_name = var_type
        self.ID = ID
        self.name = "ParamDeclareNode"
        self.fn_id = "";
    def generate_bad_code(self, scope, bad_code_generated, entry_formed):
        #print("declaring variable")
        entry = entry_formed
        #print("variable type (self) " + self.type_name)
        new_value = 0
        for key in generated_global_variables:
            if (generated_global_variables[key].ID == self.ID and generated_global_variables[key].scope==scope and generated_global_variables[key].active== True and generated_global_variables[key].fn_id == self.fn_id and self.fn_id !=""):
                #print("Id already existed in declaration")
                raise NameError("ERROR("+ str(size_of_input-statement_count) +"): variable already declared in this scope '"+ str(self.ID) +"' ")
        
        #(self,type_, value,scope = 1, active = True, var_name= None, size = None,array_type = False,array_index=None,array_parent = None)
        if (self.type_name == "array(char)" or self.type_name == "array(val)"):
            new_table_entry = TableEntry(self.type_name, 0, scope, True, self.ID,0, True,None, None)
            new_table_entry.fn_id = self.fn_id;
        else:
            new_table_entry = TableEntry(self.type_name, 0, scope, True, self.ID,None, False,None, None)
            new_table_entry.fn_id = self.fn_id;
        generated_global_variables[entry] = new_table_entry
        print("initializing param entry for parameter: " + entry)
        return entry 


class DeclarationNode(BaseNode):
    def __init__(self,children,var_type,ID):
        BaseNode.__init__(self,children)
        self.type_name = var_type
        self.ID = ID
        self.name = "DeclarationNode"
    def generate_bad_code(self, scope, bad_code_generated):
        #print("declaring variable")
        entry =get_entry() if(self.type_name == "val" or self.type_name == "char")  else get_array_entry()
        #print("variable type (self) " + self.type_name)
        new_value = 0
        for key in generated_global_variables:
            if (generated_global_variables[key].ID == self.ID and generated_global_variables[key].scope==scope and generated_global_variables[key].active== True and generated_global_variables[key].fn_id == ""):
                raise NameError("ERROR("+ str(size_of_input-statement_count) +"): variable already declared in this scope '"+ str(self.ID) +"' ")
        
        for child in self.children:
            if (isinstance(child,ValLiteralNode) or isinstance(child,CharLiteralNode) or isinstance(child, ArrayCharNode)):
                new_value = child.generate_bad_code(scope, bad_code_generated)
                type_1 = generated_global_variables[new_value].type_
                if(self.type_name != type_1):
                    raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for declaring (lhs='"+self.type_name+"', rhs='"+type_1+"')")
                print(new_value)
                if (self.type_name == "val" or self.type_name == "char"):
                    bad_code_generated.append("val_copy {} {}".format(new_value,entry))
                else:
                    bad_code_generated.append("ar_copy {} {}".format(new_value,entry))
            else:
                #print("new value {} = {}".format(entry, self.children[0]))
                new_value = self.children[0].generate_bad_code(scope, bad_code_generated)
                print("did generate bad code for declaring noninit array")
                print(new_value)
                
                type_1 = generated_global_variables[new_value].type_
                if(self.type_name != type_1):
                    raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for declaring (lhs='"+self.type_name+"', rhs='"+type_1+"')")
                print(new_value)
                #print("Value stored here: " + str(generated_global_variables[new_value].value))
                if(self.type_name == "val" or self.type_name == "char"):
                    bad_code_generated.append("val_copy {} {}".format(new_value,entry))
                else:
                    bad_code_generated.append("ar_copy {} {}".format(new_value, entry))
        #it ceases being active when its block stops
        #(self,type_, value,scope = 1, active = True, var_name= None, size = None,array_type = False,array_index=None,array_parent = None)
        new_table_entry = TableEntry(self.type_name, generated_global_variables[new_value].value, scope, True, self.ID,generated_global_variables[new_value].size, False,None, None)
        generated_global_variables[entry] = new_table_entry
        if(function_scope == 1):
            print("declaration add: " + entry)
            function_registers.append(entry)
        return entry 

#node for accessing an ID. a node with a single child, the ID's value    
#returns the entry in the table where its value is. this can be used
#for both updating and querying it
class IdAccessNode(BaseNode):
    def __init__(self, children,ID,index = None):
        BaseNode.__init__(self,children)
        self.ID = ID
        self.name = "IdAccessNode"
        self.index = index

    def generate_bad_code(self, scope, bad_code_generated):
        best_scope = 0;
        entry = ""
        for key in generated_global_variables:
            if (generated_global_variables[key].ID == self.ID and generated_global_variables[key].scope<=scope and generated_global_variables[key].ID != None):
                if (generated_global_variables[key].scope>=best_scope and generated_global_variables[key].active == True):
                    best_scope = generated_global_variables[key].scope
                    entry = key
                
        if (entry == ""):
            raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(self.ID) +"' ")
        #if index isnt none, we need to create a new entry
        #our base 'entry' is the array, we want indexed value
        elif (self.index !=None):
            if(generated_global_variables[entry].type_ != "array(char)" and generated_global_variables[entry].type_ != "array(val)"):
                raise TypeError("ERROR("+str(size_of_input-statement_count)+"): variable must be an 'array' type to index (rhs='"+generated_global_variables[entry].type_+"')")
            indexed_entry = get_entry()
            index_register = self.index.generate_bad_code(scope, bad_code_generated)
            index_type = generated_global_variables[index_register].type_
            if(index_type != "val"):
                raise TypeError("ERROR("+str(size_of_input-statement_count)+"): index must be a 'val' type (rhs='"+index_type+"')")
            bad_code_generated.append("ar_get_idx {} {} {}".format(entry, index_register, indexed_entry))
        #self,type_, value,scope = 1, active = True, var_name= None, size = None,array_type = False,array_index=None,array_parent = None)
            index_value_type = "val" if (generated_global_variables[entry].type_ == "array(val)") else "char"
            #print("index type: " + index_value_type)
            #generated_global_variables[indexed_entry] = TableEntry(index_value_type,"value unknown at compile time",scope, True, None, None, True, self.index,entry)
            generated_global_variables[indexed_entry] = TableEntry(index_value_type,"value unknown at compile time",scope, True, None, None, True, index_register,entry)
            #if(function_scope ==1):
            #    print("id access add: " + indexed_entry)
            #    function_registers.append(indexed_entry)
            return indexed_entry
        else:
            #if(function_scope ==1):
            #    print("id access add: " + entry)
            #    function_registers.append(entry)
            return entry
        
#node class to allow assigning values to variables after declaration
#the generate method returns the id of the variable in the generated table,
#so essentially its new value.
#should have 2 children, an idaccessnode and an expression to set equal to
class IdAssignmentNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "IdAssignmentNode"
    def generate_bad_code(self, scope, bad_code_generated):
        entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        #if assigning from an array index, it should work as is.
        new_assign_value = self.children[1].generate_bad_code(scope, bad_code_generated)
        entry_table = generated_global_variables[entry]
        new_assign_table = generated_global_variables[new_assign_value]
        if(entry_table.array_index ==None and entry_table.type_ != "array(char)" and entry_table.type_ != "array(val)"):
            type_1 = new_assign_table.type_
            if(type_1 != entry_table.type_):
                raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for declaring (rhs='"+type_1+"')")
            #print("value stored for this variable: " +str(entry_table.value))
            entry_table.value = new_assign_table.value
            
            #print("assigning to a variable")
            bad_code_generated.append("val_copy {} {}".format(new_assign_value,entry));
            return entry
        elif(entry_table.type_ == "array(char)" or entry_table.type_ == "array(val)"):
            type_1 = new_assign_table.type_
            if(type_1 != entry_table.type_):
                raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for declaring (rhs='"+type_1+"')")
            #print("value stored for this variable: " +str(entry_table.value))
            entry_table.value = new_assign_table.value
            
            #print("array copy")
            bad_code_generated.append("ar_copy {} {}".format(new_assign_value,entry));
            return entry
        else:
            print("assigning to an array index")
            type_1 = new_assign_table.type_
            if(type_1 != entry_table.type_):
                raise TypeError("ERROR("+str(size_of_input-statement_count)+"): types do not match for assigning (rhs='"+type_1+ " lhs= " + entry_table.type_ +"')")
            print("value stored for this variable: " +str(entry_table.value))
            entry_table.value = new_assign_table.value
            entry_table.size = new_assign_table.size
            index_register = entry_table.array_index
            #.generate_bad_code(scope, bad_code_generated)
            bad_code_generated.append("ar_set_idx {} {} {}".format(entry_table.array_parent,index_register,new_assign_value));
            if(function_scope ==1):
                function_registers.append(new_assign_value)
            return new_assign_value
        #assign the new value to this in the table, output its memory location

#node for accessing the size of an array. returns a val or the var its in
#throws type error for non array types
class SizeAccessNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "SizeAccessNode"

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        #an ID access node, this should have a return type of array(something)
        child_0_table = generated_global_variables[child_0_entry]
        if(child_0_table.type_ != "array(val)" and child_0_table.type_ != "array(char)"):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): only arrays can use the 'size' method (rhs='"+type_1+"')")
        bad_code_generated.append("ar_get_size {} {}".format(child_0_entry, entry))
        #self,type_, value,scope = 1, active = True, var_name= None, size = None,array_type = False,array_index=None,array_parent = None)
        generated_global_variables[entry] = TableEntry("val",child_0_table.size,scope)
        print("size stored in the array: "+str(generated_global_variables[child_0_entry].size))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry
    
#node to update the size of an array, throws error for non array types.  
class ResizeNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "ResizeNode"

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        child_0_entry = self.children[0].generate_bad_code(scope, bad_code_generated)
        #an ID access node, this should have a return type of array(something)
        child_0_table = generated_global_variables[child_0_entry]
        if(child_0_table.type_ != "array(val)" and child_0_table.type_ != "array(char)"):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): only arrays can use the 'size' method (rhs='"+type_1+"')")
        child_1_entry = self.children[1].generate_bad_code(scope, bad_code_generated)
        child_1_table = generated_global_variables[child_1_entry]
        if (child_1_table.type_ != "val"):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): resize method requires a 'val' parameter (rhs='"+type_1+"')")
        bad_code_generated.append("ar_set_size {} {}".format(child_0_entry, child_1_entry))
        #self,type_, value,scope = 1, active = True, var_name= None, size = None,array_type = False,array_index=None,array_parent = None)
        child_0_table.size = child_1_entry
        generated_global_variables[entry] = TableEntry("val",child_0_table.size,scope)
        print("size stored in the array: "+str(generated_global_variables[child_0_entry].size))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry

#node type for printing values. For each parameter given, it out_val's it 
#or out_char's it if it is a CHAR_LITERAL
#at the end it prints a new line, with out_char '\n'
class PrintNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "PrintNode"

    def generate_bad_code(self, scope, bad_code_generated):
        child_entries = []
        for child in self.children:
            for i in range (0,len(self.children[0])):
                child_entry = child[i].generate_bad_code(scope, bad_code_generated)
                print(child_entry)
                #returns the entry id
                type_name = generated_global_variables[child_entry].type_
                if (type_name == "val"):
                    bad_code_generated.append("out_val {}".format(child_entry))
                if (type_name == "char"):
                    bad_code_generated.append("out_char {}".format(child_entry))
                elif(type_name == "array(char)" or type_name == "array(val)"):
                    #print("array input to print (char)")
                    size_entry = get_entry()
                    index_entry = get_entry()
                    check_entry = get_entry()
                    bad_code_generated.append("ar_get_size {} {}".format(child_entry,size_entry))
                    bad_code_generated.append("val_copy {} {}".format(0,index_entry))
                    label = get_block_start()
                    end_label = get_block_end()
                    bad_code_generated.append(label + ":")
                    #subtract index from size. if result is 0 we exit
                    bad_code_generated.append("sub {} {} {}".format(size_entry,index_entry,check_entry))
                    bad_code_generated.append("jump_if_0 {} {}".format(check_entry,end_label))
                    #add 1 to index AFTER reading index
                    bad_code_generated.append("ar_get_idx {} {} {}".format(child_entry,index_entry,check_entry))
                    if (type_name == "array(char)"):
                        bad_code_generated.append("out_char {}".format(check_entry))
                    else:
                        bad_code_generated.append("out_val {}".format(check_entry))
                    bad_code_generated.append("val_copy {} {}".format(1,check_entry))
                    bad_code_generated.append("add {} {} {}".format(index_entry,check_entry,index_entry))
                    bad_code_generated.append("jump {}".format(label))
                    bad_code_generated.append(end_label + ":")
                    
        bad_code_generated.append("out_char '\\n'")
        #print("done printing!")

#node to random a value. Randoms a value between 0 -> input, we just include the range. 
#Note: I assume the result is 1 for printing purposes (locally)
class RandomNode(BaseNode):
    def __init__(self, children):
        BaseNode.__init__(self,children)
        self.name = "RandomNode"

    def generate_bad_code(self, scope, bad_code_generated):
        entry = get_entry()
        generated_global_variables[entry] = TableEntry("val", ValLiteralNode([1]))
        child_0 = self.children[0].generate_bad_code(scope, bad_code_generated);
        type_0 = generated_global_variables[child_0].type_
        if (type_0 != "val"):
            raise TypeError("ERROR("+str(size_of_input-statement_count)+"): random arguments are not type 'val' (rhs='"+type_0+"')")
        sweep_range = generated_global_variables[child_0].value
        print("Randoming range: " + str(sweep_range))
        bad_code_generated.append("random {} {}".format(sweep_range.children[0],entry))
        if(function_scope ==1):
            function_registers.append(entry)
        return entry
#END OF NODES
def p_program(p):
    """
    program : statements
    """
    p[1].generate_bad_code(-1, bad_code_generated_global)

def p_zero_statements(p):
    """
    statements :
    """
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
              | array_resize ';'
              | ';'
              | function_return
    """
    global statement_count
    statement_count +=1
    if(len(p) >1):
        pn = StatementNode([p[1]])
    else:
        #print("empty statement")
        pn = StatementNode([ValLiteralNode([0])])
    p[0] = pn

def p_function_call(p):
    """
    expr : ID '(' function_args ')'
         | ID '(' ')'
    """
    if (len(p) > 4):
        p[0] = FunctionCallNode([p[3]], "function_" + p[1])
    else:
        p[0] = FunctionCallNode([], "function_" + p[1])

def p_function_declare(p):
    """
    statements : statements function_define '{' statements '}' %prec FN2
    """
    block_node = p[1]
    p[2].children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node

def p_function_declare2(p):
    """
    statements : statements function_define statement %prec FN1
    """
    block_node = p[1]
    block_node_generated = BlockNode([]);
    block_node_generated.children.append(p[3])
    p[2].children.append(p[3])
    block_node.children.append(p[2])
    p[0] = block_node
#production rule for the definition and declaration of a function
#for just declaring the function then later defining, a separate 
#prod. rule will be needed
def p_function_define(p):
    """
    function_define : FUNCTION_DEFINE type_node ID '(' function_params ')'
                    | FUNCTION_DEFINE type_node ID '(' ')'
    """
    #create a slot in the function table, update that later
    #FunctionNode ( children, type, ID )
    global global_functions
    if ("function_" + p[3] in global_functions):
        raise NameError("ERROR("+ str(size_of_input-statement_count) +"): function already exists '"+ str(p[3]) +"' ")
    if (len(p) == 7):
        print("FunctionID: " + p[3] + ":length of arguments: " + str(len(p[5])))
        new_entry = FunctionEntry("function_" + p[3], p[2], len(p[5]))
        global_functions["function_" + p[3]] = new_entry
        def_funct = FunctionNode(p[5],p[2],"function_" + p[3])
        print("fixing function params: ")
        for param in p[5]: #array of ParamDeclareNode 's 
            param.fn_id = "function_" + p[3]
        
        p[0] = def_funct
    else:
        print("no parameters for function")
        new_entry = FunctionEntry("function_" + p[3], p[2], 0)
        global_functions["function_" + p[3]] = new_entry
        def_funct = FunctionNode([],p[2],"function_" +p[3])
        p[0] = def_funct
        

def p_function_return(p):
    """
    function_return : FUNCTION_RETURN expr ';'
    """
    #need some way for a function to check if it contains a return statement.
    p[0] = ReturnNode([p[2]])
    
def p_function_params(p):
    """
    function_params : function_params ',' function_param
                    | function_param
    """
    arguments_array = []
    length = len(p)
    if (length > 2 ):
        new_array = p[1]
        new_declare = p[3]
        #new_declare.f_scope = 1;
        new_array.append(p[3])
        p[0] = p[1]
    else:
        array = []
        array.append(p[1])
        p[0] = array

#the function parameter is like a pseudo declaration, no space allocated for it until the function gets called.
def p_function_param(p):
    """
    function_param : type_node ID
    """
    #example: max(val y, val x)
    #treat it as a declaration node later, only error would be if you had 2 params with the same name
    GLOBAL_VARIABLES[p[2]] = [0];
    p[0] = ParamDeclareNode(p[1],p[2])
    
    
def p_resize_attribute(p):
    """
    array_resize : var_id COMMAND_RESIZE '(' expr ')'
    """
    #print("production rule for resize access node")
    p[0] = ResizeNode([p[1],p[4]])

def p_break(p):
    """
    break_arg : BREAK
    """
    #print("break found")
    p[0] = BreakNode([p[1]])

def p_expr_char(p):
    """
    expr : CHAR_LITERAL
    """
    p[0] = CharLiteralNode([p[1]])
    
def p_expr_string(p):
    """
    expr : STRING_LITERAL
    """
    character_array = convertString(p[1]);
    p[0] = ArrayCharNode([character_array])

def p_expr_number(p):
    """
    expr : VAL_LITERAL
    """
    val = 0
    if ('.' in p[1]):
        val = float(p[1])
    else:
        val = int(p[1])
    p[0] = ValLiteralNode([val])

def p_expr_addition(p):
    """
    expr : expr '+' expr
    """
    p[0] = BinaryMathNode([p[1], p[3]], "+")

def p_expr_subtraction(p):
    """
    expr : expr '-' expr
    """
    p[0] = BinaryMathNode([p[1], p[3]], "-")

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
    p[0] = BinaryMathNode([p[1], p[3]], "/")

def p_expr_multiplication(p):
    """
    expr : expr '*' expr
    """
    p[0] = BinaryMathNode([p[1], p[3]], "*")
    
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
    
def p_expr_boolean_or(p):
    """
    expr : expr BOOL_OR expr
    """
    p[0] = BooleanOrNode([p[1],p[3]])

def p_expr_boolean_not(p):
    """
    expr : BOOL_NOT expr %prec UMINUS
    """
    p[0] = BooleanNotNode([p[2]])

#compound assignments
#+=, -=, *=, /= (compound assignments)
def p_expr_cmpd_add(p):
    """
    expr : var_id ASSIGN_ADD expr
    """
    value = p[3]
    #GLOBAL_VARIABLES[p[1].ID][0] = BinaryMathNode([p[1],p[3]],"+")
    p[0] = IdAssignmentNode([p[1],BinaryMathNode([p[1],p[3]],"+")])

def p_expr_cmpd_sub(p):
    """
    expr : var_id ASSIGN_SUB expr
    """
        # x = x - 1 (x-=1)
        #an assign node with a child IdAccessNode and a BinaryMathNode(-)
    value = p[3]
    p[0] = IdAssignmentNode([p[1],BinaryMathNode([p[1],p[3]],"-")])

def p_expr_cmpd_mult(p):
    """
    expr : var_id ASSIGN_MULT expr
    """
    value = p[3]
    #GLOBAL_VARIABLES[p[1].ID][0] = BinaryMathNode([p[1],p[3]],"*")
    p[0] = IdAssignmentNode([p[1],BinaryMathNode([p[1],p[3]],"*")])

def p_expr_cmpd_div(p):
    """
    expr : var_id ASSIGN_DIV expr
    """
    value = p[3]
    #GLOBAL_VARIABLES[p[1].ID][0] = BinaryMathNode([p[1],p[3]],"/")
    p[0] = IdAssignmentNode([p[1],BinaryMathNode([p[1],p[3]],"/")])
        
#==, !=, <, <=, >, >= comparisons
def p_compare_eq(p):
    """
    expr : expr COMP_EQU expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],"==")
    
def p_compare_neq(p):
    """
    expr : expr COMP_NEQU expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],"!=")

def p_compare_gt(p):
    """
    expr : expr COMP_GTR expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],">")
    
def p_compare_gte(p):
    """
    expr : expr COMP_GTE expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],">=")

def p_compare_lt(p):
    """
    expr : expr COMP_LESS expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],"<")

def p_compare_lte(p):
    """
    expr : expr COMP_LTE expr
    """
    p[0] = BinaryComparisonNode([p[1],p[3]],"<=")
    
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
# a random int 0<= x < expr
def p_random(p):
    """
    expr : COMMAND_RANDOM '(' expr ')'
    """
    p[0] = RandomNode([p[3]])   


def p_type_node(p):
    """
    type_node : TYPE 
              | SPEC_TYPE '(' TYPE ')'
    """
    if (len(p) <4):
        if(p[1] == "string"):
            p[0] = "array(char)"
        else:
            p[0] = p[1]
    else:
        if(p[3] =="string"):
            raise TypeError("ERROR("+ str(size_of_input-statement_count) + ") nested string arrays not allowed")
        else:
            return_type = p[1] + "(" + p[3] + ")"
            #print("type for array: " + str(return_type))
            p[0] = return_type
#the variable declaration rule. Allows the variable to be initialized to
#either a literal value or a preexisting ID, checks to see the value you are trying to create is not in namespace already, and if you are setting it equal to an ID, that the ID exists in the namespace
def p_var_declaration(p):
    """
    declaration : type_node ID '=' expr
                | type_node ID
    """
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
        elif (p[1] =="char"):
            p[0] = DeclarationNode([CharLiteralNode([''])],p[1],p[2])
        elif (p[1] == "string" or p[1] == "array(char)"):
            #print("string type? " + p[1])
            p[0] = DeclarationNode([ArrayCharNode([[]])],p[1],p[2])
        else:
            #array val Node
            p[0] = DeclarationNode([ArrayValNode([[]])],p[1],p[2])
        
def p_variable_access(p):
    """
    expr : var_id
    """
    p[0] = p[1]
    
def p_size_attribute(p):
    """
    expr : var_id COMMAND_SIZE '(' ')'
    """
    #print("production rule for size access node")
    p[0] = SizeAccessNode([p[1]])
    
def p_id_access(p):
    """
    var_id : ID
    """
    value = 0
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(p[1]) +"' ")
    else:
        value = GLOBAL_VARIABLES[p[1]][0]
        p[0] = IdAccessNode([value],p[1])

def p_index_access(p):
    """
    var_id : ID '[' expr ']'
    """
    value = 0;
    if (p[1] not in GLOBAL_VARIABLES):
        raise NameError("ERROR("+ str(size_of_input-statement_count) +"): unknown variable '"+ str(p[1]) +"' ")
    else:
        value = GLOBAL_VARIABLES[p[1]][0]
        #add extra argument to id access node: index of the array (if it is one)
        #also need to use the secret array parts of the symbol table now
        p[0] = IdAccessNode([value],p[1],p[3])
def p_assignment(p):
    """
    expr : var_id '=' expr
    """
    #p[0] = IdAssignmentNode([IdAccessNode([GLOBAL_VARIABLES[p[1]][0]],p[1]),p[3]])
    p[0] = IdAssignmentNode([p[1],p[3]])
    #GLOBAL_VARIABLES[p[1]][0] = p[3]

#for generic scope blocks without conditionals
def p_scope_block_enter(p):
    """
    statements : statements '{' statements '}'
    """
    block_node = p[1]
    block_node.children.append(p[3])
    p[0] = block_node
    
def p_if_block_enter(p):
    """
    statements : statements if_conditional '{' statements '}' %prec IF2
    """
    #print("Entering if block")
    block_node = p[1]
    p[2].children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node
    
def p_if_else_block_enter(p):
    """
    statements : statements if_conditional '{' statements '}' else_conditional '{' statements '}' %prec IF6
    """
    #print("Entering if/else block")
    block_node = p[1]
    
    p[6].children.append(p[8])
    p[2].children.append(p[4])
    p[2].children.append(p[6])
    block_node.children.append(p[2])
    p[0] = block_node
    
def p_if_else_block_enter2(p):
    """
    statements : statements if_conditional statement else_conditional statement %prec IF3
    """
    #print("Entering if/else block")
    block_node = p[1]
    
    p[4].children.append(p[5])
    p[2].children.append(p[3])
    p[2].children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node
    
def p_if_else_block_enter3(p):
    """
    statements : statements if_conditional '{' statements '}' else_conditional statement %prec IF5
    """
    #print("Entering if/else block")
    block_node = p[1]
    
    p[6].children.append(p[7])
    p[2].children.append(p[4])
    p[2].children.append(p[6])
    block_node.children.append(p[2])
    p[0] = block_node
    
def p_if_else_block_enter4(p):
    """
    statements : statements if_conditional statement else_conditional '{' statements '}' %prec IF4
    """
    #print("Entering if/else block")
    block_node = p[1]
    
    p[4].children.append(p[6])
    p[2].children.append(p[3])
    p[2].children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node


def p_if_block_enter_2(p):
    """
    statements : statements if_conditional statement %prec IF1
    """
    #print("Entering if block")
    block_node = p[1]
    p[2].children.append(p[3])
    block_node.children.append(p[2])
    p[0] = block_node

def p_if_conditional(p):
    """
    if_conditional : IF '(' expr ')'
    """
    #print("If conditional node")
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
    block_node = p[1]
    p[2].children.append(p[4])
    block_node.children.append(p[2])
    p[0] = block_node

def p_while_block_enter2(p):
    """
    statements : statements while_conditional statement %prec IF2
    """
    block_node = p[1]
    p[2].children.append(p[3])
    block_node.children.append(p[2])
    p[0] = block_node

def p_while_conditional(p):
    """
    while_conditional : WHILE '(' expr ')'
    """
    #print("While conditional node")
    p[0] = WhileConditionNode([p[3]])

def p_error(p):
    raise SyntaxError(p)


def parse_string(input_):
    GLOBAL_VARIABLES.clear()
    #yacc.yacc(errorlog=yacc.NullLogger())
    lex.lex()
    parser = yacc.yacc()
    parser.parse(input_)
    return True


input_ = r"""
    define val countdown(val x) {
		  if (x == 0) {
		    print("hello");
		    return 0;
		  }
		  print(x);
		  countdown(x - 1);
		  return 0;
		}
		countdown(3);
		
"""
def generate_bad_code_from_string(input_):
    generated_global_variables.clear()
    GLOBAL_VARIABLES.clear()
    global_functions.clear()
    global bad_code_generated_global, S_COUNT, WHILE_COUNT, WHILE_ACTIVE
    global OR_COUNT, BLOCK_ACTIVE, BLOCK_COUNT, AND_COUNT, NOT_COUNT
    global line_count, size_of_input, statement_count, scope, IF_COUNT
    global function_code_generated_global; function_code_generated_global = []
    global global_function_stack;
    global_function_stack.clear();
    S_COUNT = 1; OR_COUNT = 0; AND_COUNT = 0; NOT_COUNT = 0;statement_count = 0;
    size_of_input = 0; scope = 0; IF_COUNT =0;
    WHILE_COUNT = 0; WHILE_ACTIVE =0; BLOCK_ACTIVE = 0; BLOCK_COUNT =0;
    bad_code_generated_global = []
    size_of_input= len(re.split('\n',input_))
    #print("length of input: " + str(len(input_)))
    #print("size of input: " + str(size_of_input));
    
    lexer = lex.lex()
    parser = yacc.yacc(errorlog=yacc.NullLogger())
    program = parser.parse(input_, lexer=lexer)
    output = bad_code_generated_global
    bad_code_return = """"""
    for element in bad_code_generated_global:
        bad_code_return += (element + '\n')
        #print(element)
    
    #functions
    bad_code_return += ("jump define_functions_end" + '\n')

    for element in function_code_generated_global:
        bad_code_return += (element + '\n')
    bad_code_return += ("define_functions_end:" + '\n')
    return bad_code_return

#function to generate ugly code from a string of good code. First generates bad code from string using the generate_bad_code_from_string fn, then converts that to ugly.
def generate_ugly_code_from_string(input_):
    bad_string = generate_bad_code_from_string(input_)
    #start heap at 10000
    ugly_code_generated = "store 10000 0 \n";
    #initialize stack into regH (20000)
    ugly_code_generated += "val_copy 20000 regH\n";
    for line in bad_code_generated_global:
        ugly_code_generated += (ugly_parse(line));
    
    ugly_code_generated += ("jump define_functions_end\n");
      
    for line in function_code_generated_global:
        ugly_code_generated += (ugly_parse(line));
    
    ugly_code_generated += ("define_functions_end:\n");
    return ugly_code_generated;

#function to convert a line of bad code into a line of ugly code.
def ugly_parse(line_):
    #split by spaces NOT contained within a '
    line_split =re.split(" ", line_);
    for i in range(0,len(line_split)):
        if(line_split[i] == "'" and line_split[i + 1] == "'"):
            #split by wrong thing, resize
            print("resizing array")
            line_split = [line_split[0],"' '", line_split[3]];
            break;
    active_line = [];
    #load scalars into registers regardless of command
    first_p = "";
    second_p = "";
        
    if(len(line_split) > 3):
        if(line_split[1][0] =="s" or line_split[1][0] == "a"):
            active_line.append("load {} regA \n".format(line_split[1][1:]));
            first_p = "regA";
        else:
            first_p = line_split[1];
        if(line_split[2][0] == "s"):
            active_line.append("load {} regB \n".format(line_split[2][1:]));
            second_p = "regB"
        else:
            second_p = line_split[2];
    active_return = "";
    if(line_split[0] == "val_copy"):
        if(line_split[1][0] =="s"):
            active_line.append("load {} regA \n".format(line_split[1][1:]));
            active_line.append("val_copy regA regB \n\n")
        else:
            active_line.append("val_copy {} regB \n".format(line_split[1]));
        active_line.append("store regB {} \n\n".format(line_split[2][1:]));
    elif(line_split[0] =="add"):
        active_line.append("add {} {} {} \n".format(first_p, second_p, "regC"))
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] =="sub"):
        active_line.append("sub {} {} {} \n\n".format(first_p, second_p, "regC"))
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] =="div"):
        active_line.append("div {} {} {} \n".format(first_p, second_p, "regC"))
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] =="mult"):
        active_line.append("mult {} {} {} \n".format(first_p, second_p, "regC"))
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] == "test_less"):
        active_line.append("test_less {} {} regC \n".format(first_p, second_p));
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] == "test_gtr"):
        active_line.append("test_gtr {} {} regC \n".format(first_p, second_p));
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] == "test_equ"):
        active_line.append("test_equ {} {} regC \n".format(first_p, second_p));
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] == "test_nequ"):
        active_line.append("test_nequ {} {} regC \n".format(first_p, second_p));
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] == "test_gte"):
        active_line.append("test_gte {} {} regC \n".format(first_p, second_p));
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] == "test_lte"):
        active_line.append("test_lte {} {} regC \n".format(first_p, second_p));
        active_line.append("store regC {} \n\n".format(line_split[3][1:]));
    elif(line_split[0] == "jump_if_0"):
        if(line_split[1][0] =="s"):
            active_line.append("load {} regA \n\n".format(line_split[1][1:]));
            active_line.append("jump_if_0 regA {} \n\n".format(line_split[2]));
            #load scalar into register
        else:
            active_line.append("jump_if_0 {} {} \n\n".format(line_split[1],line_split[2]));
    elif(line_split[0] == "jump_if_n0"):
        if(line_split[1][0] =="s"):
            active_line.append("load {} regA \n".format(line_split[1][1:]));
            active_line.append("jump_if_n0 regA {} \n\n".format(line_split[2]));
            #load scalar into register
        else:
            active_line.append("jump_if_n0 {} {} \n\n".format(line_split[1],line_split[2]));
    elif(line_split[0] == "jump"):
        #only alter this if it is jumping to a scalar
        if (line_split[1][0] == "s" and re.match(r's[0-9]+', line_split[1])!= None):
            print("match from jump regex")
            active_line.append("load {} regA\n".format(line_split[1][1:]));
            active_line.append("jump regA\n\n");
        else:
            active_return = line_ + "\n\n";
    elif(line_split[0] == "out_val"):
        if(line_split[1][0] == "s"):
            active_line.append("load {} regA \n".format(line_split[1][1:]))
            active_line.append("out_val regA \n\n")
        else:
            active_line.append("out_val {} \n\n".format(line_split[1]))
    elif(line_split[0] == "out_char"):
        if(line_split[1][0] == "s"):
            active_line.append("load {} regA \n".format(line_split[1][1:]))
            active_line.append("out_char regA \n\n")
        else:
            active_line.append("out_char {} \n\n".format(line_split[1]))
    elif(line_split[0] == "random"):
        if(line_split[1][0] == "s"):
            active_line.append("load {} regA \n".format(line_split[1][1:]))
            active_line.append("random regA regB \n\n")
        else:
            active_line.append("random {} regB \n".format(line_split[1]))
        active_line.append("store regB {} \n\n".format(line_split[2][1:]))
    elif(line_split[0] == "ar_get_size"): #first one is an array id always
        active_line.append("load {} regA \n".format(line_split[1][1:]))
        active_line.append("mem_copy regA {}\n\n".format(line_split[2][1:]))
    elif(line_split[0] == "ar_get_idx"): #should get params caught by intro
        active_line.append("add regA 1 regA\n")
        active_line.append("add regA {} regA\n".format(second_p))
        active_line.append("mem_copy regA {} \n\n".format(line_split[3][1:]))
    elif(line_split[0] == "ar_set_idx"):
        active_line.append("add regA 1 regA\n")
        active_line.append("add regA {} regA\n".format(second_p))
        active_line.append("mem_copy {} regA \n\n".format(line_split[3][1:]))
    elif(line_split[0] == "ar_set_size"): #long one
        label_number = get_label();
        start_label = "resize_start_" + str(label_number);
        stop_label = "resize_end_" + str(label_number);
        active_line.append("load {} regA\n".format(line_split[1][1:]))
        if(line_split[2][0] == "s"):
            active_line.append("load {} regB\n".format(line_split[2][1:]))
            second_p = "regB";
        else:
            active_line.append("val_copy {} regB\n".format(line_split[2]))
            second_p = "regB" #just a number in this case
        #jump here if the array a(x) 's x-memory location holds a zero, in which case give it the current free memory location.
        active_line.append("array_init_subroutine_start_"+ str(label_number) + ":\n")
        active_line.append("jump {}\n".format("array_init_subroutine_end_"+ str(label_number)))
        active_line.append("inner_start_" + str(label_number) + ":\n")
        #this part only reachable if we explicitly jump to the actual label
        active_line.append("load 0 regG\n");
        #give it the value at mem. position zero, reevaluate regA
        active_line.append("store regG {}\n".format(line_split[1][1:]))
        active_line.append("load {} regA\n".format(line_split[1][1:]))
        active_line.append("array_init_subroutine_end_"+ str(label_number) + ":\n")
        #if {regA} holds zero, jump to inner start
        active_line.append("jump_if_0 regA {}\n".format("inner_start_" + str(label_number)))
        #this regC is supposed to be the size of A, but if A was 0 valued it never got a memory location
        #we need a subroutine so that if a1's "1" memory location holds a "0" 
        #(never initialized) then we give it the free memory position.
        active_line.append("load regA regC\n")
        active_line.append("store {} regA\n".format(second_p))
        active_line.append("test_lte {} regC regD\n".format(second_p)) #see if
        #we need to allocate new space
        active_line.append("jump_if_n0 regD {}\n".format(stop_label)) #Done!
        active_line.append("load 0 regD\n")
        active_line.append("add regD 1 regE\n")
        active_line.append("add regE {} regE\n".format(second_p))
        active_line.append("store regE 0\n") #save new free mem. position
        active_line.append("store regD {}\n".format(line_split[1][1:]))
        active_line.append("store {} regD\n".format(second_p)) #store new size
        active_line.append("add regA regC regC\n")
        active_line.append(start_label + ":\n")
        active_line.append("add regA 1 regA\n") #FROM array
        #once this A reaches the limit of the original array, it starts inserting nothing
        active_line.append("add regD 1 regD\n") #TO array
        active_line.append("test_gtr regD regE regF\n")
        active_line.append("jump_if_n0 regF {}\n".format(stop_label))
        active_line.append("test_lte regA regC regF\n")
        active_line.append("jump_if_0 regF {}\n".format("passover_marker_" + str(label_number)))
        active_line.append("mem_copy regA regD\n") # copy current index
        active_line.append("passover_marker_" + str(label_number) + ":\n")
        active_line.append("jump {}\n".format(start_label)) #jump to start of 
        active_line.append(stop_label + ":\n\n") #end of copy loop
    elif(line_split[0] == "ar_copy"): #ar_set_size plus a bunch of value copies
        label_number = get_label();
        start_label = "resize_start_" + str(label_number);
        stop_label = "resize_end_" + str(label_number);
        active_line.append("array_copy_start:\n")
        active_line.append("load {} regA\n".format(line_split[1][1:]))
        #both will be arrays
        active_line.append("load {} regB\n".format(line_split[2][1:]))
        second_p = "regB"; 
        active_line.append("array_init_subroutine_start_"+ str(label_number) + ":\n")
        active_line.append("jump {}\n".format("array_init_subroutine_end_"+ str(label_number)))
        active_line.append("inner_start_" + str(label_number) + ":\n")
        #this part only reachable if we explicitly jump to the actual label
        active_line.append("load 0 regG\n");
        active_line.append("store regG {}\n".format(line_split[2][1:]))
        active_line.append("load {} regB\n".format(line_split[2][1:]))
        active_line.append("array_init_subroutine_end_"+ str(label_number) + ":\n")
        active_line.append("jump_if_0 regB {}\n".format("inner_start_" + str(label_number)))
        active_line.append("load regA regC\n") #load old array size into regC
        active_line.append("store regC {}\n".format(second_p)) #replace old size
        #we need to store register A's size into register B, as B is the target
        #not done this just means the size is right
        active_line.append("load regB regG \n")
        active_line.append("load 0 regD\n") #load free mem. pos
        active_line.append("add regD 1 regE\n") #increment to first arr. pos
        active_line.append("add regE {} regE\n".format("regG")) #move regE to new free memory position
        active_line.append("store regE 0\n") #save new free mem. position
        active_line.append("store regD {}\n".format(line_split[2][1:])) #redirect array pointer to new start position
        active_line.append("store {} regD\n".format("regC")) #store new size
        active_line.append(start_label + ":\n")
        #right now this is copying array 1's values over
        active_line.append("add regA 1 regA\n") #FROM array
        active_line.append("add regD 1 regD\n") #TO array
        active_line.append("test_gte regD regE regF\n")
        active_line.append("jump_if_n0 regF {}\n".format(stop_label))
        active_line.append("mem_copy regA regD\n") # copy current index
        active_line.append("jump {}\n".format(start_label)) #jump to start of 
        active_line.append(stop_label + ":\n\n") #end of copy loop
    #need arr_pop, arr_push, pop, push. for now just pop.
    elif(line_split[0] == "pop"):
        active_line.append("sub regH 1 regH\n");
        active_line.append("load regH regA\n");
        active_line.append("store regA {}\n\n".format(line_split[1][1:]));
    elif(line_split[0] == "push"):
        #either push a value or push a label
        if (re.match(r'[as][0-9]+', line_split[1])!= None):
            #pushing a register
            active_line.append("#" + line_ + '\n')
            active_line.append("load {} regA\n".format(line_split[1][1:]))
        else:
            active_line.append("#" + line_ + '\n')
            active_line.append("val_copy {} regA\n".format(line_split[1]))
        active_line.append("store regA regH\n")
        active_line.append("add 1 regH regH\n")
    elif(line_split[0] == "ar_push"):
        active_line.append("#" + line_ + '\n')
        active_line.append("load {} regA\n".format(line_split[1][1:]))
        active_line.append("store regA regH\n")
        active_line.append("add 1 regH regH\n")
    elif(line_split[0] == "ar_pop"):
        active_line.append("sub regH 1 regH\n");
        active_line.append("load regH regA\n");
        active_line.append("store regA {}\n\n".format(line_split[1][1:]));
    #TODO: ar_pop and ar_push    
    
    else: #comment or label
        active_return = line_ + "\n";
    for line in active_line:
        active_return += line;
    return active_return;
    
if __name__ == "__main__":
    #parse_string(input_)
    #source = sys.stdin.read()
    #result = generate_bad_code_from_string(input_)
    print("Output from parse: ")
    #print(result)
    #final_output = run_bad_code_from_string(result)
    #print(final_output);
    #ugly = generate_ugly_code_from_string(input_);
    #print(ugly)
    #print("ugly code compiler")
    #output = run_ugly_code_from_string(ugly)
    #print(output)
    
