#!/usr/bin/python3
import time

class Stack:
    """FIFO Stack for NPN lang machine"""
    def __init__(self):
        self._stack_array = []
        self._last_val = None
        self._stack_underflow = False
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
            self._stack_array.append(self._last_val)
    def clear_stack(self):
        self._stack_array.clear()
    def good(self):
        return not self._stack_underflow
    def clear_err(self):
        self._stack_underflow = False
    def size(self):
        return len(self._stack_array)

class Machine:
    """Experimental NPN language core machine"""
    __version__ = "v0.0.4"
    def _noop(self):
        pass
    def __init__(self):
        self._symbols = {"+":self._add,"-":self._sub,"*":self._mul,"/":self._div,"%":self._mod,"clr":self._noop,"pop":self._noop,"decl":self._decl,"undecl":self._undecl,"lbl":self._lbl,"if":self._noop,"==":self._equ,"!=":self._inequ,"do":self._noop,"undo":self._noop,"end":self._noop,"cont":self._noop,"<":self._lt,">":self._gt,"goto":self._goto,"ret":self._ret,"subrt":self._subrt,"read":self._noop,"dump":self._noop,"open":self._noop,"exec":self._noop,"ref":self._ref,"wait":self._wait}
        self._special_symbols = {"null":None,";":"\n"}
        self._labels = {} #{"label" : stack_index}
        self._vars = {"_wait" : 1} #{"varname" : value}
        self._stack = Stack() #holds everything
        self._str = Stack()
        self._prog = []
        self._prog_index = 0
        self._subroutines = Stack()
        self._conditionals = [] #[{begin_index:end_index}]
        self._current_symbol = None
        self._symbols["clr"] = self._stack.clear_stack
        self._symbols["pop"] = self._stack.pop

    def clear(self):
        self._stack.clear_stack()
        self._prog.clear()
        self._subroutines.clear_stack()
        self._conditionals.clear()
        self._vars.clear()
        self._str.clear_stack()
        self._labels.clear()
        self._current_symbol = None
        self._prog_index = 0

    def _run_prog(self):
        self._stack.clear_stack()
        prog_len = len(self._prog)
        self._prog_index = 0
        self._subroutines.push(-1)
        exit_msg = "SUBRT -1 EXEC EOF"
        while self._prog_index < prog_len:
            #print(self._prog[self._prog_index])
            if self._prog[self._prog_index][1]:
                self._prog[self._prog_index][0]()
            else:
                if type(self._prog[self._prog_index][0]) == str:
                    self._str.push(self._prog[self._prog_index][0])
                else:
                    self._stack.push(self._prog[self._prog_index][0])
            print(f"IND: {self._prog_index}, STACK: {self._stack._stack_array}, STRS: {self._str._stack_array}, VARS: {self._vars}")
            if not self._stack.good():
                print("ERR: STACK UNDERFLOW")
                tmp = input("CONTINUE (y/N)?")
                if tmp.lower() == "y":
                    self._stack.clear_err()
                else:
                    exit_msg = "HALTING..."
                    break
            if self._prog_index < 0:
                exit_msg = "RET SUBRT -1"
                self._prog_index += 1
                break
            self._prog_index += 1
        print(exit_msg)

    def _load_prog(self, lines):
        for line in lines:
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
                    self._prog.append((self._current_symbol,False))
                    self._prog_index += 1
                else:
                    print("ERR: UNKNOWN SYMBOL")
            else:
                self._prog.append((self._current_symbol,True))
                self._prog_index += 1

    def interpreter(self):
        while True:
            prog_input = input(f"{self._prog_index}> ")
            if prog_input.lower() == "run":
                self._run_prog()
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
            prog_input = prog_input.split()
            print(prog_input)
            self._load_prog(prog_input)
        
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
        self._vars[str(b)] = a
    def _undecl(self):
        a = self._str.pop()
        self._vars.pop(a)
    def _ref(self):
        a = self._str.pop()
        b = self._vars.get(a)
        if b != None:
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
            self._subroutines.push(self._prog_index)
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
        if b > a:
            self._stack.push(1)
        else:
            self._stack.push(0)
    def _lt(self):
        a = self._stack.pop()
        b = self._stack.pop()
        if b < a:
            self._stack.push(1)
        else:
            self._stack.push(0)

print("HTROF INTERPRETER")
print("INIT MACHINE...")
machine = Machine()
print("MACHINE VER:",machine.__version__)
print("STARTING INTERFACE...")
print("CMDS: RUN,CLEAR(ALL/STACK/PROG),QUIT")
machine.interpreter()
