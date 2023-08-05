### use pytest to test this file ###

from grammar import *
import test_scanner as ts
from ll_k_parser import parse_from_string, parse_from_tokens
from scanner import Token, Scan, make_scanner


def test_base_case(capfd):
    empty = Grammar[str, str](("S",), (), (), "S")
    assert not parse_from_string(empty, 0, "")
    assert not parse_from_string(empty, 0, "x")

    epsilon = Grammar[str, str](("S",), (), (Production("S", ()),), "S")
    assert parse_from_string(epsilon, 0, "")
    assert not parse_from_string(epsilon, 0, "x")

    single = Grammar[str, str](("S",), ("x",), (Production("S", ("x",)),), "S")
    assert not parse_from_string(single, 0, "")
    assert parse_from_string(single, 0, "x")
    assert not parse_from_string(single, 0, "xx")


recursive_grammar = Grammar[str, str](
    ("S", "T"),
    ("a", "b"),
    (
        Production("S", (NT("T"), NT("S"))),
        Production("S", ("a", NT("T"))),
        Production("T", ("b",)),
    ),
    "S",
)


def test_recursive(capfd):
    assert not parse_from_string(recursive_grammar, 1, "")
    assert not parse_from_string(recursive_grammar, 1, "ba")
    assert parse_from_string(recursive_grammar, 1, "ab")
    assert parse_from_string(recursive_grammar, 1, "bab")
    assert parse_from_string(recursive_grammar, 1, "bbab")
    assert not parse_from_string(recursive_grammar, 1, "bcab")
    assert not parse_from_string(recursive_grammar, 1, "bbabb")
    out, err = capfd.readouterr()
    assert "not LL(1)" not in out
    parse_from_string(recursive_grammar, 0, "bbab")
    out, err = capfd.readouterr()
    assert "not LL(0)" in out


Number = ts.Number(0)
Identifier = ts.Identifier("")
Operator = ts.Operator("")
Left = ts.Left()
Right = ts.Right()

complex_grammar = Grammar[str, Token](
    ("S", "Cont", "Arg", "Op"),
    (Number, Identifier, Operator, Left, Right),
    (
        Production("S", (NT("Arg"), NT("Cont"))),
        Production("Cont", (NT("Op"), NT("Arg"), NT("Cont"))),
        Production("Cont", ()),
        Production("Op", (Operator,)),
        Production("Arg", (Number,)),
        Production("Arg", (Identifier,)),
        Production("Arg", (Left, NT("S"), Right)),
    ),
    "S",
)


def test_complex(capfd):
    parse = lambda k, inp: parse_from_tokens(
        complex_grammar, k, list(make_scanner(ts.scan_complex, inp))
    )
    assert not parse(1, "")
    assert parse(1, "10 + hello")
    assert parse(1, "10 + hello - 0")
    assert parse(1, "10 + hello - (a - a)")
    assert parse(1, "0 * ((1 * (2)) * 3)")
    assert parse(1, "0*((1*(2))*3)")
    assert parse(1, "0*   (\t(1*\n(2))    \n *3)")
    assert parse(1, "(0 * ((1 * (2)) * 3))")
    assert not parse(1, "0 * ((1 * (2)) * 3) <=")
    assert not parse(1, "0 * ((1 * (2)) * 3) 4")
    assert not parse(1, "(0 * ((1 * (2)) * 3)")
    assert not parse(1, "(0 * ((1 ** (2)) * 3))")
    out, err = capfd.readouterr()
    assert "not LL(1)" not in out
    parse(0, "(0 * ((1 * (2)) * 3))")
    out, err = capfd.readouterr()
    assert "not LL(0)" in out
