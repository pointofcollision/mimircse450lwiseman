from sys import stdin

def variable_check(input_):
  scope = 0;
  variable_dictionary = [];
  tokens = input_.split('\n')
  for element in tokens:
    line_split = element.split(' ')
    if (line_split[0] =="open" and line_split[1] == "scope"):
        print("Trying to open scope at " + str(scope) + ": SUCCESS")
        scope = scope+1;
    elif (line_split[0] =="close" and line_split[1] == "scope"):
        print("Trying to close scope at " + str(scope) + ": SUCCESS")
        for var_name in variable_dictionary:
            if(var_name[0] == scope):
                variable_dictionary.remove(var_name)
                #print("variable out of scope")
        scope = scope-1;
    elif (line_split[0]== "declare"):
      string_to_print = "Trying to declare "+line_split[1]+ " at scope " + str(scope) + ":"
      flag = True
      for var_name in variable_dictionary:
            if(var_name[1] == line_split[1] and var_name[0] == scope):
                string_to_print += " FAILED"
                flag = False
                break
      if (flag):
          variable_dictionary.append([scope,line_split[1]])
          string_to_print += " SUCCESS"
      print(string_to_print)
    elif (line_split[0] == "use"):
      string_to_print = "Trying to use " + line_split[1]+ " at scope "+str(scope)+ ":"
      #first check to see if we have one in our scope, then check for outside
      #(below current scope)
      flag = False
      scope_found = 0
      for var_name in variable_dictionary:
        if(var_name[0] <= scope and var_name[1] == line_split[1]):
          if(scope_found <var_name[0]):
            scope_found = var_name[0]
          flag = True
          #found one we can use
      if(flag == False):
        string_to_print += " FAILED"
      else:
        string_to_print += " SUCCESS" + " (found in scope "+str(scope_found)+")"
      print(string_to_print)
  return_val = input_
  return return_val
  
  

input_ = stdin.read()
variable_check(input_)
#for line in input_.splitlines():
#    raise NotImplementedError()
