"""
6.101 Lab — Lisp Interpreter (Part 1, Python 3.9 safe)
"""
#!/usr/bin/env python3
# NO ADDITIONAL IMPORTS!
import sys, os
sys.setrecursionlimit(20_000)

################ Exceptions ################
class SchemeError(Exception):            pass
class SchemeSyntaxError(SchemeError):    pass
class SchemeNameError(SchemeError):      pass
class SchemeEvaluationError(SchemeError):pass

############ Tokenize & Parse #############
def number_or_symbol(tok):
    if tok == "#t": return True
    if tok == "#f": return False
    try:   return int(tok)
    except ValueError:
        try: return float(tok)
        except ValueError:
            return tok

def tokenize(src:str):
    out, buf = [], ""
    for line in src.splitlines():
        for ch in line:
            if ch == ";": break               # comment
            if ch.isspace():
                if buf: out.append(buf); buf = ""
            elif ch in "()":
                if buf: out.append(buf); buf = ""
                out.append(ch)
            else: buf += ch
        if buf: out.append(buf); buf = ""
    return out

def parse(toks):
    if not toks: raise SchemeSyntaxError()
    def read(i):
        if i >= len(toks): raise SchemeSyntaxError()
        tk = toks[i]
        if tk == ")": raise SchemeSyntaxError()
        if tk != "(": return number_or_symbol(tk), i+1
        lst, i = [], i+1
        while True:
            if i >= len(toks): raise SchemeSyntaxError()
            if toks[i] == ")": return lst, i+1
            expr, i = read(i)
            lst.append(expr)
    tree, nxt = read(0)
    if nxt != len(toks): raise SchemeSyntaxError()
    return tree

########### Pair / EMPTY (proper lists) ###########
class Pair:
    def __init__(self, car, cdr): self.car, self.cdr = car, cdr
    def __repr__(self): return f"(cons {self.car} {self.cdr})"

class EmptyList:
    def __repr__(self): return "()"
    def __eq__(self, o): return isinstance(o, EmptyList)
EMPTY = EmptyList()

def cons_builtin(a,b): return Pair(a,b)
def car_builtin(p):
    if not isinstance(p,Pair): raise SchemeEvaluationError()
    return p.car
def cdr_builtin(p):
    if not isinstance(p,Pair): raise SchemeEvaluationError()
    return p.cdr

def list_builtin(*elems):
    lst=EMPTY
    for v in reversed(elems): lst = Pair(v,lst)
    return lst

def is_list(obj):
    while isinstance(obj,Pair): obj=obj.cdr
    return obj == EMPTY

def length_builtin(lst):
    n,cur=0,lst
    while isinstance(cur,Pair): n,cur = n+1,cur.cdr
    if cur!=EMPTY: raise SchemeEvaluationError()
    return n

def list_ref_builtin(lst, idx):
    if not(isinstance(idx,int) and idx>=0): raise SchemeEvaluationError()
    cur=lst
    while isinstance(cur,Pair):
        if idx==0: return cur.car
        idx,cur = idx-1,cur.cdr
    raise SchemeEvaluationError()

def append_builtin(*lists):
    if not lists: return EMPTY
    for L in lists:
        if L is not EMPTY and not isinstance(L,Pair):
            raise SchemeEvaluationError()
    for L in lists[:-1]:
        if not is_list(L): raise SchemeEvaluationError()

    # single-list copy
    if len(lists)==1:
        src,head,tail = lists[0], None, None
        cur=src
        while isinstance(cur,Pair):
            node=Pair(cur.car,EMPTY)
            if head is None:
                head=node
            else:
                tail.cdr=node
            tail=node
            cur=cur.cdr
        return head if head else EMPTY

    # ≥2 lists
    head=tail=None
    for src in lists[:-1]:
        cur=src
        while isinstance(cur,Pair):
            node=Pair(cur.car,EMPTY)
            if head is None: head=node
            else:            tail.cdr=node
            tail=node
            cur=cur.cdr
    if head is None:
        return lists[-1]
    tail.cdr = lists[-1]
    return head

############ Arithmetic / Bool ############
def calc_sub(*a): return -a[0] if len(a)==1 else a[0]-sum(a[1:])
def calc_mul(*a):
    r=1
    for v in a: r*=v
    return r
def calc_div(*a):
    r=a[0]
    for v in a[1:]: r/=v
    return r
def need2(a): len(a)>=2 or (_ for _ in ()).throw(SchemeEvaluationError())
def cmp(fn): return lambda *a: (need2(a) or all(fn(x,y) for x,y in zip(a,a[1:])))

########### Built-ins Table ###########
scheme_builtins={
    "+":lambda *a:sum(a), "-":calc_sub,"*":calc_mul,"/":calc_div,
    "equal?":cmp(lambda x,y:x==y), ">":cmp(lambda x,y:x>y),
    ">=":cmp(lambda x,y:x>=y), "<":cmp(lambda x,y:x<y),
    "<=":cmp(lambda x,y:x<=y), "not":lambda x:not x,
    "cons":cons_builtin,"car":car_builtin,"cdr":cdr_builtin,
    "list":list_builtin,"list?":is_list,
    "length":length_builtin,"list-ref":list_ref_builtin,
    "append":append_builtin,
}

############ Frames / Env ############
class ParentFrame:
    def __init__(self): self.bindings = scheme_builtins.copy()
    def lookup(self,n):
        if n in self.bindings: return self.bindings[n]
        raise SchemeNameError()
    def define(self,n,v): self.bindings[n]=v

class Frames:
    def __init__(self,parent=None):
        self.bindings={}
        self.parent=parent or ParentFrame()
    def define(self,n,v): self.bindings[n]=v
    def lookup(self,n):
        return self.bindings[n] if n in self.bindings else self.parent.lookup(n)
def make_initial_frame(): return Frames()

########### User Lambdas #############
class Function:
    def __init__(self,params,body,env):
        self.p,self.b,self.e = params,body,env
    def __call__(self,*a):
        if len(a)!=len(self.p): raise SchemeEvaluationError()
        call=Frames(self.e)
        for p,v in zip(self.p,a): call.define(p,v)
        return evaluate(self.b,call)

################ Evaluate ################
def evaluate(expr, env=None):
    env = env or make_initial_frame()
    if isinstance(expr,list) and expr==[]: return EMPTY
    if isinstance(expr,(int,float,bool)): return expr
    if isinstance(expr,str):
        if expr=="()": return EMPTY
        return env.lookup(expr)
    if not isinstance(expr,list) or not expr: raise SchemeEvaluationError()

    op,*rest = expr
    if op=="define":
        target,valexpr = rest
        if isinstance(target,list):
            name,params = target[0],target[1:]
            fn=Function(params,valexpr,env); env.define(name,fn); return fn
        val=evaluate(valexpr,env); env.define(target,val); return val
    if op=="lambda": return Function(rest[0],rest[1],env)
    if op=="if":
        tst,thn,alt = rest
        return evaluate(thn,env) if evaluate(tst,env) else evaluate(alt,env)
    if op=="and":
        for e in rest:
            if evaluate(e,env) is False: return False
        return True
    if op=="or":
        for e in rest:
            v=evaluate(e,env)
            if v is not False: return v
        return False
    if op=="begin":
        val=None
        for e in rest: val=evaluate(e,env)
        return val
    if op == "del":
        var = expr[1]
        if (var in env.bindings):
            val = env.lookup(var)
            del env.bindings[var]
            return val
        else:
            raise SchemeNameError()
       # ---------------------------------------------------------------
    #  LET  special-form
    #   (let ((var1 expr1) (var2 expr2) …)  body-expr)
    # ---------------------------------------------------------------
    if op == "let":
        new_env = Frames(env)
        bindings = expr[1]
        body = expr[2]
        for pairs in bindings:
            if len(pairs) != 2:
                raise SchemeSyntaxError()
            var, val_expr = pairs
            value = evaluate(val_expr, env)
            new_env.define(var, value)
        return evaluate(expr[2], new_env)
    if op == "set!":
        new_frame = make_initial_frame()
        new_frame.parent = env
        m = new_frame
        eval = evaluate(expr[2], env)
        var = expr[1]
        enter = False
        try:
            new_frame.lookup(var)
            while(enter != True):
                if (var in m.bindings):
                    m.define(var, eval)
                    enter = True
                else:
                    m = m.parent
        except:
            raise SchemeNameError()
        return eval







        

    proc=evaluate(op,env)
    args=[evaluate(a,env) for a in rest]
    try: return proc(*args)
    except SchemeError: raise
    except Exception: raise SchemeEvaluationError()

############### Helper: split token stream ###############
def _toplevel_forms(tokens):
    depth,start = 0,0
    for i,tk in enumerate(tokens):
        if tk=="(": depth+=1
        elif tk==")": depth-=1
        if depth==0:              # end of a top-level form
            yield tokens[start:i+1]
            start = i+1

################ evaluate_file ################
def evaluate_file(file_name=None, env=None):
    env = env or make_initial_frame()
    results = []

    file_list = (
        [file_name] if file_name is not None
        else [p for p in sys.argv[1:] if p.endswith(".scm") or p.endswith(".txt")]
    )

    for path in file_list:
        print("LOAD-SCM:", path, file=sys.stderr) 
        with open(path,"r",encoding="utf-8") as f:
            toks = tokenize(f.read())
            for chunk in _toplevel_forms(toks):
                expr = parse(chunk)
                results.append(evaluate(expr,env))
    return results[-1] if results else None



################### REPL #####################
########################  REPL launcher  ########################
if __name__ == "__main__":
    import schemerepl, sys, os

    # make sure the helper REPL finds the lab module on sys.path
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

    # any *.scm files passed on the command line?
    cli_files = [p for p in sys.argv[1:] if p.endswith(".scm") or p.endswith(".txt")]

    if cli_files:
        # preload those files into a single shared frame
        frame = make_initial_frame()
        evaluate_file(None, env=frame)           # evaluate CLI files first

        # start the interactive REPL **with that populated frame**
        schemerepl.SchemeREPL(
            sys.modules[__name__],               # lab_module (positional arg)
            use_frames= True ,
            repl_frame=frame,
            verbose=False
        ).cmdloop()
    else:
        # plain interactive mode (fresh top-level frame)
        schemerepl.SchemeREPL(
            sys.modules[__name__],
            use_frames=True,
            verbose=False
        ).cmdloop()
