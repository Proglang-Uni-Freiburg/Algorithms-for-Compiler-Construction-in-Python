from grammar import *
from grammar_analysis import *
from recursive_descent_parser import *
import sys

### left-recurive example grammar ###

expr_grammar = Grammar[str, str](
    ["T", "E", "F"],
    ["x", "2", "(", ")", "+", "*"],
    [
        Production("T", [NT("E")], lambda e: e),
        Production("T", [NT("T"), "+", NT("E")], lambda t, e: BinOp(t, "+", e)),
        Production("E", [NT("F")], lambda f: f),
        Production("E", [NT("E"), "*", NT("F")], lambda e, f: BinOp(e, "*", f)),
        Production("F", ["x"], lambda: Var("x")),
        Production("F", ["2"], lambda: Constant(2)),
        Production("F", ["(", NT("T"), ")"], lambda t: t),
    ],
    "T",
)

### non-left-recursive equivalent of expr_grammar ###

expr_grammar_ = Grammar[str, str](
    ["T", "T'", "E", "E'", "F"],
    ["x", "2", "(", ")", "+", "*"],
    [
        Production("T", [NT("E"), NT("T'")]),
        Production("T'", ["+", NT("E"), NT("T'")]),
        Production("T'", []),
        Production("E", [NT("F"), NT("E'")]),
        Production("E'", ["*", NT("F"), NT("E'")]),
        Production("E'", []),
        Production("F", ["x"]),
        Production("F", ["2"]),
        Production("F", ["(", NT("T"), ")"]),
    ],
    "T",
)


### expr_grammar specific parser ###


def td_parse_T(inp: str) -> Iterator[str]:
    # 1st production
    yield from td_parse_E(inp)
    # 2nd production
    for inp1 in td_parse_T(inp):
        if inp1[:1] == "+":
            yield from td_parse_E(inp1[1:])


def td_parse_E(inp: str) -> Iterator[str]:
    # 1st production
    yield from td_parse_F(inp)
    # 2nd production
    for inp1 in td_parse_E(inp):
        if inp1[:1] == "*":
            yield from td_parse_F(inp1[1:])


def td_parse_F(inp: str) -> Iterator[str]:
    match inp[:1]:
        case "x":
            yield inp[1:]
        case "2":
            yield inp[1:]
        case "(":
            for rest_inp in td_parse_E(inp[1:]):
                match rest_inp[:1]:
                    case ")":
                        yield rest_inp[1:]


### first_1 sets calculation for expr_grammar_ ###


pretty = lambda sets: {
    key: {reduce(lambda x, y: x + y, v, "") for v in value}
    for key, value in sets.items()
}
es = calculate_empty(expr_grammar_)
fs = pretty(calculate_first(expr_grammar_, es))


### first_1 sets calculation for expr_grammar_ using general method###


first_1_analysis = First_K_Analysis[str, str, frozenset[tuple[str]]](1)
first_1 = pretty(first_1_analysis.run(expr_grammar_))


### using the LL(k) parser on expr_grammar_ ###


def accept_expr(inp: str) -> tuple[Optional[str], str]:
    return accept_from_string(expr_grammar_, 1, inp)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("first_1 sets of expr_grammar_:")
        print(fs)
        print("\nfirst_1 sets of expr_grammar_ (using general method):")
        print(first_1)
        exit()
    arg = sys.argv[1]
    result = accept_expr(arg)
    print(f"Accepted '{result[0]}' with rest '{result[1]}'")
