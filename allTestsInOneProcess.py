
##
##  akira player
##

from akiraplayer.test_logic import *

##
##  process
##

from process.tests_all import *

if __name__ == '__main__':
    unittest.main(exit = False, verbosity = 1)
    if False:
        ## assure sometimes that all threads spawned by tests finished
        print_running_threads()


