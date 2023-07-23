from dataclasses import dataclass
from typing import TypeVar, Any, Union, Generic


### context free grammars ###


TS = TypeVar("TS")
NTS = TypeVar("NTS", str, int)


@dataclass(frozen=True)
class NT(Generic[NTS]):
    nt: NTS


Symbol = Union[NT[NTS], TS]


@dataclass(frozen=True)
class Production(Generic[NTS, TS]):
    lhs: NTS
    rhs: list[Symbol]
    ext: Any = None


@dataclass(frozen=True)
class Grammar(Generic[NTS, TS]):
    nonterminals: list[NTS]
    terminals: list[TS]
    rules: list[Production[NTS, TS]]
    start: NTS

    def productions_with_lhs(self, nts: NTS) -> list[Production]:
        return [rule for rule in self.rules if rule.lhs == nts]


def start_separated(g: Grammar[NTS, TS], new_start: NTS) -> Grammar[NTS, TS]:
    return Grammar(
        g.nonterminals.copy(),
        g.terminals.copy(),
        g.rules + [Production(new_start, [g.start], lambda x: x)],
        new_start,
    )


### abstract syntax for arithmetic expressions ###


@dataclass(frozen=True)
class AST:
    pass


@dataclass(frozen=True)
class BinOp(AST):
    left: AST
    binop: str
    right: AST


@dataclass(frozen=True)
class Var(AST):
    name: str


@dataclass(frozen=True)
class Constant(AST):
    val: int
