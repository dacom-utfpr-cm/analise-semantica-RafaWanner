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

def find_all_paths(node, path):
    temp_path = path[1:]
    result = []
    temp_result = None

    a = find_all_nodes(node, path[0])

    for i in range(len(a)):
        temp_result = walk_tree(a[i], temp_path)

        if (temp_result is not None):
            result.append(temp_result)

    return result

def find_all_paths_excludint_parent(node, path, parent):
    temp_path = path[1:]
    result = []
    temp_result = None

    a = find_all_nodes(node, path[0])

    for i in range(len(a)):
        if (find_parent_node(a[i], parent) is None):
            temp_result = walk_tree(a[i], temp_path)

            if (temp_result is not None):
                result.append(temp_result)

    return result

def find_all_nodes_children(node, path):
    temp_path = path[1:]
    result = []
    temp_result = None

    a = find_all_nodes(node, path[0])

    for i in range(len(a)):
        temp_result = walk_tree(a[i], temp_path)

        if (temp_result is not None):
            for child in getattr(temp_result, 'children', []):
                result.append(child)

    return result

def find_parent_node(start_node, target_name):
    """Walk up the tree from the start_node searching for a node with the target_name and return that node."""
    current_node = start_node
    
    while current_node is not None:
        if current_node.name == target_name:
            return current_node
        current_node = current_node.parent  # Move up to the parent node

    return None  # Return None if the target node is not found

def find_all_nodes_children_with_parent(node, path, parent):
    temp_path = path[1:]
    result = []
    temp_result = None

    a = find_all_nodes(node, path[0])

    for i in range(len(a)):
        temp_result = walk_tree(a[i], temp_path)

        if (temp_result is not None):
            if (find_parent_node(temp_result, parent) is not None):
                for child in getattr(temp_result, 'children', []):
                    result.append(child)

    return result

def get_string_after_last_underscore(s):
    match = re.search(r'_(?!.*_)(.*)', s)
    if match:
        return match.group(1)
    return s  # Return the whole string if no underscore is found

def comparator_type(node, type_coparasion, error_msg):
    call_var = node

    variable_path = [
        "declaracao_variaveis",
        "lista_variaveis",
        "var",
        "ID",
        call_var.name
    ]

    lista_parametros_path = [
        "lista_parametros",
        "parametro", 
        "id",
        call_var.name
    ]

    pai = find_parent_node(call_var, "cabecalho")
    variable = None
    variable_type = None

    if (find_all_paths(pai, variable_path)):
        """Variable Declared On Function"""
        variable = find_all_paths(pai, variable_path)

        variable_type = find_parent_node(variable[0], "declaracao_variaveis").children[0].children[0].name

    elif (find_all_paths(pai, lista_parametros_path)):
        """Variable Declared On Function Parameters"""
        variable = find_all_paths(pai, lista_parametros_path)
        
        variable_type = find_parent_node(variable[0], "parametro").children[0].children[0].name

    elif (find_all_paths_excludint_parent(root, variable_path, "cabecalho")):
        """Variable Declared Globaly"""
        variable = find_all_paths_excludint_parent(root, variable_path, "cabecalho")

        variable_type = find_parent_node(variable[0], "declaracao_variaveis").children[0].children[0].name

    else:
        """Variable Not Declared Treat As Null"""

    if (variable_type != type_coparasion):
            errorArray.append(error_handler.newError(checkKey, error_msg))



# Executor
def execute_order_66(root):
    s_funcao_principal(root) # Feita
    s_declaracao_de_funcao(root) # Feita
    s_retorno_de_funcao(root) # Feita

    s_variavel_nao_declarada(root)
    s_variavel_declarada_inicializada_utilizada(root) # Feita



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
    function_path = [
        "chamada_funcao",
        "ID"
    ]

    cabecalho_path = [
        "declaracao",
        "declaracao_funcao",
        "cabecalho",
        "ID"
    ]

    function_calls = find_all_nodes_children(root, function_path)

    for function_call in function_calls:
        function_is_declared = False
        function_node = find_parent_node(function_call, "lista_declaracoes")
        
        while function_node:
            function_check = walk_tree(function_node, cabecalho_path)

            if function_check and function_check.children[0].name == function_call.name:
                function_is_declared = True
                s_identificador_de_funcao(function_check.children[0], function_call)
                break
            else:
                function_node = walk_tree(function_node, ["lista_declaracoes"])
        
        if not function_is_declared:
            errorArray.append(error_handler.newError(checkKey, 'ERR-SEM-CALL-FUNC-NOT-DECL'))

# checa se a quantidade de parametros reais e formais de uma funcao sao iguais
def s_identificador_de_funcao(node_formal, node_real):
    parameters_path = [
        "lista_parametros",
        "parametro"
    ]

    argumentos_path = [
        "lista_argumentos",
        "expressao"
    ]

    formal_length = find_all_paths(node_formal.parent.parent, parameters_path)
    real_length = find_all_paths(node_real.parent.parent, argumentos_path)

    if (len(real_length) > len(formal_length)):
        errorArray.append(error_handler.newError(checkKey, 'ERR-SEM-CALL-FUNC-WITH-MANY-ARGS'))

    elif (len(real_length) < len(formal_length)):
        errorArray.append(error_handler.newError(checkKey, 'ERR-SEM-CALL-FUNC-WITH-FEW-ARGS'))

    else:
        s_verifica_tipagem_chamada_de_funcao(formal_length, real_length)

# checa se a funcao foi retornada corretamente
def s_retorno_de_funcao(root):
    retorno_path = [
        "cabecalho",
        "corpo",
        "acao",
        "retorna",
        "expressao", 
        "expressao_logica",
        "expressao_simples",
        "expressao_aditiva",
        "expressao_multiplicativa",
        "expressao_unaria",
        "fator"
    ]

    dec_func = find_all_nodes(root, "declaracao_funcao")
    retorno_var = None

    for i in range(len(dec_func)):
        retorno = walk_tree(dec_func[i], retorno_path)
        function_type = dec_func[i].children[0].children[0].name

        if (retorno is not None):
            # checa se o retorno e uma variavel
            retorno_check = walk_tree(retorno, ["var"])

            if (retorno_check is not None):
                retorno_var = retorno_check.children[0].children[0]
                comparator_type(retorno_var, function_type, 'ERR-SEM-FUNC-RET-TYPE-ERROR')

        else:
            errorArray.append(error_handler.newError(checkKey, 'ERR-SEM-FUNC-RET-TYPE-ERROR'))



# ---Variaveis---

# verifica se a variavel foi lida ou escrita sem ser declarada
def s_variavel_nao_declarada(root):
    pass

# verifica se a variavel foi declarada, utilizada e inicializada
def s_variavel_declarada_inicializada_utilizada(root):
    variable_path = [
        "declaracao_variaveis", 
        "lista_variaveis", 
        "var", 
        "ID"
    ]

    variables = find_all_nodes_children(root, variable_path)

    for i in range(len(variables)):
        pai = find_parent_node(variables[i], "cabecalho")
        if (pai == None):
            pai = root

        atribuicao_path = [
            "atribuicao",
            "var",
            "ID",
            variables[i].name
        ]

        expression_path = [
            "expressao", 
            "expressao_logica",
            "expressao_simples",
            "expressao_aditiva",
            "expressao_multiplicativa",
            "expressao_unaria",
            "fator",
            "var",
            "ID",
            variables[i].name
        ]

        atribuicoes = find_all_paths(pai, atribuicao_path)
        expresions = find_all_paths(pai, expression_path)

        print(variables[i].name)
        print(atribuicoes)
        print(expresions)

        if (len(variables[i].parent.parent.children) > 1):
            if (variables[i].parent.parent.children[1].name == "indice"):
                s_indice_nao_inteiro(variables[i].parent.parent.children[1])
                return
            else:
                pass
                
        elif (atribuicoes):
            for j in range(len(atribuicoes)):
                if (len(atribuicoes[j].parent.parent.children) > 1):
                    if (atribuicoes[j].parent.parent.children[1].name == "indice"):
                        s_indice_nao_inteiro(atribuicoes[j].parent.parent.children[1])
                        return
                else:
                    pass

        elif (expresions):
            for k in range(len(expresions)):
                if (len(expresions[k].parent.parent.children) > 1):
                    if (expresions[k].parent.parent.children[1].name == "indice"):
                        s_indice_nao_inteiro(expresions[k].parent.parent.children[1])
                        return
                else:
                    pass



        # verifica se a variavel foi inicializada e ou utilizada
        if not atribuicoes:
            if not expresions:
                errorArray.append(error_handler.newError(checkKey, 'WAR-SEM-VAR-DECL-NOT-USED'))

            else:
                errorArray.append(error_handler.newError(checkKey, 'WAR-SEM-VAR-DECL-NOT-INIT'))

        elif not expresions:
            errorArray.append(error_handler.newError(checkKey, 'WAR-SEM-VAR-DECL-INIT-NOT-USED'))



# ---Atribuição de tipos distintos e Coerções implícitas---

# verifica se a inicializacao e uso da variavel corresponde a tipagem
def s_verifica_tipagem_inicializacao_variavel(node_var_receive, node_var_gives):
    pass

# verifica se a tipagem dos parametros formais e reais sao iguais
def s_verifica_tipagem_chamada_de_funcao(nodes_formal, nodes_real):
    parameter_real_path = [
        "expressao_logica",
        "expressao_simples",
        "expressao_aditiva",
        "expressao_multiplicativa",
        "expressao_unaria",
        "fator"
    ]

    for i in range(len(nodes_formal)):
        parameter_real = find_all_nodes_children(nodes_real[i], parameter_real_path)
        formal_type = nodes_formal[i].children[0].children[0].name

        if (parameter_real[0].name != "var"):
            real_type = get_string_after_last_underscore(parameter_real[0].children[0].name)

            if (real_type != formal_type):
                errorArray.append(error_handler.newError(checkKey, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-FUNC-ARG'))

        else:
            call_var = parameter_real[0].children[0].children[0]
            comparator_type(call_var, formal_type, 'WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-FUNC-ARG')



# ---Aranjos---

# verifica se o indice do array e um inteiro
def s_indice_nao_inteiro(root):
    indice_path = [
        "indice", 
        "expressao", 
        "expressao_logica", 
        "expressao_simples",
        "expressao_aditiva",
        "expressao_multiplicativa",
        "expressao_unaria",
        "fator",
        "numero"
    ]

    indice = find_all_nodes_children(root, indice_path)

    for i in range(len(indice)):
        if (indice[i].name) != "NUM_INTEIRO":
            errorArray.append(error_handler.newError(checkKey, 'ERR-SEM-ARRAY-INDEX-NOT-INT'))



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