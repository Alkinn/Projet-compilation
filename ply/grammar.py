import ply.yacc as yacc
import lexer
import sys
import struct

tokens = lexer.tokens
start = 'program'

def callorder():
    if not hasattr(callorder, 'counter'):
        callorder.counter = 0
    s = str(callorder.counter)
    callorder.counter += 1
    return s

def newvar():
    # Fonction servant a generer un nouveau registre de la forme %xi, i etant incremente a chaque fois
    if not hasattr(newvar, 'counter'):
        newvar.counter = 0
    s = "%x" + str(newvar.counter)
    newvar.counter += 1
    return s

def newlabel():
    # Meme chose que pour les registres, mais pour les labels
    if not hasattr(newlabel, 'counter'):
        newlabel.counter = 0
    s = "label" + str(newlabel.counter)
    newlabel.counter += 1
    return s

# Equivalent du enum pour les types
class Type          :pass
class INT       (Type):pass
class FLOAT     (Type):pass
class VOID      (Type):pass
class ARRAY     (Type):pass
class ARRAYINT  (Type):pass
class ARRAYFLOAT(Type):pass

# Initialisation de la variable globale pour connaitre le type de l'identifiant suivant
basetype = Type()

# Dictionnaire (equivalent de la hashtable)
# Marche par cle, exemple : vars = {'x' : %x3} : le dictionnaire une entree, dont la cle est 'x' (nom de la variable en C) et la valeur est %x3 (le nom du registre ou est stocke la variable)
# Pour y acceder, on tape vars['x']
vars = {}

def truncFloat(value):
    """
    Truncate to single-precision float.
    """
    return struct.unpack('f', struct.pack('f', value))[0]

def hexFloat(value, packfmt, unpackfmt, numdigits):
    raw = struct.pack(packfmt, float(value))
    intrep = struct.unpack(unpackfmt, raw)[0]
    out = '{{0:#{0}x}}'.format(numdigits).format(intrep)
    return out

def hexDouble(value):
    """
    Format *value* as a hexadecimal string of its IEEE double precision
    representation.
    """
    return hexFloat(value, 'd', 'Q', 16)

def sitofp(reg):
    # Fonction pour ecrire le code pour convertir un int en float (marche a peu pres, pas beaucoup teste)
    newReg = newvar()
    code = newReg + " = sitofp i32 " + reg +" to float\n"
    return [code, newReg]

def fptosi(reg):
    # Fonction pour ecrire le code pour convertir un int en float (marche a peu pres, pas beaucoup teste)
    newReg = newvar()
    code = newReg + " = fptosi float " + reg +" to i32\n"
    return [code, newReg]


# On utilise aussi des dictionnaires pour chaque regle. p[0] = {} initialise p[0] en un dictionnaire, et le minimum est d'y mettre un code :
# p[0]['code'] = "machin truc"
# Pour les variables, on a les cles 'code', 'reg' qui enregistre le registre ou est stocke la variable, et 'type'.
# Dans la premiere regle en dessous il y a l'entree 'name', je sais plus exactement pourquoi mais c'est pour enregistrer le nom du registre d'origine (je crois, je reviendrai dessus plus tard).
# -------------- RULES ----------------

########################### primary_expression ###########################
def p_primary_expression_1(p):
    '''primary_expression : IDENTIFIER'''
    p[0] = {}
    p[0]['reg'] = newvar()
    p_id = vars[p[1]]
    p[0]['idReg'] = p_id['reg']
    if (p_id['type'] == INT):
        p[0]['type'] = INT
        p[0]['code'] = p[0]['reg'] + " = load i32* " + p_id['reg'] + "\n"
    elif (p_id['type'] == FLOAT):
        p[0]['type'] = FLOAT
        p[0]['code'] = p[0]['reg'] + " = load float* " + p_id['reg'] + "\n"
    elif (p_id['type'] == ARRAYINT):
        tmp = newvar()
        p[0]['type'] = ARRAYINT
        p[0]['size'] = p_id['size']
        p[0]['code'] = tmp + " = getelementptr inbounds [" +p_id['size']+ " x i32]* " +p_id['reg'] +", i64 0, i32 0\n" ##get pointer
        p[0]['code'] = p[0]['code'] + p[0]['reg'] + " = load i32 " + tmp +"\n"  ##dereference pointer
    elif (p_id['type'] == ARRAYFLOAT):
        tmp = newvar()
        p[0]['size'] = p_id['size']
        p[0]['type'] = ARRAYFLOAT
        p[0]['code'] = tmp + " = getelementptr inbounds [" +p_id['size']+ " x float]* " +p_id['reg'] +", i64 0, float 0\n" ##get pointer
        p[0]['code'] = p[0]['code'] + p[0]['reg'] + " = load float* " + tmp +"\n"
    else:
        p_error("Undefined type : not int float ARRAYINT or ARRAYFLOAT")
    tmp = callorder()
    sys.stdout.write(tmp+"  prim_exp => IDENTIFIER \n")

def p_primary_expression_2(p):
    '''primary_expression : CONSTANTI'''
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['type'] = INT
    p[0]['code'] = p[0]['reg'] + " = add i32 0, " + p[1] + "\n"
    p[0]['val'] = p[1]

def p_primary_expression_3(p):
    '''primary_expression : CONSTANTF'''
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['type'] = FLOAT
    floatCF = hexDouble(truncFloat(float(p[1])))
    p[0]['code'] = p[0]['reg'] + " = fadd float 0.0, " + floatCF + "\n"
    p[0]['val'] = p[1]

def p_primary_expression_4(p):
    '''primary_expression : '(' expression ')' '''
    p[0] = p[2]

def p_primary_expression_5(p):
    '''primary_expression : MAP '(' postfix_expression ',' postfix_expression ')' '''
    p[0] = {'type': INT}

def p_primary_expression_6(p):
    '''primary_expression : REDUCE '(' postfix_expression ',' postfix_expression ')' '''
    p[0] = {'type': INT}

def p_primary_expression_7(p):
    '''primary_expression : IDENTIFIER '(' ')' '''
    p[0] = {'type': INT}

def p_primary_expression_8(p):
    '''primary_expression : IDENTIFIER '(' argument_expression_list ')' '''
    p[0] = {'type': INT}

def p_primary_expression_9(p):
    '''primary_expression : IDENTIFIER INC_OP'''
    p[0] = {'type': INT}

def p_primary_expression_10(p):
    '''primary_expression : IDENTIFIER DEC_OP'''
    p[0] = {'type': INT}

########################### postfix_expression ###########################
def p_postfix_expression_1(p):
    '''postfix_expression : primary_expression'''
    p[0] = p[1]

def p_postfix_expression_2(p):
    '''postfix_expression : postfix_expression '[' expression ']' '''
    p[0] = {} 
    p[0]['reg'] = newvar();
    p[0]['idReg'] = p[0]['reg']
    if (p[1]['type'] == ARRAYINT):
        if ((p[3]['type'] == INT) and (p[3]['val'] >= 0)):
            p[0]['code'] = p[3]['code'] + p[0]['reg'] +" = getelementptr inbounds [" + p[1]['size'] + " x i32]* " + p[1]['idReg'] +", i64 0, i32 "+ p[3]['reg'] +"\n"
            p[0]['type'] = INT
        else:
            p_error("Error at line " + str(p.lineno)+" : array index should be POSITIVE INT")
    elif (p[1]['type'] == ARRAYFLOAT):
        sys.stdout.write("checkpoing : ARRAYFLOAT")        
        if ((p[3]['type'] == INT) and p[3]['val'] >= 0):
            p[0]['code'] = p[0]['reg'] +" = getelementptr inbounds [" + p[1]['size'] + " x float]* " + p[1]['idReg'] +", i64 0, float "+ p[3]['val']+"\n"
            p[0]['type'] = FLOAT
        else:
            p_error("TypeError at line " + str(p.lineno) + " : array index should be POSITIVE INT")
    else:
        p_error("TypeError at line " + str(p.lineno)+ " : expected ARRAYINT or ARRAYFLOAT got"+ str(p[1]['type']) + "instead")

########################### argument_expression_list ###########################
def p_argument_expression_list_1(p):
    '''argument_expression_list : expression'''
    p[0] = p[1]

def p_argument_expression_list_2(p):
    '''argument_expression_list : argument_expression_list ',' expression'''

########################### unary_expression ###########################
def p_unary_expression_1(p):
    '''unary_expression : postfix_expression'''
    p[0] = p[1]

def p_unary_expression_2(p):
    '''unary_expression : INC_OP unary_expression'''
    p[0] = p[2]

def p_unary_expression_3(p):
    '''unary_expression : DEC_OP unary_expression'''
    p[0] = p[2]

def p_unary_expression_4(p):
    '''unary_expression : unary_operator unary_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    if (p[2]['type'] == INT):
        p[0]['type'] = INT
        p[0]['code'] = p[2]['code'] + " " + p[0]['reg'] + " = sub i32 0, " + p[2]['reg'] + "\n"
    elif (p[2]['type'] == FLOAT):
        p[0]['type'] = FLOAT
        p[0]['code'] = p[2]['code'] + " " + p[0]['reg'] + " = fsub float 0.0, " + p[2]['reg'] + "\n"    

########################### unary_operator ###########################
def p_unary_operator_1(p):
    '''unary_operator : '-' '''

########################### multiplicative_expression ###########################
def p_multiplicative_expression_1(p):
    '''multiplicative_expression : unary_expression'''
    p[0] = p[1]


def p_multiplicative_expression_2(p):
    '''multiplicative_expression : multiplicative_expression '*' unary_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['type'] = INT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = mul i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['type'] = FLOAT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fmul float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == INT and p[3]['type'] == FLOAT):
        p[0]['type'] = FLOAT
        p1 = sitofp(p[1]['reg'])
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p1[0] + p[0]['reg'] + " = fmul float " + p1[1] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

def p_multiplicative_expression_3(p):
    '''multiplicative_expression : multiplicative_expression '/' unary_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['type'] = INT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = sdiv i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['type'] = FLOAT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fdiv float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

def p_multiplicative_expression_4(p):
    '''multiplicative_expression : multiplicative_expression '%' unary_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['type'] = INT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = srem i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['type'] = FLOAT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = frem float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

########################### additive_expression ###########################
def p_additive_expression_1(p):
    '''additive_expression : multiplicative_expression'''
    p[0] = p[1]

def p_additive_expression_2(p):
    '''additive_expression : additive_expression '+' multiplicative_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['type'] = INT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = add i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['type'] = FLOAT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fadd float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

def p_additive_expression_3(p):
    '''additive_expression : additive_expression '-' multiplicative_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['type'] = INT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = sub i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['type'] = FLOAT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fsub float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

########################### comparison_expression ###########################
def p_comparison_expression_1(p):
    '''comparison_expression : additive_expression'''
    p[0] = p[1]

def p_comparison_expression_2(p):
    '''comparison_expression : additive_expression '<' additive_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['type'] = INT
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = icmp slt i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fcmp olt float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

def p_comparison_expression_3(p):
    '''comparison_expression : additive_expression '>' additive_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['type'] = INT
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = icmp sgt i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fcmp ogt float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

def p_comparison_expression_4(p):
    '''comparison_expression : additive_expression LE_OP additive_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['type'] = INT
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = icmp use i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fcmp ole float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

def p_comparison_expression_5(p):
    '''comparison_expression : additive_expression GE_OP additive_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['type'] = INT
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = icmp sge i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fcmp oge float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

def p_comparison_expression_6(p):
    '''comparison_expression : additive_expression EQ_OP additive_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['type'] = INT
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = icmp eq i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fcmp oeq float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

def p_comparison_expression_7(p):
    '''comparison_expression : additive_expression NE_OP additive_expression'''
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['type'] = INT
    if (p[1]['type'] == INT and p[3]['type'] == INT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = icmp ne i32 " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    elif (p[1]['type'] == FLOAT and p[3]['type'] == FLOAT):
        p[0]['code'] = p[1]['code'] + p[3]['code'] + p[0]['reg'] + " = fcmp one float " + p[1]['reg'] + ", " + p[3]['reg'] + "\n"
    else:
        p_error("Not yet valid operation between float and int =P")

########################### expression ###########################
def p_expression_1(p):
    '''expression : unary_expression assignment_operator comparison_expression'''
    p[0] = {}
    p[0]['reg'] = p[1]['reg']
    if ((p[1]['type'] == INT) and (p[3]['type'] == INT)) :
        p[0]['type'] = INT
        p[0]['code'] = p[1]['code'] + p[3]['code'] + "store i32 " + p[3]['reg'] + ", i32* " + p[1]['idReg'] + "\n"
    elif (p[1]['type'] == FLOAT):
        if (p[3]['type'] == FLOAT):
            p[0]['type'] = FLOAT
            p[0]['code'] = p[1]['code'] + p[3]['code'] + "store float " + p[3]['reg'] + ", float* " + p[1]['idReg'] + "\n"
        elif (p[3]['type'] == INT):
            tmp = sitofp(p[3]['reg'])
            p[0]['code'] = p[1]['code'] + p[3]['code']+ tmp[0] + "store float " + tmp[1] + ", float* " + p[1]['idReg'] + "\n"
    # p[0] = {}
    # p[0]['reg'] = p[1]['reg']
    # if p[3]['type'] == INT:
    #     p[0]['type'] = INT
    #     p[0]['code'] = p[1]['code'] + p[3]['code'] + "store i32 " + p[3]['reg'] + ", i32* " + p[1]['idReg'] +"\n"
    #     #p[0]['code'] = p[3]['code'] + "store i32 " + p[3]['reg'] + ", i32* " + p[1]['idReg'] + "\n" + p[1]['code'] +"\n"
    # elif p[3]['type'] == FLOAT:
    #     p[0]['type'] = FLOAT
    #     if (p[1]['type'] == INT):
    #         newReg = newvar()
    #         p1 = sitofp(p[1]['reg'])
    #         p[0]['code'] = p[3]['code'] + p1[0] + "store float " + p[3]['reg'] + ", float* " + p1[1] + "\n" + newReg + "= load float* " + p1[1] + "\n"
    #     else:
    #         p[0]['code'] = p[3]['code'] + "store float " + p[3]['reg'] + ", float* " + p[1]['idReg'] + "\n" + p[1]['code']

def p_expression_2(p):
    '''expression : comparison_expression'''
    p[0] = p[1]

########################### assignment_operator ###########################
def p_assignment_operator_1(p):
    '''assignment_operator : '=' '''

def p_assignment_operator_2(p):
    '''assignment_operator : MUL_ASSIGN'''

def p_assignment_operator_3(p):
    '''assignment_operator : ADD_ASSIGN'''

def p_assignment_operator_4(p):
    '''assignment_operator : SUB_ASSIGN'''

########################### declaration ###########################
def p_declaration_1(p):
    '''declaration : type_name declarator_list ';' '''
    p[0] = p[2]

def p_declaration_2(p):
    '''declaration : EXTERN type_name declarator_list ';' '''

########################### declarator_list ###########################
def p_declarator_list_1(p):
    '''declarator_list : declarator'''
    p[0] = p[1]

def p_declarator_list_2(p):
    '''declarator_list : declarator_list ',' declarator'''
    p[0] = {}
    p[0]['code'] = p[1]['code'] + p[3]['code']

########################### type_name ###########################
def p_type_name_1(p):
    '''type_name : VOID'''
    global basetype
    basetype = VOID
    p[0] = {}
    p[0]['type'] = VOID

def p_type_name_2(p):
    '''type_name : INT'''
    global basetype
    basetype = INT
    p[0] = {}
    p[0]['type'] = INT

def p_type_name_3(p):
    '''type_name : FLOAT'''
    global basetype
    basetype = FLOAT
    p[0] = {}
    p[0]['type'] = FLOAT

########################### declarator ###########################
def p_declarator_1(p):
    '''declarator : IDENTIFIER'''
    global basetype
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['type'] = basetype
    p[0]['name'] = p[1]
    if (basetype == INT):
        p[0]['code'] = p[0]['reg']+" = alloca i32\n"
    else:
        p[0]['code'] = p[0]['reg']+" = alloca float\n"

    vars[p[1]] = p[0]

def p_declarator_2(p):
    '''declarator : '(' declarator ')' '''
    p[0] = p[2]

def p_declarator_3(p):
    '''declarator : declarator '[' CONSTANTI ']' '''
    p[0] = {}
    p[0]['reg'] = newvar()
    p[0]['size'] = p[3]
    if (p[1]['type'] == INT):
        p[0]['code'] = p[0]['reg']+" = alloca ["+ p[3] +" x i32]\n"
        p[0]['type'] = ARRAYINT
    elif (p[1]['type'] == FLOAT):
        p[0]['code'] = p[0]['reg']+" = alloca ["+ p[3] +" x float]\n"
        p[0]['type'] = ARRAYFLOAT

    vars[p[1]['name']] = p[0]

def p_declarator_4(p):
    '''declarator : declarator '[' ']' '''

def p_declarator_5(p):
    '''declarator : declarator '(' parameter_list ')' '''

def p_declarator_6(p):
    '''declarator : declarator '(' ')' '''
    p[0] = p[1]

########################### parameter_list ###########################
def p_parameter_list_1(p):
    '''parameter_list : parameter_declaration'''

def p_parameter_list_2(p):
    '''parameter_list : parameter_list ',' parameter_declaration'''

########################### parameter_declaration ###########################
def p_parameter_declaration_1(p):
    '''parameter_declaration : type_name declarator'''

########################### statement ###########################
def p_statement_1(p):
    '''statement : compound_statement'''
    p[0] = p[1]

def p_statement_2(p):
    '''statement : expression_statement'''
    p[0] = p[1]

def p_statement_3(p):
    '''statement : selection_statement'''
    p[0] = p[1]

def p_statement_4(p):
    '''statement : iteration_statement'''
    p[0] = p[1]

def p_statement_5(p):
    '''statement : jump_statement'''
    p[0] = p[1]

########################### compound_statement ###########################
def p_compound_statement_1(p):
    '''compound_statement : '{' '}' '''
    p[0] = {}
    #p[0]['code'] = "{\n\n}"

def p_compound_statement_2(p):
    '''compound_statement : '{' statement_list '}' '''
    p[0] = p[2]
    #p[0]['code'] = "{\n" + p[2]['code'] + "\n}"

def p_compound_statement_3(p):
    '''compound_statement : '{' declaration_list statement_list '}' '''
    p[0] = {}
    p[0]['code'] = p[2]['code'] + p[3]['code']
    #p[0]['code'] = "{\n" + p[2]['code'] + p[3]['code'] + "\n}"


########################### declaration_list ###########################
def p_declaration_list_1(p):
    '''declaration_list : declaration'''
    p[0] = p[1]

def p_declaration_list_2(p):
    '''declaration_list : declaration_list declaration'''
    p[0] = {}
    p[0]['code'] = p[1]['code'] + p[2]['code']

########################### statement_list ###########################
def p_statement_list_1(p):
    '''statement_list : statement'''
    p[0] = p[1]

def p_statement_list_2(p):
    '''statement_list : statement_list statement'''
    p[0] = {}
    p[0]['code'] = p[1]['code'] + p[2]['code']

########################### expression_statement ###########################
def p_expression_statement_1(p):
    '''expression_statement : ';' '''
    p[0] = {}
    p[0]['code'] = "\n"

def p_expression_statement_2(p):
    '''expression_statement : expression ';' '''
    p[0] = p[1]

########################### selection_statement ###########################
def p_selection_statement_1(p):
    '''selection_statement : IF '(' expression ')' statement'''
    p[0] = {}
    trueLabel = newlabel()
    endLabel = newlabel()
    p[0]['code'] = p[3]['code'] + "br i1 " + p[3]['reg'] + ", label %" + trueLabel + ", label %" + endLabel + "\n" + trueLabel + ":\n" + p[5]['code'] + "br label %" + endLabel + "\n" + endLabel + ":\n"

def p_selection_statement_2(p):
    '''selection_statement : IF '(' expression ')' statement ELSE statement'''
    p[0] = {}
    trueLabel = newlabel()
    falseLabel = newlabel()
    endLabel = newlabel()
    p[0]['code'] = p[3]['code'] + "br i1 " + p[3]['reg'] + ", label %" + trueLabel + ", label %" + falseLabel + "\n" + trueLabel + ":\n" + p[5]['code'] + "br label %" + endLabel + "\n" + falseLabel + ":\n" + p[7]['code'] + "br label %" + endLabel + "\n" + endLabel + ":\n"

def p_selection_statement_3(p):
    '''selection_statement : FOR '(' expression_statement expression_statement expression ')' statement'''
    p[0] = {}
    entryLabel = newlabel()
    loopLabel = newlabel()
    endLabel = newlabel()

    # TODO : VERIFICATION SUR LES TYPES DES EXPRESSIONS
    if (p[3]['code'] != "\n" and p[4]['code'] != "\n"):

        i = newvar()
        nextvar = p[3]['reg']

        # Phi node
        phiNode = i + " = phi i32 [" + p[3]['reg'] + ", %" + entryLabel + " ], [ " + nextvar + ", %" + loopLabel + " ]" + "\n"

        # Incrementation
        incCode = p[5]['code']
        #incCode = nextvar + " = add i32 " + i +", " + p[5]['reg'] + "\n"

        # Corps de la boucle
        loopBody = p[7]['code']

        # Terminaison de la boucle
        terminationCode = p[4]['code'] + "br i1 " + p[4]['reg'] + ", label %" + loopLabel + ", label %" + endLabel + "\n" 
        print p[5]


    p[0]['code'] =p[3]['code'] + "br label %"+ entryLabel + "\n" + entryLabel + ":\nbr label %" + loopLabel + "\n" + loopLabel +":\n" + phiNode + loopBody + incCode + terminationCode + endLabel + ":\n"

########################### iteration_statement ###########################
def p_iteration_statement_1(p):
    '''iteration_statement : WHILE '(' expression ')' statement'''

def p_iteration_statement_2(p):
    '''iteration_statement : DO statement WHILE '(' expression ')' ';' '''

########################### jump_statement ###########################
def p_jump_statement_1(p):
    '''jump_statement : RETURN ';' '''
    p[0] = {}
    p[0]['code'] = "ret i1 0"

def p_jump_statement_2(p):
    '''jump_statement : RETURN expression ';' '''
    p[0] = {}
    if (p[2]['type'] == INT):
        p[0]['code'] = p[2]['code'] + "ret i32 " + p[2]['reg']


########################### program ###########################
def p_program_1(p):
    '''program : external_declaration'''
    p[0] = p[1]

def p_program_2(p):
    '''program : program external_declaration'''
    p[0] = {}
    p[0]['code'] = p[1]['code'] + p[2]['code']

########################### external_declaration ###########################
def p_external_declaration_1(p):
    '''external_declaration : function_definition'''
    p[0] = p[1]

def p_external_declaration_2(p):
    '''external_declaration : declaration'''
    p[0] = p[1]

########################### function_definition ###########################
def p_function_definition_1(p):
    '''function_definition : type_name declarator compound_statement'''
    p[0] = {}
    if p[1]['type'] == INT:
        p[0]['type'] = p[1]['type']
        p[0]['code'] = "define i32 @" + p[2]['name'] + "() {\n" + p[3]['code'] + "\n}"
    print p[0]['code']

def p_error(p):
    print "Error line " + str(p.lineno) + ":" + str(p)

if __name__ == '__main__':
    parser = yacc.yacc()
    if len(sys.argv) > 1 :
        filename = sys.argv[1]
        with open(filename, 'r') as f:
            parser.parse(f.read())
    else :
        print("Usage: ./{0} <file.c>".format(sys.argv[0]))
