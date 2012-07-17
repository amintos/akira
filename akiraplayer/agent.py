#
#   HTTP/AAAI Game Agent
#

from BaseHTTPServer import *
from kif import Parser, Formatter
from match import Match

# Global Agent State

matches = dict()

# -----------------------------------------------------------------------------
# AAAI PROTOCOL HANDLER

class GameRequestHandler(BaseHTTPRequestHandler):

    # -------------------------------------------------------------------------
    # REQUEST HANDLING

    def do_GET(self):
        self.respond_with('Hello World')
        # maybe we could repsond with something meaningful later

    def do_POST(self):
        # an AAAI game master contacts us via POST on /
        if self.path == '/':
            size = int(self.headers['content-length'])
            content = self.rfile.read(size)
            self.process_game_message(content)

    def respond_with(self, message, status = 200):
        self.send_response(status)
        self.send_header('content-type', 'text/html')
        self.send_header('content-length', str(len(message)))
        self.end_headers()
        self.wfile.write(message)

        print message

    # -------------------------------------------------------------------------
    # REQUEST INTERPRETATION

    def parse_message(self, message):
        # parse Lisp-like format of message
        data = Parser(message).first_node()

        # messages take the form (COMMAND  MATCH_ID  ARG_0 ... ARG_N)
        command     = data[0].upper()
        match_id    = data[1]
        arguments   = data[2:]  # rest
        return command, match_id, arguments


    def process_game_message(self, message):
        command, match_id, args = self.parse_message(message)

        # dispatch messages to running matches or start a new match
        if match_id in matches:
            if command == 'PLAY':  return self.play(match_id, *args)
            if command == 'STOP':  return self.stop(match_id, *args)
        else:
            if command == 'START': return self.start(match_id, *args)

            # should not reach here:
            self.respond_with('Unknown Match ID: %s' % match_id, 500)

    # -------------------------------------------------------------------------
    # GAME COMMAND IMPLEMENTATIONS

    def start(self, match_id, role, gdl_rules, start_clock, play_clock, *_):
        match = Match(
            match_id,
            role,
            gdl_rules,
            int(start_clock),
            int(play_clock))

        matches[match_id] = match

        if match.start():           # blocking call!
            self.respond_with('READY')
        else:
            self.respond_with('ERROR on START', 500)


    def play(self, match_id, all_moves, *_):
        move = matches[match_id].play(all_moves)
        f = Formatter(move)
        self.respond_with(f.kif())


    def stop(self, match_id, *_):
        matches[match_id].stop()
        del matches[match_id]





# -----------------------------------------------------------------------------
# AGENT STARTUP

def serve(port = 4001):
    server = HTTPServer(('', port), GameRequestHandler)
    server.serve_forever()
    return server

serve()
