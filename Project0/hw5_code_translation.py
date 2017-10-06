from sys import stdin

def variable_check(input_):
  scope = 0;
  variable_dictionary = [];
  #each slot has var_dict["name"][0] = type, var_dict["name"][1] = name
  tokens = input_.split('\n')
  for element in tokens:
    line_split = element.split(' ')
    if(line_split[0]== "val" or line_split[0]== "char" or line_split[0]== "array(val)" or line_split[0]== "array(char)" or line_split[0]== "string"):
      if (line_split[0] == "string"):
        string_to_print = "Trying to declare "+"("+line_split[1]+" of type " + "array(char)" + "):"
      else:
        string_to_print = "Trying to declare "+"("+line_split[1]+" of type " + line_split[0] + "):"
      flag = True
      for var_name in variable_dictionary:
            if(var_name[1] == line_split[1]):
                string_to_print += " ERROR: Redeclaration"
                flag = False
                break
      if (flag):
          if (line_split[0]== "string"):
            variable_dictionary.append(["array(char)",line_split[1]])
          else:
            variable_dictionary.append([line_split[0],line_split[1]])
          string_to_print += " SUCCESS"
      print(string_to_print)
    elif (len(line_split) == 2):
      string_to_print = "Trying to use " +"("+ line_split[0]+")"+ ":"
      
      flag = False
      for var_name in variable_dictionary:
        if(var_name[1] == line_split[0]):
          flag = True
          string_to_print += " SUCCESS: " + "Found a " + var_name[0]
          #found one we can use
      if(flag == False):
        string_to_print += " ERROR: Usage before declaration"
      print(string_to_print)
    elif(len(line_split) == 4 and line_split[1] == '>'):
      string_to_print = "Trying to greater-than: "
      var_1 = None; var_2= None
      for var_name in variable_dictionary:
            if(var_name[1] ==line_split[2]):
              var_2 = var_name
            if(var_name[1] ==line_split[0]):
              var_1 = var_name
      if (var_1 == None or var_2 == None):
        string_to_print += "ERROR usage before declaration"
      else:
        string_to_print += "types are "+ var_1[0] +" and " + var_2[0] + ": "
        if (var_1[0] == "array(char)" or var_2[0] == "array(char)"):
          string_to_print += "ERROR: type doesn't support greater-than"
        elif (var_1[0] != var_2[0]):
          string_to_print += "ERROR: types don't match"
        else:
          string_to_print += "SUCCESS"
      print(string_to_print)
  return_val = input_
  return return_val
  
input_ = stdin.read()
variable_check(input_)