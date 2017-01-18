
KEYWORDS = {'def', 'var'}
SYMBOLS = tuple(reversed([
    '(', ')', '[', ']', '{', '}',
]))

class Source(object):
    def __init__(self, name, contents):
        self.name = name
        self.contents = contents


class Token(object):
    def __init__(self, type, value=None, source=None, pos=None):
        self.type = type
        self.value = value
        self.source = source
        self.pos = pos

    def __eq__(self, other):
        return self.type == other.type and self.value == other.value

    def __repr__(self):
        return 'Token({}, {})'.format(self.type, self.value)


class ParseError(Exception):
    def __init__(self, message, token):
        self.message = message
        self.token = token


class Parser(object):
    def __init__(self, source):
        self.source = source
        self._s = source.contents
        self._p = 0  # current position in the lex
        self._pp = None  # position of the peek token
        self._peek = self._extract()

    @property
    def _c(self):
        return self._s[self._p] if self._p < len(self._s) else ''

    def _skipspaces(self):
        while self._c.isspace():
            self._p += 1

    def _cut(self):
        return self._s[self._pp:self._p]

    def _tok(self, type, hasValue=True):
        if hasValue:
            value = self._cut()
        else:
            value = None
        return Token(type, value, self.source, self._pp)

    def _extract(self):
        self._skipspaces()
        self._pp = self._p

        if not self._c:
            return self._tok('EOF', hasValue=False)

        if self._c.isdigit():
            while self._c.isdigit():
                self._p += 1
            if self._c == '.':
                self._p += 1
                while self._c.isdigit():
                    self._p += 1
                return self._tok('FLOAT')
            else:
                return self._tok('INT')

        if self._c.isalpha() or self._c == '_':
            while self._c.isalnum() or self._c == '_':
                self._p += 1
            if self._cut() in KEYWORDS:
                return self._tok(self._cut(), hasValue=False)
            else:
                return self._tok('NAME')

        if self._c in '"\'' or self._s[self._p:self._p+2] in ('r"', "r'"):
            if self._c == 'r':
                raw = True
                self._p += 1
            else:
                raw = False
            q = self._c
            if self._s.startswith(q * 3, self._p):
                q = q * 3
            self._p += len(q)
            buf = ''
            while self._c and not self._s.startswith(q, self._p):
                if raw or self._c != '\\':
                    buf += self._c
                else:
                    self._p += 1
                    if not self._c:
                        raise ParseError("Invalid escape", self._tok('ERR'))
                    if self._c == 'n':
                        buf += '\n'
                    else:
                        raise ParseError(
                            "Invalid escape " + self._c, self._tok('ERR'))
            if not self._c:
                raise ParseError("Unclosed string literal", self._tok('ERR'))
            self._p += len(q)
            return self._tok('STRING')

        for sym in SYMBOLS:
            if self._s.startswith(sym, self._p):
                self._p += len(sym)
                return self._tok(sym, hasValue=False)

        while self._c and not self._c.isspace():
            self._p += 1

        raise ParseError("Unrecognized token " + value, self._tok('ERR'))



def test():
    pass

