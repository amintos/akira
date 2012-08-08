import os
import unittest
import time

EXCLUDE_LIST = [
    'test_all'
]

# find all test_*.py files and import everything

for file in os.listdir('.'):
    if file.lower().endswith('.py') and \
       file.lower().startswith('test_'):

        module_name = file[:-3]
        if module_name not in EXCLUDE_LIST:
            exec "from %s import *" % module_name
            print 'loaded', module_name
        else:
            print 'excluded', module_name

# do not mess up test-output with loading output
time.sleep(0.1)

# run and exit properly
unittest.main()