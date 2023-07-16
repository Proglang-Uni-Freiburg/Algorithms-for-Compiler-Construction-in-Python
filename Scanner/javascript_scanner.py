from dataclasses import dataclass
from regexp import *
from scanner import *
import sys

@dataclass(frozen=True)
class Return(Token):
    pass

@dataclass(frozen=True)
class Intlit(Token):
    value: int

@dataclass(frozen=True)
class Ident(Token):
    name: str

@dataclass(frozen=True)
class Lparen(Token):
    pass

@dataclass(frozen=True)
class Rparen(Token):
    pass

@dataclass(frozen=True)
class Slash(Token):
    pass

@dataclass(frozen=True)
class Strlit(Token):
    value: str

digit = char_range_regexp("0", "9")
hexdigit = alternative_list([digit, char_range_regexp("A", "F"),
                             char_range_regexp("a", "f")])
hexprefix = alternative(string_regexp("0x"), string_regexp("0X"))
sign = optional(Symbol("-"))
integer_literal = alternative(concat(sign, repeat_one(digit)),
concat_list([sign, hexprefix, repeat_one(hexdigit)]))

letter = alternative(char_range_regexp("A", "Z"), char_range_regexp("a", "z"))
identifier_start = alternative_list([letter, Symbol("$"), Symbol("_")])
identifier_part = alternative(identifier_start, digit)
identifier = concat(identifier_start, repeat(identifier_part))

blank_characters = "\t "
line_end_characters = "\n\r"
white_space = repeat_one(class_regexp(blank_characters + line_end_characters))

escaped_char = concat(Symbol("\\"), alternative(Symbol("\\"), Symbol("\"")))
content_char = alternative_list([Symbol(chr(a))
                                 for a in range(ord(" "), 128)
                                 if a not in [ord("\\"), ord("\"")]])
string_literal = concat_list([Symbol("\""),
                              repeat(alternative(escaped_char, content_char)),
                              Symbol("\"")])

LexRule(string_literal, lambda ss, i, j: (strlit(ss[i+1:j-1]), j))

string_spec: LexState = [
    LexRule(escaped_char, lambda ss, i, j: (Strlit(ss[i+1]), j)),
    LexRule(content_char, lambda ss, i, j: (Strlit(ss[i]), j))
]

string_token = Scan(string_spec).scan_one()

def strlit(ss: str) -> Strlit:
    "use subsidiary scanner to transform string content"
    ls = []
    for s in make_scanner(string_token, ss):
        match s:
            case Strlit(value):
                ls.append(value)
            case _:
                raise Exception(f"Unexpected case: {s}")
    return Strlit("".join(ls))

js_spec: LexState = [
    LexRule(string_regexp("return"), lambda ss, i, j: (Return(), j)),
    LexRule(integer_literal, lambda ss, i, j: (Intlit(int(ss[i:j])), j)),
    LexRule(identifier, lambda ss, i, j: (Ident(ss[i:j]), j)),
    LexRule(white_space, lambda ss, i, j: js_token(ss, j)),
    LexRule(Symbol("("), lambda ss, i, j: (Lparen(), j)),
    LexRule(Symbol(")"), lambda ss, i, j: (Rparen(), j)),
    LexRule(Symbol("/"), lambda ss, i, j: (Slash(), j)),
    LexRule(string_literal, lambda ss, i, j: (strlit(ss[i+1:j-1]), j))
]

js_token: Callable[[str, Position], LexResult] = Scan(js_spec).scan_one()

def scan(ss: str) -> Iterator[Token]:
    return make_scanner(js_token, ss)

def example2() -> None:
    string = "return Segment (pi / 2)"
    print(f"Example 2 with \"{string}\"")
    sc = make_scanner(js_token, string)
    for ta in sc:
        print(ta)

def example3() -> None:
    string = "return Segment (pi / 2)"
    print(f"Example 3 with \"{string}\"")
    sc = make_scanner(js_token, 'return "foobar\\"..."')
    for ta in sc:
        print(ta)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Example 1 with '   42...'")
        print(js_token("   42...", 0))
        print("\nExample 2 with 'return Segment (pi / 2)'")
        sc = make_scanner(js_token, "return Segment (pi / 2)")
        for ta in sc:
            print(ta)
        print("\nExample 3 with 'return \"foobar\\\"...\"'")
        sc = make_scanner(js_token, "return \"foobar\\\"...\"")
        for ta in sc:
            print(ta)
        exit()
    print([x for x in scan(sys.argv[1])])
