#
#   Parser & Formatter for Knowledge Interchange Format
#

WHITESPACE = set((' ', '\t', '\n', '\r', ';'))
BEGIN = '('
END = ')'
COMMENT_START = ';'
COMMENT_END = '\n'

SINGLE_TOKENS = WHITESPACE\
                | set((BEGIN, END))\
                | set((COMMENT_START, COMMENT_END))

class Parser(object):

    def __init__(self, raw_gdl):
        '''Initializes a parser over the given KIF code'''
        self.data = raw_gdl
        self.length = len(raw_gdl)
        self.offset = 0

    def next_token(self):
        self.skip_whitespace()
        if self.offset < self.length:
            t = self.data[self.offset]
            if t in SINGLE_TOKENS:
                self.offset += 1
                return t
            else:
                return self.next_symbol()
        else:
            return None

    def skip_whitespace(self):
        if self.offset >= self.length:
            return

        is_comment = self.data[self.offset] == COMMENT_START

        while (self.offset < self.length) and\
              (self.data[self.offset] in WHITESPACE) or\
              (is_comment):

            if is_comment and self.data[self.offset] == COMMENT_END:
                is_comment = False
            elif not is_comment and self.data[self.offset] == COMMENT_START:
                is_comment = True

            self.offset += 1

    def next_symbol(self):
        i = self.offset
        n = self.length
        d = self.data
        while i < n and not d[i] in SINGLE_TOKENS:
            i += 1
        symbol = d[self.offset : i]
        self.offset = i
        return symbol

    def ast(self, literal_transform = str, compound_transform = tuple):
        symbols = []
        while self.offset < self.length:
            t = self.next_token()
            if t == BEGIN:
                symbols.append(self.ast(literal_transform, compound_transform))
            elif t == END:
                return compound_transform(symbols)
            elif t == None:
                pass
            else:
                symbols.append(literal_transform(t))
        return compound_transform(symbols)

    def first_node(self, literal_transform = str, compound_transform = tuple):
        '''Return the first parsed root node.'''
        try:
            return self.ast(literal_transform, compound_transform)[0]
        except IndexError as e:
            raise ValueError("Parsing did not yield an element")


class Formatter(object):

    def __init__(self, data_tuple):
        self.data_tuple = data_tuple
        self.out = None

    def format_item(self, item):
        if isinstance(item, tuple):
            return self.format_compound(item)
        else:
            return self.format_literal(item)

    def format_compound(self, item):
        return BEGIN + ' '.join(map(self.format_item, item)) + END

    def format_literal(self, item):
        return str(item)

    def kif(self):
        if not self.out:
            self.out = self.format_item(self.data_tuple)
        return self.out