import sys
import threading

class Logger(object):

    serial_lock = threading.Lock()

    def inform(self, message):
        with Logger.serial_lock:
            sys.stdout.write(message + '\n')
            sys.stdout.flush()

Main = Logger()