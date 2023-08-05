from dataclasses import dataclass
from typing import TypeVar, Any, Union, Generic, Callable, Optional


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
    rhs: tuple[Symbol, ...]
    # should take len(rhs) arguments if present
    ext: Optional[Callable[..., Any]] = None


@dataclass(frozen=True)
class Grammar(Generic[NTS, TS]):
    nonterminals: tuple[NTS, ...]
    terminals: tuple[TS, ...]
    rules: tuple[Production[NTS, TS], ...]
    start: NTS

    def productions_with_lhs(self, nts: NTS) -> list[Production]:
        return [rule for rule in self.rules if rule.lhs == nts]


def start_separated(g: Grammar[NTS, TS], new_start: NTS) -> Grammar[NTS, TS]:
    new_production: Production[NTS, TS] = Production(new_start, (NT(g.start),))
    return Grammar(
        g.nonterminals + (new_start,),
        g.terminals,
        g.rules + (new_production,),
        new_start,
    )
