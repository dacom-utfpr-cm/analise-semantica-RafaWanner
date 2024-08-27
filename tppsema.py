import sys
import os
import subprocess
import json
import re

from sys import argv, exit

import logging

logging.basicConfig(
     level = logging.DEBUG,
     filename = "sema.log",
     filemode = "w",
     format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

import ply.yacc as yacc

from tppparser import main as tppparser_main

# Get the token map from the lexer.  This is required.
from tpplex import tokens

from mytree import MyNode
from anytree.exporter import DotExporter, UniqueDotExporter
from anytree import Node, RenderTree, AsciiStyle

from myerror import MyError

error_handler = MyError('SemaErrors')
syn = MyError('ParserErrors')
le = MyError('LexerErrors')

checkKey = False
checkTpp = False

root = None

# Reconstruir Arvore
def parse_label(line):
    match = re.search(r'\[label="(.+?)"\]', line)
    return match.group(1) if match else None

def reconstruct_tree_from_dot(filepath):
    nodes = {}
    edges = []

    with open(filepath, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if '->' in line:  # Process edge
            parent, child = line.split(' -> ')
            parent = parent.strip().strip('"')
            child = child.strip().strip(';').strip('"')
            edges.append((parent, child))
        elif '[' in line and 'label=' in line:  # Process node
            node_id = line.split(' ')[0].strip().strip('"')
            label = parse_label(line)
            nodes[node_id] = Node(label)

    # Creating the tree structure by connecting nodes
    for parent, child in edges:
        nodes[child].parent = nodes[parent]

    # Finding the root (the node without a parent)
    root = None
    for node in nodes.values():
        if node.is_root:
            root = node
            break

    return root

# Programa Principal.
def run_tppparser(args):
    # Construct the command line arguments
    cmd = ['python', 'tppparser.py'] + args
    try:
        # Run the subprocess and capture the output and error
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout, None  # Return stdout if no errors
    except subprocess.CalledProcessError as e:
        return None, e.stderr  # Return stderr if there was an error

def main():
    global checkKey
    global checkTpp
    global errorArray
    
    if(len(sys.argv) < 2):
        errorArray.append(error_handler.newError(checkKey, 'ERR-SEM-USE'))
        raise TypeError(error_handler.newError(checkKey, 'ERR-SEM-USE'))

    posArgv = 0

    for idx,arg in enumerate(sys.argv):
        aux = arg.split('.')
        if aux[-1] == 'tpp':
            checkTpp = True
            posArgv = idx
        
        if arg == "-k":
            checkKey = True
    
    if checkKey and len(sys.argv) < 3:
        errorArray.append(le.newError(checkKey, 'ERR-SEM-USE'))
        raise TypeError(errorArray)
    elif not checkTpp:
        errorArray.append(le.newError(checkKey, 'ERR-SEM-NOT-TPP'))
        raise IOError(errorArray)
    elif not os.path.exists(argv[posArgv]):
        errorArray.append(le.newError(checkKey, 'ERR-SEM-FILE-NOT-EXISTS'))
        raise IOError(errorArray)
    else:
        stdout, stderr = run_tppparser(sys.argv)
        
        if stderr:
            print("Error while running tppparser.py:\n", stderr)
            sys.exit(1)
        
        # If successful, parse and process the result from stdout
        # For example, if stdout contains the `root` information or any result:
        print(stdout) # mostra os print to tpparser
        # Parse `stdout` if it contains relevant data

        # Example usage:
        filepath = sys.argv[1] + ".unique.ast.dot"
        root = reconstruct_tree_from_dot(filepath)

        # To visualize the tree:
        for pre, fill, node in RenderTree(root):
            print(f"{pre}{node.name}")
    
    if len(errorArray) > 0:
        raise IOError(errorArray)

if __name__ == "__main__": 
    try:
        main()
    except Exception as e:
        print('\n--------------------------------------------- ERR-SEM ---------------------------------------------\n')
        #for x in range(len(e.args[0])):
            #print (e.args[0][x])
    except (ValueError, TypeError):
        print('\n-------------------------------------------------------------------------------------------\n')
        for x in range(len(e.args[0])):
            print (e.args[0][x])
