

free = 'o'
Q = 'x'

def generateKnowledge(n):
    prolog = ['\n\n\noneOrNoneOf(%s).' % ','.join(free * n)]
    prolog2 = []
    gdl = [('oneOrNoneOf',) + (free,) * n]
    for i in range(n):
        l = [free] * n
        l[i] = Q
        gdl.append(('oneOf', ) + tuple(l))
        gdl.append(('oneOrNoneOf', ) + tuple(l))
        prolog2.append( 'oneOf(%s).' % ','.join(l))
        prolog.append( 'oneOrNoneOf(%s).' % ','.join(l))
    prolog.extend(prolog2)
    del prolog2

    def at(x, y):
        assert 0 <= x < n
        assert 0 <= y < n
        return 'F%ix%i' % (x, y)

    args = []
    for x in range(n):
        for y in range(n):
            args.append(at(x, y))

    # vertical conditions

    
    field = ['<=', ['field'] + map(lambda v: '?' + v, args)]
    prolog.append( 'field(%s) :- ' %  ','.join(args))

    toVars = lambda args: tuple([('?' + arg if arg != free else free) \
                                 for arg in args])

    def oneOf(args):
        field.append(('oneOf',) + toVars(args))
        prolog.append('    oneOf(%s),' % ','.join(args))

    def oneOrNoneOf(args):
        field.append(('oneOrNoneOf',) + toVars(args))
        prolog.append('    oneOrNoneOf(%s),' % ','.join(args))

    for x in range(n):
        v = [] # vertial
        h = [] # horizontal
        ll = []
        lh = []
        rl = []
        rh = []
        for y in range(n):
            v.append(at(x, y))
            h.append(at(y, x))
            if x + y < n:
                ll.append(at(y, x + y))
                lh.append(at(y, n - (x + y) - 1))
                rl.append(at(n - y - 1, x + y))
                rh.append(at(n - y - 1, n - (x + y) - 1))
            else:
                ll.append(free)
                lh.append(free)
                rl.append(free)
                rh.append(free)
        oneOf(v)
        oneOf(h)
        oneOrNoneOf(ll)
        oneOrNoneOf(lh)
        oneOrNoneOf(rl)
        oneOrNoneOf(rh)

    gdl.append(tuple(field))
    prolog.append('    true.')
    prolog = '\n'.join(prolog)
    gdl = tuple(gdl)
    
    return gdl, prolog

class MyError(Exception):
    pass

def benchmarkGdl(n):
    print ' gdl %s '.center(60, '-') % n
    import sys, time
    sys.path.append('..')
    from akiraplayer.logic import Theory, _, fromVariableName
    l = []
    def callback(*args):
        l.append(args)
        raise MyError()

    gdl, prolog = generateKnowledge(n)
    theory = Theory(gdl)
##    print theory.source
    args = (_,) * n * n + (callback,)
    t = time.time()
    try:
        theory.functions['field_'](*args)
    except MyError:
        t = time.time() - t
    else:
        print 'no solution'
        return
    if 1:
        solution = l[0]
        i = 0
        for x in range(n):
            for y in range(n):
                print fromVariableName(solution[i]),
                i += 1
            print 
            
    print 'seconds for first solution: %s ' % t

# (file, command)
swi_prolog_interpreters = [
    ('C:/Program Files/pl/bin/swipl.exe', r'C:\Program Files\pl\bin\swipl.exe', 'C:\\Program Files\\pl\\bin\\')
    ]
    
def benchmarkProlog(n):
    print ' prolog: %s '.center(60, '-') % n
    import os, time
    import subprocess
    fileName = os.tempnam()
    file = open(fileName, 'w')
    gdl, prolog = generateKnowledge(n)
    file.write(prolog)
    file.write('\n')
    file.write('''
:- field(%s), halt; write('no solution'), halt.
''' % ','.join(['F%ix%i' % (x, y) for x in range(n) for y in range(n)]))
    file.close()
    for program in swi_prolog_interpreters:
        if os.path.exists(program[0]):
            break
    else:
        print 'no interpreter found'
        return

    ## '--quiet', 
    args = (program[1], '-s', fileName.replace('\\', '/'))
    print 'executing', args
    t = time.time()
    p = subprocess.Popen(args, stdout = subprocess.PIPE, \
                         stderr = subprocess.PIPE, stdin = subprocess.PIPE, \
                         cwd = program[2])
    p.wait()
    output, error = p.communicate('')
    t = time.time() - t
    print output
    if p.returncode != 0:
        print error
        print 'Error in prolog:', p.returncode
        return
    if output != 'no solution':
        print 'seconds for first solution: %s ' % t
    os.remove(fileName)


def benchmark(n):
    benchmarkGdl(n)
    benchmarkProlog(n)
    

if __name__ == '__main__':
    benchmark(8)
