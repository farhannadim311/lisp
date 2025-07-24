"""
6.101 Lab:
LISP Interpreter Part 1
"""

#!/usr/bin/env python3

# import doctest # optional import
# import typing  # optional import
# import pprint  # optional import

import sys

sys.setrecursionlimit(20_000)

# NO ADDITIONAL IMPORTS!

#############################
# Scheme-related Exceptions #
#############################


class SchemeError(Exception):
    """
    A type of exception to be raised if there is an error with a Scheme
    program.  Should never be raised directly; rather, subclasses should be
    raised.
    """
    pass


class SchemeSyntaxError(SchemeError):
    """
    Exception to be raised when trying to evaluate a malformed expression.
    """
    pass


class SchemeNameError(SchemeError):
    """
    Exception to be raised when looking up a name that has not been defined.
    """
    pass


class SchemeEvaluationError(SchemeError):
    """
    Exception to be raised if there is an error during evaluation other than a
    SchemeNameError.
    """
    pass



############################
# Tokenization and Parsing #
############################


def number_or_symbol(value):
    """
    Helper function: given a string, convert it to an integer or a float if
    possible; otherwise, return the string itself

    >>> number_or_symbol('8')
    8
    >>> number_or_symbol('-5.32')
    -5.32
    >>> number_or_symbol('1.2.3.4')
    '1.2.3.4'
    >>> number_or_symbol('x')
    'x'
    """
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values). Returns a list of strings.

    Arguments:
        source (str): a string containing the source code of a Scheme expression
    """
    res = []
    temp = ""
    source_lines = source.splitlines()

    for line in source_lines:
        for char in line:
            if char == ";":
                break  # Ignore the rest of the line after a comment
            elif char.isspace():
                if temp:
                    res.append(temp)
                    temp = ""
            elif char == "(" or char == ")":
                if temp:
                    res.append(temp)
                    temp = ""
                res.append(char)
            else:
                temp += char
        if temp:
            res.append(temp)
            temp = ""

    return res



def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Arguments:
        tokens (list): a list of strings representing tokens
    """
    def parse_expression(index):
        token = tokens[index]

        # Base case: number or symbol
        if token not in ("(", ")"):
            return number_or_symbol(token), index + 1

        # Recursive case: S-expression
        if token == "(":
            subexpr = []
            index += 1  # move past '('

            while tokens[index] != ")":
                expr, index = parse_expression(index)
                subexpr.append(expr)

            return subexpr, index + 1  # skip past ')'

    parsed_expr, next_index = parse_expression(0)
    return parsed_expr


######################
# Built-in Functions #
######################

def calc_sub(*args):
    if len(args) == 1:
        return -args[0]

    first_num, *rest_nums = args
    return first_num - scheme_builtins['+'](*rest_nums)

def calc_mul(*args):
    if(len(args) == 1):
        return args[0]
    first_num, *rest_nums = args
    return first_num * scheme_builtins['*'](*rest_nums)

def cal_div(*args):
    if(len(args) == 1):
        return args[0]
    first_num, *rest_nums = args
    return first_num / scheme_builtins["*"](*rest_nums)
 
scheme_builtins = {
    "+": lambda *args: sum(args),
    "-": calc_sub,
    "*": calc_mul,
    "/": cal_div
}



##############
# Evaluation #
##############

def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)  # recursively yield items from sublist
        else:
            yield item

def evaluate(tree, frame=None):
    if frame is None:
        frame = make_initial_frame()

    # Case 1: Numeric literal
    if isinstance(tree, (int, float)):
        return tree

    if (isinstance(tree, list) and tree[0] == "lambda"):
        params = tree[1]
        body = tree[2]
        func = Function(params, body, frame)
        return func
    
    if (isinstance(tree, list) and tree[0] == "define" and isinstance(tree[1], list)):
        params = tree[1][1:]
        body = tree[2]
        func = Function(params, body, frame)
        frame.define(tree[1][0], func)
        return func
    # Case 2: Symbol
    if isinstance(tree, str):
        return frame.lookup(tree)

    # Case 3: Compound expression
    if isinstance(tree, list):
        if len(tree) == 0:
            raise SchemeEvaluationError()

        if tree[0] == "define":
            if len(tree) != 3:
                raise SchemeSyntaxError()
            name = tree[1]
            val = evaluate(tree[2], frame)
            frame.define(name, val)
            return val

        op = evaluate(tree[0], frame)  # allows operator to be a variable
        args = [evaluate(arg, frame) for arg in tree[1:]]
        try:
            return op(*args)
        except SchemeNameError:
            raise SchemeNameError()
        except SchemeEvaluationError:
            raise SchemeEvaluationError()
        except Exception:
            SchemeEvaluationError()

    raise SchemeEvaluationError()


def make_initial_frame():
    return Frames()

class ParentFrame():
    def __init__(self, parent = None):
        self.bindings = {
             "+": lambda *args: sum(args),
            "-": calc_sub,
            "*": calc_mul,
            "/": cal_div
        }
        self.parent = parent

    def define(self, name, value):
        if(not isinstance(name, str) or " " in name):
            raise SchemeNameError()
        self.bindings[name] = value
    
    def lookup(self, name):
        if name in self.bindings:
            return self.bindings[name]
        else:
            if(self.parent is not None):
                return self.parent.lookup(name)
            raise SchemeNameError()
            

class Frames():
    
    def __init__(self, parent = None):
        self.bindings = {}
        if parent is None:
            parent = ParentFrame()
        self.parent = parent
    
    def define(self, name, value):
        if(not isinstance(name, str) or " " in name):
            raise SchemeNameError()
        self.bindings[name] = value

    def lookup(self, name):
        if name in self.bindings:
            return self.bindings[name]
        else:
            if(self.parent is not None):
                return self.parent.lookup(name)
            raise SchemeNameError()

class Function:
    def __init__(self, params, body, defining_env):
        self.params = params          # list of parameter names (strings)
        self.body = body              # single Scheme expression (parsed tree)
        self.env = defining_env       # frame where the function was defined (for lexical scoping)

    def __call__(self, *args):
        if len(args) != len(self.params):
            raise SchemeEvaluationError()

        # Create a new frame for the function call, enclosing frame is the defining environment
        frame = Frames(self.env)
        
        # Bind parameters to arguments in the new frame
        for param, arg in zip(self.params, args):
            frame.define(param, arg)

        # Evaluate the function body in the new frame
        return evaluate(self.body, frame)


        
        
    

if __name__ == "__main__":
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)
    import os
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    import schemerepl
    schemerepl.SchemeREPL(sys.modules[__name__], use_frames=True, verbose=False).cmdloop()
