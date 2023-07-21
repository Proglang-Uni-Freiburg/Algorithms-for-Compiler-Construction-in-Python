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
class Production(Generic[NTS]):
    lhs: NTS
    rhs: list[Symbol]
    ext: Any = None


@dataclass(frozen=True)
class Grammar(Generic[NTS, TS]):
    nonterminals: list[NTS]
    terminals: list[TS]
    rules: list[Production]
    start: NTS

    def productions_with_lhs(self, nts: NTS) -> list[Production]:
        return [rule for rule in self.rules if rule.lhs == nts]


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
