### use pytest to test this file ###

import pytest
from dataclasses import dataclass
from regexp import *
from scanner import *
import test_regexp as tr


@dataclass(frozen=True)
class Number(Token):
    value: int


@dataclass(frozen=True)
class Identifier(Token):
    value: str


@dataclass(frozen=True)
class Operator(Token):
    value: str


@dataclass(frozen=True)
class Relation(Token):
    value: str


@dataclass(frozen=True)
class Left(Token):
    pass


@dataclass(frozen=True)
class Right(Token):
    pass


@dataclass(frozen=True)
class End(Token):
    pass


@dataclass(frozen=True)
class If(Token):
    pass


@dataclass(frozen=True)
class Then(Token):
    pass


@dataclass(frozen=True)
class Else(Token):
    pass


@dataclass(frozen=True)
class Return(Token):
    pass


@dataclass(frozen=True)
class Print(Token):
    pass


@dataclass(frozen=True)
class Assign(Token):
    pass


@dataclass(frozen=True)
class WhiteSpace(Token):
    pass


def test_base_case():
    scan_nothing = Scan([])
    assert list(make_scanner(scan_nothing, "")) == []
    with pytest.raises(ScanError) as error_info:
        scan_nothing("", 0)
    with pytest.raises(ScanError) as error_info:
        list(make_scanner(scan_nothing, "a"))

    scan_one = Scan([LexRule(Symbol("a"), lambda ss, i, j: (Identifier(ss[i:j]), j))])
    assert list(make_scanner(scan_one, "")) == []
    assert list(make_scanner(scan_one, "a")) == [Identifier("a")]
    assert list(make_scanner(scan_one, "aa")) == [Identifier("a"), Identifier("a")]
    with pytest.raises(ScanError) as error_info:
        list(make_scanner(scan_one, "b"))


scan_complex: Scan = Scan(
    [
        LexRule(tr.left, lambda ss, i, j: (Left(), j)),
        LexRule(tr.right, lambda ss, i, j: (Right(), j)),
        LexRule(tr.end, lambda ss, i, j: (End(), j)),
        LexRule(tr.if_keyword, lambda ss, i, j: (If(), j)),
        LexRule(tr.then_keyword, lambda ss, i, j: (Then(), j)),
        LexRule(tr.else_keyword, lambda ss, i, j: (Else(), j)),
        LexRule(tr.return_keyword, lambda ss, i, j: (Return(), j)),
        LexRule(tr.print_keyword, lambda ss, i, j: (Print(), j)),
        LexRule(tr.assign_keyword, lambda ss, i, j: (Assign(), j)),
        LexRule(
            tr.white_space,
            lambda ss, i, j: scan_complex(ss, j) if len(ss) > j else (End(), j),
        ),
        LexRule(tr.number, lambda ss, i, j: (Number(int(ss[i:j])), j)),
        # order matters!
        LexRule(tr.identifier, lambda ss, i, j: (Identifier(ss[i:j]), j)),
        LexRule(tr.operator, lambda ss, i, j: (Operator(ss[i:j]), j)),
        LexRule(tr.relation, lambda ss, i, j: (Relation(ss[i:j]), j)),
    ]
)


def test_complex_case():
    assert list(make_scanner(scan_complex, "")) == []
    assert list(make_scanner(scan_complex, " ")) == [End()]
    assert list(make_scanner(scan_complex, "1")) == [Number(1)]
    assert list(make_scanner(scan_complex, "hello")) == [Identifier("hello")]
    assert list(make_scanner(scan_complex, " hello ")) == [Identifier("hello"), End()]
    assert list(make_scanner(scan_complex, "0 hello + <= return := if ( )")) == [
        Number(0),
        Identifier("hello"),
        Operator("+"),
        Relation("<="),
        Return(),
        Assign(),
        If(),
        Left(),
        Right(),
    ]
    assert list(
        make_scanner(scan_complex, "0 \n   hello + <= \t  return := \t  if\n\t( )")
    ) == [
        Number(0),
        Identifier("hello"),
        Operator("+"),
        Relation("<="),
        Return(),
        Assign(),
        If(),
        Left(),
        Right(),
    ]
    assert list(make_scanner(scan_complex, "0hello+<=return:=if()")) == [
        Number(0),
        Identifier("hello"),
        Operator("+"),
        Relation("<="),
        Return(),
        Assign(),
        If(),
        Left(),
        Right(),
    ]
    with pytest.raises(ScanError) as error_info:
        list(make_scanner(scan_complex, "!"))
