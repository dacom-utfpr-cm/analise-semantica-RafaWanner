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

errorArray = []

root = None



#    def find_node(node, target_name):
#        if node.name == target_name:
#            return node
#        for child in getattr(node, 'children', []):
#            result = find_node(child, target_name)
#            if result:
#                return result
#        return None
#
#    # Search for the 'principal' function declaration in the tree
#    principal_node = find_node(root, 'principal')
#    
#    if principal_node is None:
#        errorArray.append(error_handler.newError(checkKey, 'ERR-SEM-MAIN-NOT-DECL'))

#    def find_all_nodes(node, target_name, result=None):
#        if result is None:
#            result = []
#        if node.name == target_name:
#            result.append(node)
#        for child in getattr(node, 'children', []):
#            find_all_nodes(child, target_name, result)
#        return result
#
#    # Usage
#    principal_nodes = find_all_nodes(root, 'principal')
#    if not principal_nodes:
#        errorArray.append(error_handler.newError(checkKey, 'ERR-SEM-MAIN-NOT-DECL'))



# Funcoes Basicas

def walk_tree(node, path):
    """Walk the tree following the given path of node names and return the final node."""
    current_node = node
    for name in path:
        current_node = next((child for child in current_node.children if child.name == name), None)
        if current_node is None:
            return None
    return current_node

def check_node_exists(node, error_code):
    """Check if node exists, otherwise report an error."""
    if node is None:
        errorArray.append(error_handler.newError(checkKey, error_code))
        return False
    return True

def find_all_nodes(node, target_name, result=None):
    if result is None:
        result = []
    if node.name == target_name:
        result.append(node)
    for child in getattr(node, 'children', []):
        find_all_nodes(child, target_name, result)
    return result

def find_all_nodes_children(node, path, result=None):
    if result is None:
        result = []
    
    # If the path is empty, append the current node to the result
    if not path:
        result.append(node)
        return result
    
    # Check if the current node matches the first element of the path
    if node.name == path[0]:
        # Recursively search in children with the remaining path
        for child in getattr(node, 'children', []):
            find_all_nodes_children(child, path[1:], result)
    
    # Continue searching in siblings (children of the parent)
    for sibling in getattr(node, 'children', []):
        find_all_nodes_children(sibling, path, result)
    
    return result

def find_parent_node(start_node, target_name):
    """Walk up the tree from the start_node searching for a node with the target_name and return that node."""
    current_node = start_node
    
    while current_node is not None:
        if current_node.name == target_name:
            return current_node
        current_node = current_node.parent  # Move up to the parent node

    return None  # Return None if the target node is not found

# Executor
def execute_order_66(root):
    s_funcao_principal(root) # Feita
    s_declaracao_de_funcao(root)

    s_variavel_nao_declarada(root)
    s_variavel_nao_inicializada(root) # Feita

# ---Funções e Procedimentos---

# checa se ha funcao principal
def s_funcao_principal(root):
    # Ensure the root node is "programa"
    if not check_node_exists(root if root.name == "programa" else None, 'ERR-SEM-MAIN-NOT-DECL'):
        return

    # Define the path for the function we're looking for
    path_to_main = [
        "lista_declaracoes", 
        "declaracao", 
        "declaracao_funcao", 
        "cabecalho", 
        "ID", 
        "principal"
    ]
    
    # Walk the tree based on the predefined path
    node_principal = walk_tree(root, path_to_main)

    # Check if we found the main function node ("principal")
    if not check_node_exists(node_principal, 'ERR-SEM-MAIN-NOT-DECL'):
        return

# checa se a funcao foi declarada antes de ser chamada
def s_declaracao_de_funcao(root):
    pass

# ---Variaveis---

# verifica se a variavel foi lida ou escrita sem ser declarada
def s_variavel_nao_declarada(root):
    pass

# verifica se a variavel foi declarada mas nao inicializada
def s_variavel_nao_inicializada(root):
    variable_path = [
        "declaracao_variaveis", 
        "lista_variaveis", 
        "var", 
        "ID"
    ]

    variables = find_all_nodes_children(root, variable_path)

    atribuicao_path = [
        "atribuicao",
        "var",
        "ID",
    ]

    for i in range(len(variables)):
        initialized = False
        pai = find_parent_node(variables[i], "cabecalho")
        if (pai == None):
            pai = root

        atribuicoes = find_all_nodes_children(pai, atribuicao_path)
        
        for j in range(len(atribuicoes)):
            if (atribuicoes[j].name == variables[i].name):
                initialized = True
                break

        if not initialized:
            errorArray.append(error_handler.newError(checkKey, 'WAR-SEM-VAR-DECL-NOT-INIT'))
        

# Programa Principal.
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
        root = tppparser_main(sys.argv)
        execute_order_66(root)

        # To visualize the tree:
        #for pre, fill, node in RenderTree(root):
        #    print(f"{pre}{node.name}")
    
    if len(errorArray) > 0:
        raise IOError(errorArray)

if __name__ == "__main__": 
    try:
        main()
    except Exception as e:
        print('\n--------------------------------------------- ERR-SEM ---------------------------------------------\n')
        for x in range(len(e.args[0])):
            print (e.args[0][x])
    except (ValueError, TypeError):
        print('\n-------------------------------------------------------------------------------------------\n')
        for x in range(len(e.args[0])):
            print (e.args[0][x])
