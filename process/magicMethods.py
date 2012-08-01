'''module to unite all names of magic methods - methods that are not accessed
via __getattribute__
thus directly called by the interpreter (maybe but not for sure)

to add new methods of an object use add(object)
to add a  new magic method name use adds(name)

'''
import sys
import traceback
import types

noMagicMethods= set(['__class__', '__name__', '__new__', '__init__', '__doc__',\
                     '__metaclass__', '__del__', '__base__'])
magicMethods= set([])

_onChange= []

def onChange(function):
    '''call this function if magicMethods changes
with the new magic method set as first argument

add this function to the _onChange function list
'''
    _onChange.append(function)

def changed():
    '''this function calls all registered functions
with the magic method set as first argument'''
    it= iter(_onChange[:])
    for f in it:
        try:
            f(magicMethods)
            for f in it:
                f(magicMethods)
        except:
            traceback.print_exception(*sys.exc_info())

def _add(obj, rec= 1):
    global magicMethods
    if rec and isinstance(obj, types.ModuleType):
        rec-= 1
        for attr in dir(obj):
            add(getattr(obj, attr, None), rec)
    else:
        magicMethods |= (set([attr for attr in dir(obj) if \
                             attr[:2] == '__' and attr[-2:] == '__' and \
                             hasattr(getattr(obj, attr, None), '__call__')]) | \
                        noMagicMethods ) ^ noMagicMethods
def add(obj, rec= 1):
    '''add the names of objects magic methods to the magic method set'''
    _add(obj, rec)
    changed()
    

def adds(*strings):
    '''add these strings to the magic method set'''
    global magicMethods
    magicMethods|= (set(strings) | noMagicMethods ) ^ noMagicMethods
    changed()
    

add(__builtins__)
add(types)



__all__ = ['magicMethods', 'add', 'adds', 'onChange', 'changed']
