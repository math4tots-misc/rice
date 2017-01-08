"""
Simple language with no explicit typing that translates to C++14
"""
import sys

openbr = '{'
closebr = '}'
openpar = '('
closepar = ')'
openbk = '['
closebk = ']'


SYMBOLS = list(reversed(sorted([
    '\n', '(', ')', '{', '}', '[', ']',
    '+', '-', '*', '%', '/', ',',
    '=', '\\', '->', '.',
])))


KEYWORDS = {
    'include', 'import',
    'def', 'class', 'while', 'return', 'var'
}

PREFIX = r"""
#include <iostream>
#include <string>
#include <memory>
#include <vector>
#include <sstream>

using Int = long long;
using Float = double;

template <class T> class List;
template <class T> List<T> mklist(const std::initializer_list<T> &v);

struct String final {
    std::shared_ptr<std::string> buffer;
    String()=default;
    String(const String&)=default;
    String(const std::string &s): buffer(std::make_shared<std::string>(s)) {}
    String rrstr() const { return *this; }
};

template <class T>
struct List final {
    std::shared_ptr<std::vector<T>> buffer;
    List()=default;
    List(const List&)=default;
    List(const std::vector<T> &v): buffer(std::make_shared<std::vector<T>>(v)) {}
    String rrstr() const {
        std::stringstream ss;
        ss << "List(";
        if (!buffer->empty()) {
            ss << (*buffer)[0];
            for (unsigned int i = 1; i < buffer->size(); i++) {
                ss << ", " << (*buffer)[i];
            }
        }
        ss << ")";
        return String(ss.str());
    }
    template <class F>
    auto rrmap(F f) const {
        auto ret = mklist<decltype(f((*buffer)[0]))>({});
        for (T t: (*buffer)) {
            ret.buffer->push_back(f(t));
        }
        return ret;
    }
};

template <class T>
List<T> mklist(const std::initializer_list<T> &v) {
    return List<T>(std::vector<T>(v));
}

struct {
    template <class T>
    auto operator()(T t) {
        return t.rrstr();
    }
    auto operator()(Int t) {
        return String(std::to_string(t));
    }
    auto operator()(Float t) {
        return String(std::to_string(t));
    }
} rrstr;

struct {
    template <class T>
    void operator()(T t) {
        std::cout << *rrstr(t).buffer << std::endl;
    }
} rrprint;

"""

POSTFIX = r"""
int main() {
    rrmain();
}
"""

class Token(object):
    def __init__(self, i, type_, value):
        self.i = i
        self.type = type_
        self.value = value

    def __repr__(self):
        return 'Token(%r, %r)' % (self.type, self.value)


def lex(s):
    i = 0
    ps = [openbr]
    ts = []
    ms = {
        openbr: closebr,
        '(': ')',
        '[': ']',
    }

    def nlis():  # newline is space
        return ps[-1] != closebr

    def at_space_or_comment():
        return i < len(s) and (
            ((s[i] != '\n' or nlis()) and s[i].isspace()) or
            s[i] == '#'
        )

    while True:
        # skip spaces and comments
        while at_space_or_comment():
            if s[i] == '#':
                while i < len(s) and s[i] != '\n':
                    i += 1
            else:
                i += 1

        if i >= len(s):
            if len(ps) > 1:
                raise Exception("Unmatched: " + ps[-1])
            ts.append(Token(i, '\n', '\n'))
            ts.append(Token(i, 'EOF', ''))
            break

        j = i

        if any(s.startswith(t, i) for t in SYMBOLS):
            t = next(t for t in SYMBOLS if s.startswith(t, i))
            if t in ms:
                ps.append(t)
            elif t in ms.values():
                if ms[ps.pop()] != t:
                    raise Exception("Mismatched " + t)
            i += len(t)
            ts.append(Token(j, t, t))
            continue

        if s.startswith(('r"', '"', "r'", "'"), i):
            if s[i] == 'r':
                i += 1
            quotes = s[i:i+3] if s.startswith(s[i] * 3, i) else s[i]
            i += len(quotes)
            while i < len(s) and not s.startswith(quotes, i):
                i += 1
            if i >= len(s):
                lineno = 1 + s[:j].count('\n')
                raise Exception(
                    "String literal on line %d not terminated" % lineno)
            i += len(quotes)
            value = eval(s[j:i])
            ts.append(Token(j, 'STRING', value))
            continue

        if s[i].isdigit() or s[i] == '.' and s[i+1:i+2].isdigit():
            while i < len(s) and s[i].isdigit():
                i += 1
            if i < len(s) and s[i] == '.':
                i += 1
                while i < len(s) and s[i].isdigit():
                    i += 1
                ts.append(Token(j, 'FLOAT', float(s[j:i])))
            else:
                ts.append(Token(j, 'INT', int(s[j:i])))
            continue

        if s[i].isalpha() or s[i] == '_':
            while i < len(s) and (s[i].isalnum() or s[i] == '_'):
                i += 1
            value = s[j:i]
            if value in KEYWORDS:
                ts.append(Token(j, value, value))
            else:
                ts.append(Token(j, 'NAME', value))
            continue

        while i < len(s) and not s[i].isspace():
            i += 1
        raise Exception("Unrecognized token: " + s[j:i])

    return ts


def parse(s):
    ts = lex(s)
    i = [0]

    def peek():
        return ts[i[0]]

    def gettok():
        t = peek()
        i[0] += 1
        return t

    def at(t):
        return peek().type == t

    def atnl():
        return at('\n') or at(';')

    def expect(t):
        if not peek().type == t:
            raise Exception("Expected %r but got %r" % (t, peek()))
        return gettok()

    def consumenl():
        while atnl():
            gettok()

    def consume(t):
        if peek().type == t:
            return gettok()

    def ptop():
        if consume('def'):
            name = 'rr' + expect('NAME').value
            args = []
            expect(openpar)
            while not consume(closepar):
                args.append('rr' + expect('NAME').value)
                consume(',')
            body = pblock()
            consumenl()
            return '\nauto %s = [](%s)%s;' % (
                name, ', '.join('auto ' + n for n in args), body)
        else:
            raise Exception("Expected top-level statement but found %r" % peek())

    def pstmt():
        consumenl()
        if consume('var'):
            name = 'rr' + expect('NAME').value
            expect('=')
            expr = pexpr()
            consumenl()
            return '\nauto %s = %s;' % (name, expr)
        elif consume('return'):
            e = pexpr()
            consumenl()
            return '\nreturn %s;' % e
        elif at(openbr):
            b = pblock()
            consumenl()
            return b
        else:
            e = pexpr()
            consumenl()
            return '\n%s;' % (e,)

    def pblock():
        consumenl()
        expect(openbr)
        consumenl()
        stmts = []
        while not consume(closebr):
            stmts.append(pstmt())
            consumenl()
        return '\n{%s\n}' % (''.join(stmts).replace('\n', '\n  '))

    def pexpr():
        return pexpr3()

    def pexpr3():
        e = pexpr2()
        while True:
            if consume('+'):
                r = pexpr2()
                e = '(%s) + (%s)' % (e, r)
                continue
            if consume('-'):
                r = pexpr2()
                e = '(%s) - (%s)' % (e, r)
                continue
            break
        return e

    def pexpr2():
        e = pexpr1()
        while True:
            if consume('*'):
                r = pexpr1()
                e = '(%s) * (%s)' % (e, r)
                continue
            if consume('/'):
                r = pexpr1()
                e = '(%s) / (%s)' % (e, r)
                continue
            if consume('%'):
                r = pexpr1()
                e = '(%s) % (%s)' % (e, r)
                continue
            break
        return e

    def pexpr1():
        e = pexpr0()
        while True:
            if consume(openpar):
                args = []
                while not consume(closepar):
                    args.append(pexpr())
                    consume(',')
                e = '(%s)(%s)' % (e, ', '.join(args))
                continue
            if consume('.'):
                name = 'rr' + expect('NAME').value
                args = []
                expect(openpar)
                while not consume(closepar):
                    args.append(pexpr())
                    consume(',')
                e = '(%s).%s(%s)' % (e, name, ', '.join(args))
            break
        return e

    def pexpr0():
        if at('INT'):
            return str(expect('INT').value) + 'll'
        if at('FLOAT'):
            return str(expect('FLOAT').value)
        if at('NAME'):
            return 'rr' + expect('NAME').value
        if at('STRING'):
            return ''.join([
                'String("',
                expect('STRING').value
                    .replace('\\', '\\\\')
                    .replace('\t', '\\t')
                    .replace('\n', '\\n'),
                '")'])
        if consume(openbk):
            args = []
            while not consume(closebk):
                args.append(pexpr())
                consume(',')
            return ''.join(['mklist({', ', '.join(args), '})'])
        if consume('\\'):
            names = []
            while at('NAME'):
                names.append('rr' + expect('NAME').value)
            if consume('->'):
                body = '{ return %s; }' % pexpr()
            else:
                body = pblock()
            return ''.join([
                '[&](', ', '.join('auto ' + n for n in names), ')',
                body
            ])
        if consume(openpar):
            e = pexpr()
            expect(closepar)
            return e
        raise Exception("Expected expression but found " + repr(peek()))

    def pprog():
        stmts = []
        consumenl()
        while not at('EOF'):
            stmts.append(ptop())
        return ''.join([
            '// ------------------------------------------------------\n',
            '// -------- autogenerated from rclang source ------------\n',
            '// ------------------------------------------------------',
            PREFIX,
            ''.join(stmts),
            POSTFIX,
        ])

    return pprog()

print(parse(sys.stdin.read()))
