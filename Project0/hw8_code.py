import sys

memory_array = {}
variables = {}
def run_command(command_list):
  final_output = ""
  command_list = command_list.split(" ")
  if(command_list[0] == "out_val"):
    if(command_list[1] in variables):
      final_output = final_output+variables[command_list[1]]
    else:
      final_output = final_output+command_list[1]
  elif(command_list[0] == "val_copy"):
    if (command_list[1] in variables):
      #print("command in variables")
      variables[command_list[2]] = variables[command_list[1]]
    else:
      #print(command_list[1])
      variables[command_list[2]] = command_list[1]
  elif(command_list[0] == "add"):
    if (command_list[1] in variables):
      if (command_list[2] in variables):
        variables[command_list[3]] = str(int(variables[command_list[1]]) + int(variables[command_list[2]]))
      else:
        variables[command_list[3]] = str(int(variables[command_list[1]]) + int(command_list[2]))
    else:
      if (command_list[2] in variables):
        variables[command_list[3]] = str(int(command_list[1]) + int(variables[command_list[2]]))
      else:
        variables[command_list[3]] = str(int(command_list[1]) + int(command_list[2]))
  elif(command_list[0] == "store"):
    # store (value) (location)
    
    if (command_list[1] in variables):
      if (command_list[2] in variables):
        memory_array[variables[command_list[2]]] = variables[command_list[1]]
      else:
        memory_array[command_list[2]] = variables[command_list[1]]
    else:
      if (command_list[2] in variables):
        memory_array[variables[command_list[2]]] = command_list[1]
      else:
        memory_array[command_list[2]] = command_list[1]
  elif(command_list[0] == "load"):
    #load (location) (destination {guaranteed a register})
    if(command_list[1] in variables):
      variables[command_list[2]] = memory_array[variables[command_list[1]]]
    else:
      variables[command_list[2]] = memory_array[command_list[1]]
  return final_output
  
if __name__ == "__main__":
  output = ""
  source = sys.stdin.read()
  source_delimited = source.split('\n')
  for element in source_delimited:
    output = output + run_command(element)
  print(output)