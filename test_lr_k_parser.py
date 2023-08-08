### use pytest to test this file ###

from grammar import *
import test_scanner as ts
import test_ll_k_parser as tll
from lr_k_parser import parse_from_string, parse_from_tokens
from scanner import Token, Scan, make_scanner


def test_base_case(capfd):
    empty = start_separated(Grammar[str, str](("S",), (), (), "S"), "S'")
    assert not parse_from_string(empty, 0, "")[0]
    assert not parse_from_string(empty, 0, "x")[0]

    epsilon = start_separated(
        Grammar[str, str](("S",), (), (Production("S", ()),), "S"), "S'"
    )
    assert parse_from_string(epsilon, 0, "")[0]
    assert not parse_from_string(epsilon, 0, "x")[0]

    single = start_separated(
        Grammar[str, str](("S",), ("x",), (Production("S", ("x",)),), "S"), "S'"
    )
    assert not parse_from_string(single, 0, "")[0]
    assert parse_from_string(single, 0, "x")[0]
    assert not parse_from_string(single, 0, "xx")[0]


def test_recursive(capfd):
    recursive_grammar = start_separated(tll.recursive_grammar, "S'")
    assert not parse_from_string(recursive_grammar, 0, "")[0]
    assert not parse_from_string(recursive_grammar, 0, "ba")[0]
    assert parse_from_string(recursive_grammar, 0, "ab")[0]
    assert parse_from_string(recursive_grammar, 0, "bab")[0]
    assert parse_from_string(recursive_grammar, 0, "bbab")[0]
    assert not parse_from_string(recursive_grammar, 0, "bcab")[0]
    assert not parse_from_string(recursive_grammar, 0, "bbabb")[0]
    parse_from_string(recursive_grammar, 0, "bbab")
    out, err = capfd.readouterr()
    assert "not LR(0)" not in out


def test_complex(capfd):
    complex_grammar = start_separated(tll.complex_grammar, "S'")
    parse = lambda k, inp: parse_from_tokens(
        complex_grammar, k, list(make_scanner(ts.scan_complex, inp))
    )
    assert not parse(1, "")[0]
    assert parse(1, "10 + hello")[0]
    assert parse(1, "10 + hello - 0")[0]
    assert parse(1, "10 + hello - (a - a)")[0]
    assert parse(1, "0 * ((1 * (2)) * 3)")[0]
    assert parse(1, "0*((1*(2))*3)")[0]
    assert parse(1, "0*   (\t(1*\n(2))    \n *3)")[0]
    assert parse(1, "(0 * ((1 * (2)) * 3))")[0]
    assert not parse(1, "0 * ((1 * (2)) * 3) <=")[0]
    assert not parse(1, "0 * ((1 * (2)) * 3) 4")[0]
    assert not parse(1, "(0 * ((1 * (2)) * 3)")[0]
    assert not parse(1, "(0 * ((1 ** (2)) * 3))")[0]
    out, err = capfd.readouterr()
    assert "not LR(1)" not in out
    parse(0, "(0 * ((1 * (2)) * 3))")
    out, err = capfd.readouterr()
    assert "not LR(0)" in out


### abstract syntax  ###


@dataclass(frozen=True)
class AST:
    pass


@dataclass(frozen=True)
class Const(AST):
    value: int


@dataclass(frozen=True)
class Var(AST):
    value: str


@dataclass(frozen=True)
class BinOp(AST):
    left: AST
    op: str
    right: AST


@dataclass(frozen=True)
class BinRel(AST):
    left: AST
    rel: str
    right: AST


@dataclass(frozen=True)
class IfExp(AST):
    if_cond: AST
    then_exp: AST
    else_exp: AST


@dataclass(frozen=True)
class Ret(AST):
    exp: AST


@dataclass(frozen=True)
class Prnt(AST):
    exp: AST


@dataclass(frozen=True)
class Let(AST):
    var: str
    exp: AST


@dataclass(frozen=True)
class Module(AST):
    stmts: list[AST]


Number = ts.Number(0)
Identifier = ts.Identifier("")
Operator = ts.Operator("")
Relation = ts.Relation("")
Left = ts.Left()
Right = ts.Right()
End = ts.End()
If = ts.If()
Then = ts.Then()
Else = ts.Else()
Return = ts.Return()
Print = ts.Print()
Assign = ts.Assign()
WhiteSpace = ts.WhiteSpace()


complex_grammar = Grammar[str, Token](
    ("Module", "Stmt", "Exp"),
    (
        Number,
        Identifier,
        Operator,
        Relation,
        Left,
        Right,
        End,
        If,
        Then,
        Else,
        Return,
        Print,
        Assign,
        WhiteSpace,
    ),
    (
        Production(
            "Module", (NT("Stmt"), NT("Module")), lambda s, m: Module(s + m.stmts)
        ),
        Production("Module", (), lambda: Module([])),
        Production("Stmt", (End,), lambda end: []),
        Production("Stmt", (Print, NT("Exp"), End), lambda p, exp, end: [Prnt(exp)]),
        Production("Stmt", (Return, NT("Exp"), End), lambda r, exp, end: [Ret(exp)]),
        Production(
            "Stmt",
            (Identifier, Assign, NT("Exp"), End),
            lambda i, a, exp, end: [Let(i.value, exp)],
        ),
        Production("Exp", (Number,), lambda n: Const(n.value)),
        Production("Exp", (Identifier,), lambda i: Var(i.value)),
        Production(
            "Exp",
            (NT("Exp"), Operator, NT("Exp")),
            lambda e1, o, e2: BinOp(e1, o.value, e2),
        ),
        Production(
            "Exp",
            (NT("Exp"), Relation, NT("Exp")),
            lambda e1, r, e2: BinRel(e1, r.value, e2),
        ),
        Production(
            "Exp",
            (If, NT("Exp"), Then, NT("Exp"), Else, NT("Exp")),
            lambda i, e1, t, e2, e, e3: IfExp(e1, e2, e3),
        ),
        Production(
            "Exp",
            (Left, NT("Exp"), Right),
            lambda l, e, r: e,
        ),
    ),
    "Module",
)
complex_grammar = start_separated(complex_grammar, "S'")


def test_complex_ast(capfd):
    parse = lambda k, inp: parse_from_tokens(
        complex_grammar, k, list(make_scanner(ts.scan_complex, inp))
    )
    assert parse(1, "") == (True, Module([]))
    assert parse(1, "print hi;") == (True, Module([Prnt(Var("hi"))]))
    assert parse(1, "return 1;") == (True, Module([Ret(Const(1))]))
    assert parse(1, "hi := 1;") == (True, Module([Let("hi", Const(1))]))
    assert parse(1, "hi := 1;\nprint(hi + 1);") == (
        True,
        Module([Let("hi", Const(1)), Prnt(BinOp(Var("hi"), "+", Const(1)))]),
    )
    assert parse(1, "hi := if hi == 0 then 1 else 0;") == (
        True,
        Module(
            [Let("hi", IfExp(BinRel(Var("hi"), "==", Const(0)), Const(1), Const(0)))]
        ),
    )
    assert parse(1, "hi := if if hi == 0 then 0 else 1 then 1 else 0;") == (
        True,
        Module(
            [
                Let(
                    "hi",
                    IfExp(
                        IfExp(BinRel(Var("hi"), "==", Const(0)), Const(0), Const(1)),
                        Const(1),
                        Const(0),
                    ),
                )
            ]
        ),
    )
    assert parse(
        1, "hi := if if hi == 0 then 0 else 1 then if i then 0 else 1 else 0;"
    ) == (
        True,
        Module(
            [
                Let(
                    "hi",
                    IfExp(
                        IfExp(BinRel(Var("hi"), "==", Const(0)), Const(0), Const(1)),
                        IfExp(Var("i"), Const(0), Const(1)),
                        Const(0),
                    ),
                )
            ]
        ),
    )
    assert parse(1, "hi := if if hi == 0 then 0 else 1 then 1 else (0 * (1 / 2));") == (
        True,
        Module(
            [
                Let(
                    "hi",
                    IfExp(
                        IfExp(BinRel(Var("hi"), "==", Const(0)), Const(0), Const(1)),
                        Const(1),
                        BinOp(Const(0), "*", BinOp(Const(1), "/", Const(2))),
                    ),
                )
            ]
        ),
    )
    assert parse(1, "hi := if hi == 0 then 1 else if i then 1 else 0;") == (
        True,
        Module(
            [
                Let(
                    "hi",
                    IfExp(
                        BinRel(Var("hi"), "==", Const(0)),
                        Const(1),
                        IfExp(Var("i"), Const(1), Const(0)),
                    ),
                )
            ]
        ),
    )
    assert parse(1, "return 1 + (2 <= 3);") == (
        True,
        Module([Ret(BinOp(Const(1), "+", BinRel(Const(2), "<=", Const(3))))]),
    )
    assert parse(1, "    return 1 + (2 <= 3);    ") == (
        True,
        Module([Ret(BinOp(Const(1), "+", BinRel(Const(2), "<=", Const(3))))]),
    )
    assert parse(1, "return 1 + (2 <= 3);return 1+1;;;;") == (
        True,
        Module(
            [
                Ret(BinOp(Const(1), "+", BinRel(Const(2), "<=", Const(3)))),
                Ret(BinOp(Const(1), "+", Const(1))),
            ]
        ),
    )
    assert parse(1, "return (1 + 2) <= 3;") == (
        True,
        Module([Ret(BinRel(BinOp(Const(1), "+", Const(2)), "<=", Const(3)))]),
    )
    assert parse(1, "return((1)+(2))<=(3);") == (
        True,
        Module([Ret(BinRel(BinOp(Const(1), "+", Const(2)), "<=", Const(3)))]),
    )
    assert parse(1, "return((1)\n+(2\t))  <=   (3);") == (
        True,
        Module([Ret(BinRel(BinOp(Const(1), "+", Const(2)), "<=", Const(3)))]),
    )
    assert parse(1, "print hi") == (False, None)
    assert parse(1, "return 1 + (2 <= print 3);") == (False, None)
    assert parse(1, "return 1 + (2 <= 4 := 3);") == (False, None)
    assert parse(1, "return 1 + (2 <= 4));") == (False, None)
    assert parse(1, "return 1 ++ (2 <= 4);") == (False, None)
    assert parse(1, "return <= (2 + 4);") == (False, None)
    assert parse(1, "return 1 + (2 <= 3) return 1+1;;;;") == (False, None)
    assert parse(1, "return if i then if j then 0 else 1;") == (False, None)
    out, err = capfd.readouterr()
    assert "not LR(1)" not in out
    parse(0, "return (0 * ((1 * (2)) * 3))")
    out, err = capfd.readouterr()
    assert "not LR(0)" in out
