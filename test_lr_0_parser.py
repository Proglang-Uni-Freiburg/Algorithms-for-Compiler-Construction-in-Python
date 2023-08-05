### use pytest to test this file ###

from grammar import *
import test_scanner as ts
import test_ll_k_parser as tll
from lr_0_parser import parse_from_string, parse_from_tokens
from scanner import Token, Scan, make_scanner


def test_base_case(capfd):
    empty = start_separated(Grammar[str, str](("S",), (), (), "S"), "S'")
    assert not parse_from_string(empty, "")
    assert not parse_from_string(empty, "x")

    epsilon = start_separated(
        Grammar[str, str](("S",), (), (Production("S", ()),), "S"), "S'"
    )
    assert parse_from_string(epsilon, "")
    assert not parse_from_string(epsilon, "x")

    single = start_separated(
        Grammar[str, str](("S",), ("x",), (Production("S", ("x",)),), "S"), "S'"
    )
    assert not parse_from_string(single, "")
    assert parse_from_string(single, "x")
    assert not parse_from_string(single, "xx")


def test_recursive(capfd):
    recursive_grammar = start_separated(tll.recursive_grammar, "S'")
    assert not parse_from_string(recursive_grammar, "")
    assert not parse_from_string(recursive_grammar, "ba")
    assert parse_from_string(recursive_grammar, "ab")
    assert parse_from_string(recursive_grammar, "bab")
    assert parse_from_string(recursive_grammar, "bbab")
    assert not parse_from_string(recursive_grammar, "bcab")
    assert not parse_from_string(recursive_grammar, "bbabb")
    out, err = capfd.readouterr()
    assert "not LR(0)" not in out


def test_complex(capfd):
    complex_grammar = start_separated(tll.complex_grammar, "S'")
    parse = lambda inp: parse_from_tokens(
        complex_grammar, list(make_scanner(ts.scan_complex, inp))
    )
    assert parse("10 + hello")
    out, err = capfd.readouterr()
    assert "not LR(0)" in out
