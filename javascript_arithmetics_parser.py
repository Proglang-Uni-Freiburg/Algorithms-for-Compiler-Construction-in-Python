import sys
from grammar import *
from typing import Any
from javascript_scanner import *
from lr_k_parser import parse_from_tokens as lr_k_parse_from_tokens

### full lexer and parser based on the javascript literals ###
### and simple arithmetic operations ###

intlit = Intlit(0)
ident = Ident("")
binaryop = BinaryOp("")
lparen = Lparen()
rparen = Rparen()
ret = Return()

grammar = Grammar[str, Token](
    ("S", "T", "F"),
    (intlit, ident, binaryop, lparen, rparen),
    (
        Production("S", (NT("T"),), lambda t: t),
        Production(
            "S",
            (
                ret,
                NT("T"),
            ),
            lambda r, t: Ret(t),
        ),
        Production("T", (NT("F"),), lambda f: f),
        Production(
            "T", (NT("T"), binaryop, NT("F")), lambda t, b, f: BinOp(t, b.op, f)
        ),
        Production("F", (ident,), lambda i: Var(i.name)),
        Production("F", (intlit,), lambda i: Constant(i.value)),
        Production("F", (lparen, NT("T"), rparen), lambda l, t, r: t),
    ),
    "S",
)


def lex_and_parse(inp: str) -> tuple[bool, Any]:
    scan = list(make_scanner(js_token, inp))
    start_separated_grammar = start_separated(grammar, "S'")
    result = lr_k_parse_from_tokens(start_separated_grammar, 1, scan)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        arg = "return (xpos+ypos) / 2"
    else:
        arg = sys.argv[1]
    result = lex_and_parse(arg)
    print(f"LR(k)-parsed '{result[0]}' with parse tree '{result[1]}'")
