import os
import time


def byte():
    yield 'B'
    yield 'KB'
    yield 'MB'
    yield 'GB'
    while 1:
        yield ''

def splitInByteranges(number):
    b = byte()
    if number <= 0:
        return str(number) + next(b)
    number = int(number)
    if number <= 0:
        number = - number
        sign = '-'
    else:
        sign = ''
    l = []
    while number:
        l.append(str(number % 1024) + '_' + next(b))
        number /= 1024
    return sign + ' '.join(reversed(l[-2:]))
    

def testTroughput(read, write, title = None):
    if title is not None:
        print '-' * 8, title, '-' * 8
    s = '0'

    def do_throughput():
        write(s)
        return len(read(len(s)))

    last_throughput = None

    while 1:

        count_of_calls = 0
        start = time.time()
        end = start + 0.1
        t_ = end - 1;
        while end > t_:
            do_throughput()
            t_ = time.time()
            count_of_calls += 1
        end = t_
        
        data_amount = 0
        count_of_calls /= 100 ## raise this number if output blocks lower it for precision and risk of blocking
        start = time.time()
        end = start + 1
        t_ = end - 1;
        while end > t_:
            i = 0
            while i < count_of_calls:
                data_amount+= do_throughput()
                i += 1
            t_ = time.time()
        end = t_

        ##print  count_of_calls
        throughput = data_amount / (end - start)
        print 'packet length:', len(s), 'byte' + 's' * (bool(len(s) - 1)),
        print 'troughput:', splitInByteranges(throughput), '/s',
        if last_throughput:
            print 'last *', (throughput / last_throughput),
        print 
        
        s *= 2
        last_throughput = throughput

if __name__ == '__main__':
    read_fd, write_fd = os.pipe()
    testTroughput(lambda count: os.read(read_fd, count),
                  lambda string: os.write(write_fd, string),
                  'Benchmark of os.pipe()')

    
