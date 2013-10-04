# -*- coding: utf-8 -*-
# Copyright (C) 2013, the IEP development team
#
# IEP is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

""" 
Magic commands for the IEP kernel.
No need to use printDirect here, magic commands are just like normal Python
commands, in the sense that they print something etc.
"""

import sys
import os

MESSAGE = """List of *magic* commands:
    ?               - show this message
    ?X or X?        - show docstring of X
    ??X or X??      - help(X)
    cd              - show current directory
    cd X            - change directory
    ls              - list current directory
    who             - list variables in current workspace
    whos            - list variables plus their class and representation
    timeit X        - times execution of command X
    open X          - open file X or the Python module that defines object X
    run X           - run file X
    pip             - manage packages using pip
    conda           - manage packages using conda
    db X            - debug commands
"""


TIMEIT_MESSAGE = """Time execution duration. Usage:
    timeit fun  # where fun is a callable
    timeit 'expression'
    timeit 20 fun  # tests 20 passes
    For more advanced use, see the timeit module.
"""


class Magician:
    
    def _eval(self, command):
        
        # Get namespace
        NS1 = sys._iepInterpreter.locals
        NS2 = sys._iepInterpreter.globals
        if not NS2:
            NS = NS1
        else:
            NS = NS2.copy()
            NS.update(NS1)
        
        # Evaluate in namespace
        return eval(command, {}, NS)
    
    
    def convert_command(self, line):
        """ convert_command(line)
        
        Convert a given command from a magic command to Python code.
        Returns the converted command if it was a magic command, or 
        the original otherwise.
        
        """
        # Get converted command, catch and report errors
        try:
            res = self._convert_command(line)
        except Exception:
            # Try informing about line number
            type, value, tb = sys.exc_info()
            msg = 'Error in handling magic function:\n'
            msg += '  %s\n' % str(value)
            if tb.tb_next: tb = tb.tb_next.tb_next
            while tb:
                msg += '  line %i in %s\n' % (tb.tb_lineno, tb.tb_frame.f_code.co_filename)
                tb = tb.tb_next
            # Clear
            del tb
            # Write
            print(msg)
            return None
        
        # Process
        if res is None:
            return line
        else:
            return res
    
    
    def _convert_command(self, line):
        
        # Get interpreter
        interpreter = sys._iepInterpreter
        
        # Check if it is a variable
        command = line.rstrip()
        if ' ' not in command:
            if command in interpreter.locals:
                return
            if interpreter.globals and command in interpreter.globals:
                return
        
        # Clean and make case insensitive
        command = line.upper().rstrip()
        
        if not command:
            return
        
        elif command == '?':
            return 'print(%s)' % repr(MESSAGE)
        
        elif command.startswith("??"):
            return 'help(%s)' % line[2:].rstrip()
        elif command.endswith("??"):
            return 'help(%s)' % line.rstrip()[:-2]
        
        elif command.startswith("?"):
            return 'print(%s.__doc__)' % line[1:].rstrip()
            
        elif command.endswith("?"):
            return 'print(%s.__doc__)' % line.rstrip()[:-1]
        
        elif command.startswith('CD'):
            return self.cd(line, command)
        
        elif command.startswith('LS'):
            return self.ls(line, command)
        
        elif command.startswith('DB'):
            return self.debug(line, command)
        
        elif command.startswith('TIMEIT'):
            return self.timeit(line, command)
        
        elif command == 'WHO':
            return self.who(line, command)
        
        elif command == 'WHOS':
            return self.whos(line, command)
        
        elif command.startswith('OPEN '):
            return self.open(line, command)
        
        elif command.startswith('RUN '):
            return self.run(line, command)
        
        elif command.startswith('CONDA'):
            return self.conda(line, command)
        
        elif command.startswith('PIP'):
            return self.pip(line, command)
    
    
    def debug(self, line, command):
        if command == 'DB':
            line = 'db help'
        elif not command.startswith('DB '):
            return
        
        # Get interpreter
        interpreter = sys._iepInterpreter
        # Get command and arg
        line += ' '
        _, cmd, arg = line.split(' ', 2)
        cmd = cmd.lower()
        # Get func
        func = getattr(interpreter.debugger, 'do_'+cmd, None)
        # Call or show warning
        if func is not None:
            func(arg.strip())
        else:
            interpreter.write("Unknown debug command: %s.\n" % cmd)
        # Done (no code to execute)
        return ''
    
    
    def cd(self, line, command):
        if command == 'CD' or command.startswith("CD ") and '=' not in command:
            path = line[3:].strip()
            if path:
                try:
                    os.chdir(path)
                except Exception:
                    print('Could not change to directory "%s".' % path)
                    return ''
                newPath = os.getcwd()
            else:
                newPath = os.getcwd()
            # Done
            print(repr(newPath))
            return ''
    
    def ls(self, line, command):
        if command == 'LS' or command.startswith("LS ") and '=' not in command:
            path = line[3:].strip()
            if not path:
                path = os.getcwd()
            L = [p for p in os.listdir(path) if not p.startswith('.')]
            text = '\n'.join(sorted(L))
            # Done
            print(text)
            return ''
    
    
    def timeit(self, line, command):
        if command == "TIMEIT":
            return line, 'print(%s)' % repr(TIMEIT_MESSAGE)
        elif command.startswith("TIMEIT "):
            expression = line[7:]
            # Get number of iterations
            N = 1
            tmp = expression.split(' ',1)
            if len(tmp)==2:
                try:
                    N = int(tmp[0])
                    expression = tmp[1]
                except Exception:
                    pass
            # Compile expression
            line2 = 'import timeit; t=timeit.Timer(%s);' % expression
            line2 += 'print(str( t.timeit(%i)/%i ) ' % (N, N)
            line2 += '+" seconds on average for %i iterations." )' % N
            #
            return line2
    
    
    def who(self, line, command):
        L = self._eval('dir()\n')
        L = [k for k in L if not k.startswith('__')]
        if L:
            print(', '.join(L))
        else:
            print("There are no variables defined in this scope.")
        return ''
    
    
    def _justify(self, line, width, offset):
        realWidth = width - offset
        if len(line) > realWidth:
            line = line[:realWidth-3] + '...'
        return line.ljust(width)
    
    
    def whos(self, line, command):
        # Get list of variables
        L = self._eval('dir()\n')
        L = [k for k in L if not k.startswith('__')]
        # Anny variables?
        if not L:
            print("There are no variables defined in this scope.")
            return ''
        else:
            text = "VARIABLE: ".ljust(20,' ') + "TYPE: ".ljust(20,' ') 
            text += "REPRESENTATION: ".ljust(20,' ') + '\n'
        # Create list item for each variablee
        for name in L:
            ob = self._eval(name)
            cls = ''
            if hasattr(ob, '__class__'):
                cls = ob.__class__.__name__
            rep = repr(ob)
            text += self._justify(name,20,2) + self._justify(cls,20,2)
            text += self._justify(rep,40,2) + '\n'
        # Done
        print(text)
        return ''
    
    
    def open(self, line, command):
        
        # Get what to open            
        name = line.split(' ',1)[1].strip()
        fname = ''
        
        # Is it a file name?
        tmp = os.path.join(os.getcwd(), name)
        #
        if name[0] in '"\'' and name[-1] in '"\'': # Explicitly given
            fname = name[1:-1]
        elif os.path.isfile(tmp):
            fname = tmp
        elif os.path.isfile(name):
            fname = name
        
        else:
            # Then it maybe is an object
            
            # Get the object
            try:
                ob = self._eval(name)
            except NameError:
                print('There is not object known as "%s"' % name)
                return ''
            
            # Get its file name
            fname is None
            if hasattr(ob, '__file__'):
                fname = ob.__file__
            elif hasattr(ob, '__module__'):
                tmp = sys.modules[ob.__module__]
                if hasattr(tmp, '__file__'):
                    fname = tmp.__file__
            
            # Make .py from .pyc
            if fname and fname.endswith('.pyc') or fname.endswith('.pyo'):
                fname2 = fname
                fname = fname[:-1]
                if not os.path.isfile(fname):
                    print('Could not find source file for "%s".' % fname2)
                    return ''
        
        # Almost done
        if not fname:
            print('Could not determine file name for object "%s".' % name)
        else:
            action = 'open %s' % os.path.abspath(fname)
            sys._iepInterpreter.context._strm_action.send(action)
        #
        return ''
    
    
    def run(self, line, command):
        
        # Get what to open            
        name = line.split(' ',1)[1].strip()
        fname = ''
        
        # Enable dealing with qoutes
        if name[0] in '"\'' and name[-1] in '"\'':
            name = name[1:-1]
        
        # Is it a file name?
        tmp = os.path.join(os.getcwd(), name)
        #
        if os.path.isfile(tmp):
            fname = tmp
        elif os.path.isfile(name):
            fname = name
        
        # Go run!
        if not fname:
            print('Could not find file to run "%s".' % name)
        else:
            sys._iepInterpreter.runfile(fname)
        #
        return ''
    
    
    def conda(self, line, command):
        
        if not (command == 'CONDA' or command.startswith('CONDA ')):
            return
        
        # Get command args
        args = line.split(' ')
        args = [w for w in args if w]
        args.pop(0) # remove 'conda'
        
        # Stop if user does "conda = ..."
        if args and '=' in args[0]:
            return
        
        # Go!
        # Weird double-try, to make work on Python 2.4
        oldargs = sys.argv
        try:
            try:
                import conda
                from conda.cli import main
                sys.argv = ['conda'] + list(args)
                main()
            except SystemExit:  # as err:
                type, err, tb = sys.exc_info(); del tb
                err = str(err)
                if len(err) > 4:  # Only print if looks like a message
                    print(err)
            except Exception:  # as err:
                type, err, tb = sys.exc_info(); del tb
                print('Error in conda command:')
                print(err)
        finally:
            sys.argv = oldargs
        
        return ''
    
    
    def pip(self, line, command):
        
        if not (command == 'PIP' or command.startswith('PIP ')):
            return
        
        # Get command args
        args = line.split(' ')
        args = [w for w in args if w]
        args.pop(0) # remove 'pip'
        
        # Stop if user does "pip = ..."
        if args and '=' in args[0]:
            return
        
        # Tweak the args
        if args[0] == 'uninstall':
            args.insert(1, '--yes')
        
        # Go!
        try:
            from iepkernel.pipper import pip_command 
            pip_command(*args)
        except SystemExit:  # as err:
            type, err, tb = sys.exc_info(); del tb
            err = str(err)
            if len(err) > 4:  # Only print if looks like a message
                print(err)
        except Exception:# as err:
            type, err, tb = sys.exc_info(); del tb
            print('Error in pip command:')
            print(err)
        
        return ''