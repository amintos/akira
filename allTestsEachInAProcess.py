import os
import sys
import subprocess
import re

def isTestFile(fileName):
    return fileName.lower().startswith('test_') and \
           (   fileName.lower().endswith('.py') or \
               fileName.lower().endswith('.pyw'))

cwd = os.getcwd()
try:
    for dirPath, dirNames, fileNames in os.walk(os.path.abspath('.')):
        os.chdir(dirPath)
        for fileName in fileNames:
            if isTestFile(fileName):
##                print fileName
                p = subprocess.Popen([sys.executable, fileName],
                                     stdin = subprocess.PIPE,
                                     stderr = subprocess.PIPE,
                                     stdout = subprocess.PIPE)
                try:
                    stdout, stderr = p.communicate()
                except KeyboardInterrupt:
                    print 'Interrupted:', fileName
                    raise 
                stderr =  stderr.rstrip()
                
                if not stderr[-10:].lower().endswith('ok'):
                    print stderr, 
                    print fileName
                    print 
                else:
                    print stderr[:-2].rstrip()

finally:
    os.chdir(cwd)

if not 'idlelib' in sys.modules:
    raw_input('>')
