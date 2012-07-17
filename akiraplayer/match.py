#
#   A running match
#

from log import Main

TIME_BUFFER = 0.2   # seconds

class Match(object):

    def __init__(self, id, role, rules, start_clock, play_clock):
        self.id = id
        self.role = role
        self.rules = rules
        self.start_clock = start_clock
        self.play_clock = play_clock
        print self.rules

    # This method is blocking for at most start_clock seconds and returns
    # whether game initialization was successful.
    def start(self):
        Main.inform("starting %s" % self.id)
        return True

    # This method is blocking for play_clock seconds and responds
    # with a legal move as predicate tuple
    def play(self, all_moves):
        Main.inform("playing after %s" % str(all_moves))
        return ('move', 'anywhere')

    # This method cleans up after a match has been finished or stopped by
    # the game master.
    def stop(self):
        Main.inform("stopping")
        pass

