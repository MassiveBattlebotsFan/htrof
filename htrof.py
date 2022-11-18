#!/usr/bin/python3
import time, sys

class Stack:
    """FIFO Stack for NPN lang machine"""
    def __init__(self):
        self._stack_array = []
        self._last_val = None
        self._stack_underflow = False
        self._FIFO = True
    def pop(self):
        if len(self._stack_array) > 0:
            self._last_val = self._stack_array[0]
            self._stack_array = self._stack_array[1:]
            return self._last_val
        else:
            self._stack_underflow = True
            return self._last_val #this is a stack underflow
    def read_top(self):
        if len(self._stack_array) > 0:
            self._last_val = self._stack_array[0]
            return self._last_val
        else:
            self._stack_underflow = True
            return self._last_val #this is a stack underflow
    def push(self, *items):
        for item in items:
            self._last_val = item
            if self._FIFO:
                self._stack_array.append(self._last_val)
            else:
                self._stack_array.insert(0, self._last_val)
    def clear_stack(self):
        self._stack_array.clear()
        self._stack_underflow = False
    def good(self):
        return not self._stack_underflow
    def clear_err(self):
        self._stack_underflow = False
    def size(self):
        return len(self._stack_array)
    def toggle_mode(self):
        self._FIFO = not self._FIFO

class Machine:
    """Experimental RPN language core machine"""
    __version__ = "v0.0.7"
    def _noop(self):
        pass
    def __init__(self):
        self._symbols = {"+":self._add,"-":self._sub,"*":self._mul,"/":self._div,"%":self._mod,"pm":self._stack_mode,"init":self._set_init,"cat":self._cat,"split":self._split,"dmpnl":self._dmpnl,"clr":self._noop,"clrstr":self._noop,"pop":self._noop,"popstr":self._noop,"tostr":self._tostr,"dup":self._dup,"dupstr":self._dupstr,"decl":self._decl,"declstr":self._declstr,"undecl":self._undecl,"lbl":self._lbl,"if":self._if,"=":self._equ,"!=":self._inequ,"unif":self._unif,"end":self._end,"<":self._lt,">":self._gt,"goto":self._goto,"ret":self._ret,"subrt":self._subrt,"read":self._read,"dump":self._dump,"open":self._noop,"drop":self._noop,"exec":self._noop,"ref":self._ref,"wait":self._wait,"setobj":self._noop}
        self._special_symbols = {"null":None,";":"\n"}
        self._special_objects = {"stdio":(sys.stdin,sys.stdout)}
        self._current_object = "stdio"
        self._objects = {}
        self._labels = {} #{"label" : stack_index}
        self._sys_vars = {"_wait" : 1, "_nl" : '\n'} #{"varname" : value}
        self._vars = {}
        self._stack = Stack() #holds everything
        self._str = Stack()
        self._prog = []
        self._prog_index = 0
        self._init = False
        self._subroutines = []
        self._conditionals = {} #[{begin_index:end_index}]
        self._current_symbol = None
        self._symbols["clr"] = self._stack.clear_stack
        self._symbols["clrstr"] = self._str.clear_stack
        self._symbols["popstr"] = self._str.pop
        self._symbols["pop"] = self._stack.pop
        self._init_symbols = [self._symbols["lbl"], self._symbols["end"]]
        self._debug = False
    def debug_mode(self, val:bool):
        self._debug = val
    def clear(self):
        self._stack.clear_stack()
        self._prog.clear()
        self._subroutines.clear()
        self._conditionals.clear()
        self._vars.clear()
        for object in self._objects:
            object[0].close()
            object[1].close()
        self._objects.clear()
        self._current_object = "stdio"
        self._str.clear_stack()
        self._labels.clear()
        self._current_symbol = None
        self._prog_index = 0
        self._stack._FIFO = True
        self._str._FIFO = True
    def _run_prog(self):
        self._stack.clear_stack()
        self._str.clear_stack()
        self._stack._FIFO = True
        self._str._FIFO = True
        prog_len = len(self._prog)
        self._prog_index = 0
        self._subroutines.append(-1)
        exit_msg = "SUBRT -1 EXEC EOF"
        while self._prog_index < prog_len:
            #print(self._prog[self._prog_index])
            if self._prog[self._prog_index][1]:
                if not self._init or (self._prog[self._prog_index][0] in self._init_symbols):
                    self._prog[self._prog_index][0]()
            else:
                if type(self._prog[self._prog_index][0]) == str:
                    self._str.push(self._prog[self._prog_index][0])
                else:
                    self._stack.push(self._prog[self._prog_index][0])
            if self._debug:
                print(f"IND: {self._prog_index}, STACK: {self._stack._stack_array}, STRS: {self._str._stack_array}, VARS: {self._vars}")
            if not self._stack.good() or not self._str.good():
                print("ERR: STACK UNDERFLOW")
                tmp = input("CONTINUE (y/N)?")
                if tmp.lower() == "y":
                    self._stack.clear_err()
                    self._str.clear_err()
                else:
                    exit_msg = "HALTING..."
                    break
            if self._prog_index < 0:
                exit_msg = "RET SUBRT -1"
                self._prog_index += 1
                break
            self._prog_index += 1
        print("\n"+exit_msg)

    def _load_prog(self, data):
        old_ind = self._prog_index
        prog_clone = self._prog
        current_cond = None
        quote_symbol = False
        lines = []
        buffer = ""
        for dat in data:
            dat = dat.strip()
            for char in dat:
                if char == "\"" and not quote_symbol:
                    quote_symbol = True
                    buffer += char
                elif char == "\"" and quote_symbol:
                    quote_symbol = False
                    buffer += char
                elif not quote_symbol:
                    if char.isspace():
                        lines.append(buffer)
                        buffer = ""
                        continue
                    else:
                        buffer += char
                else:
                    buffer += char
            if len(buffer) > 0:
                lines.append(buffer)
                buffer = ""
        #print(lines)
        for line in lines:
            if len(line) == 0:
                continue
            self._current_symbol = self._symbols.get(line.lower())
            if self._current_symbol == None:
                if line.lower()[0:2] == "0x":
                    try:
                        self._current_symbol = int(line,base=16)
                    except ValueError:
                        self._current_symbol = None
                elif line.lower()[0:2] == "0b":
                    try:
                        self._current_symbol = int(line,base=2)
                    except ValueError:
                        self._current_symbol = None
                elif line.lower()[-1] == "f":
                    try:
                        self._current_symbol = float(line[0:len(line)-1])
                    except ValueError:
                        self._current_symbol = None
                elif line.lower()[0] == "\"":
                    self._current_symbol = line.replace("\"","")
                else:
                    try:
                        self._current_symbol = int(line)
                    except ValueError:
                        self._current_symbol = None
                if self._current_symbol != None:
                    prog_clone.append((self._current_symbol,False))
                    self._current_symbol = None
                    self._prog_index += 1
                else:
                    print("ERR: UNKNOWN SYMBOL")
            else:
                if line.lower() == "if" or line.lower() == "unif":
                    current_cond = self._prog_index
                if line.lower() == "end":
                    self._conditionals[current_cond] = self._prog_index
                    current_cond = None
                prog_clone.append((self._current_symbol,True))
                self._prog_index += 1
        if current_cond != None:
            print("ERR: UNCLOSED CONDITIONAL")
            self._prog_index = old_ind
        else:
            self._prog = prog_clone

    def interpreter(self):
        while True:
            print(f"{self._prog_index}> ",end='',flush=True)
            prog_input = sys.stdin.readline()[:-1]
            prog_input = prog_input.replace("\\n","\n")
            if prog_input.lower() == "run":
                self._run_prog()
                continue
            if prog_input.lower() == "debug":
                self.debug_mode(not self._debug)
                print("Debug:",str(self._debug))
                continue
            if prog_input.lower() == "quit":
                break
            if prog_input.lower() == "clearall":
                self.clear()
                continue
            if prog_input.lower() == "clearprog":
                self._prog.clear()
                self._prog_index = 0
                continue
            if prog_input.lower() == "clearstack":
                self._stack.clear_stack()
                continue
            if prog_input.lower() == "list":
                print(self._prog)
                continue
            #prog_input = prog_input.split()
            print(prog_input)
            self._load_prog([prog_input])

    def _stack_mode(self):
        self._str.toggle_mode()
        self._stack.toggle_mode()
    def _dmpnl(self):
        a = self._special_objects.get(self._current_object)
        if a == None:
            a = self._objects.get(self._current_object)
            if a == None:
                return
        a = a[1]
        a.write("\n")
    def _split(self):
        a = self._stack.pop()
        b = self._str.pop()
        if type(a) == int and a < len(b) and a >= 0:
            self._str.push(b[:a],b[a:])
        else:
            self._str.push(b)
    def _cat(self):
        a = self._str.pop()
        b = self._str.pop()
        self._str.push(a+b)
    def _tostr(self):
        a = self._stack.pop()
        self._str.push(str(a))
    def _read(self):
        a = self._special_objects.get(self._current_object)
        if a == None:
            a = self._objects.get(self._current_object)
            if a == None:
                return
        a = a[0]
        self._str.push(a.readline()[:-1].replace("\\n","\n"))
    def _dump(self):
        a = self._special_objects.get(self._current_object)
        if a == None:
            a = self._objects.get(self._current_object)
            if a == None:
                return
        a = a[1]
        a.write(self._str.pop())
    def _set_init(self):
        self._init = True
    def _end(self):
        if self._init:
            self._init = False
    def _add(self):
        a = self._stack.pop()
        b = self._stack.pop()
        self._stack.push(a+b)
    def _sub(self):
        a = self._stack.pop()
        b = self._stack.pop()
        self._stack.push(a-b)
    def _mul(self):
        a = self._stack.pop()
        b = self._stack.pop()
        self._stack.push(a*b)
    def _div(self):
        a = self._stack.pop()
        b = self._stack.pop()
        if b == 0:
            b = 1
        self._stack.push(a/b)
    def _mod(self):
        a = self._stack.pop()
        b = self._stack.pop()
        if b == 0:
            b = 1
        self._stack.push(a%b)
    def _decl(self):
        a = self._stack.pop()
        b = self._str.pop()
        if self._sys_vars.get(str(b)) != None:
            self._sys_vars[str(b)] = a
            return
        else:
            self._vars[str(b)] = a
    def _undecl(self):
        a = self._str.pop()
        self._vars.pop(a)
    def _declstr(self):
        a = self._str.pop()
        b = self._str.pop()
        self._vars[str(b)] = a
    def _ref(self):
        a = self._str.pop()
        b = self._sys_vars.get(a)
        if b == None:
            b = self._vars.get(a)
        if b != None:
            if type(b) == str:
                self._str.push(b)
            else:
                self._stack.push(b)
    def _lbl(self):
        a = self._str.pop()
        self._labels[str(a)] = self._prog_index
    def _goto(self):
        a = self._str.pop()
        b = self._labels.get(str(a))
        if type(b) == int:
            self._prog_index = b
    def _subrt(self):
        a = self._str.pop()
        b = self._labels.get(str(a))
        if type(b) == int:
            self._subroutines.append(self._prog_index)
            self._prog_index = b
    def _ret(self):
        a = self._subroutines.pop()
        self._prog_index = a
    def _wait(self):
        a = self._vars.get("_wait")
        if a != None:
            time.sleep(a)
    def _equ(self):
        a = self._stack.pop()
        b = self._stack.pop()
        if a == b:
            self._stack.push(1)
        else:
            self._stack.push(0)
    def _inequ(self):
        a = self._stack.pop()
        b = self._stack.pop()
        if a != b:
            self._stack.push(1)
        else:
            self._stack.push(0)
    def _gt(self):
        a = self._stack.pop()
        b = self._stack.pop()
        if a > b:
            self._stack.push(1)
        else:
            self._stack.push(0)
    def _lt(self):
        a = self._stack.pop()
        b = self._stack.pop()
        if a < b:
            self._stack.push(1)
        else:
            self._stack.push(0)
    def _if(self):
        a = self._stack.pop()
        if a == 0:
            self._prog_index = self._conditionals.get(self._prog_index)
    def _unif(self):
        a = self._stack.pop()
        if a != 0:
            self._prog_index = self._conditionals.get(self._prog_index)
    def _dup(self):
        a = self._stack.pop()
        self._stack.push(a,a)
    def _dupstr(self):
        a = self._str.pop()
        self._str.push(a,a)

print("HTROF INTERPRETER")
print("INIT MACHINE...")
machine = Machine()
print("MACHINE VER:",machine.__version__)
if len(sys.argv) > 1:
    print(f"ARGUMENT PASSED, LOADING [{sys.argv[1]}] AS FILE")
    with open(sys.argv[1], "r") as file:
        text = file.readlines()
    machine._load_prog(text)
    print("PROG LOADED")
print("STARTING INTERFACE...")
print("CMDS: RUN,CLEAR(ALL/STACK/PROG),QUIT")
machine.interpreter()
