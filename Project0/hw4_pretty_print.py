class Node:
    def __init__(self, children=None, data=None):
        self.children = children
        self.data = data
        self.name = "Node"

class OtherNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.name = "OtherNode"


class BinaryNode(Node):
    def __init__(self, children):
        if(len(children) != 2):
            raise NotImplemented("Only 2 nodes allowed at binary node")
        Node.__init__(self, children)
        self.name= "BinaryNode"


class DataNode(Node):
    def __init__(self, data):
        Node.__init__(self, None, data)
        self.name= "DataNode"


class ManyNode(Node):
    def __init__(self, children):
        Node.__init__(self, children)
        self.name= "ManyNode"

#todo:make this a depth first search
def node_to_string(node):
    return(node_to_string_ret(node,0))

def node_to_string_ret(node,depth):
    
    string_to_return = ""
    for i in range(1,depth):
        string_to_return += "."
    string_to_return += node.name
    #print(string_to_return)
    if(node.data != None):
        string_to_return += " data = "
        string_to_return += str(node.data)
    string_to_return += ":"
    if (node.children != None):
        for child in node.children:
            string_to_return += '\n'
            string_to_return += "."
            string_to_return += (node_to_string_ret(child,depth+1))
    return(string_to_return)

#n = BinaryNode([BinaryNode([DataNode(14), DataNode(64)]), DataNode(100)])
#result = node_to_string(n)
#print(result)