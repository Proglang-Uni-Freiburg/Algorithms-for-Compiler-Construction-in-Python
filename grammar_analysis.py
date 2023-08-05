from grammar import *
from dataclasses import dataclass
from functools import partial, reduce
from typing import Callable, Optional, Generic, TypeVar, cast


### fixed-point algorithm ###


T = TypeVar("T")
Key = TypeVar("Key")
Value = TypeVar("Value")


# convinience
def map_eq(old: dict[Key, Value], current: dict[Key, Value]) -> bool:
    return all(old[k] == current[k] for k in old)


def fixed_point(current: T, update: Callable[[T], T], eq: Callable[[T, T], bool]) -> T:
    old: Optional[T] = None
    while old is None or not eq(old, current):
        old = current
        current = update(current)
    return current


### calculating first_1 sets ###


EmptySet = dict[NTS, bool]


def initial_empty(g: Grammar[NTS, TS]) -> EmptySet:
    return {n: False for n in g.nonterminals}


def derives_empty(fs: EmptySet, alpha: list[Symbol]) -> bool:
    match alpha:
        case []:
            return True
        case [NT(nt), *rest]:
            return fs[nt] and derives_empty(fs, rest)
        case [ts, *rest]:
            return False
    raise Exception(f"Unexpected case: {alpha}")


def update_empty(g: Grammar[NTS, TS], fs: EmptySet) -> EmptySet:
    fs = fs.copy()
    for n in g.nonterminals:
        fn = fs[n]
        for rule in g.productions_with_lhs(n):
            fn = fn or derives_empty(fs, list(rule.rhs))
        fs[n] = fn
    return fs


FirstSet = dict[NTS, frozenset[TS]]


def initial_first(g: Grammar[NTS, TS]) -> FirstSet:
    return {n: frozenset() for n in g.nonterminals}


def first(
    epsilon: TS, es: EmptySet, fs: FirstSet, alpha: list[Symbol]
) -> frozenset[TS]:
    match alpha:
        case [NT(nt), *rest] if es[nt]:
            return fs[nt] | first(epsilon, es, fs, rest)
        case [NT(nt), *rest]:
            return fs[nt]
        case [t, *rest]:
            return frozenset([cast(TS, t)])
        case []:
            return frozenset([epsilon])
    raise Exception(f"Unexpected case: {alpha}")


def update_first(
    g: Grammar[NTS, TS], epsilon: TS, es: EmptySet, fs: FirstSet
) -> FirstSet:
    fs = fs.copy()
    for n in g.nonterminals:
        fn = fs[n]
        for rule in g.productions_with_lhs(n):
            fn = fn | first(epsilon, es, fs, list(rule.rhs))
        fs[n] = fn
    return fs


def calculate_empty(g: Grammar[NTS, TS]) -> EmptySet:
    es = initial_empty(g)
    return fixed_point(es, partial(update_empty, g), map_eq)


def calculate_first(g: Grammar[NTS, TS], epsilon: TS, es: EmptySet) -> FirstSet:
    fs = initial_first(g)
    return fixed_point(fs, partial(update_first, g, epsilon, es), map_eq)


### calculating first_k/follow_k sets ###


Element = TypeVar("Element")  # semilattice element


@dataclass(frozen=True)
class GrammarAnalysis(Generic[NTS, TS, Element]):
    # abstract methods
    def bottom(self) -> Element:
        raise NotImplementedError

    def empty(self) -> Element:
        raise NotImplementedError

    def singleton(self, term: list[TS]) -> Element:
        raise NotImplementedError

    def join(self, x: Element, y: Element) -> Element:
        raise NotImplementedError

    def concat(self, x: Element, y: Element) -> Element:
        raise NotImplementedError

    def equal(self, x: Element, y: Element) -> bool:
        raise NotImplementedError

    def initial_analysis(self, g: Grammar[NTS, TS]) -> dict[NTS, Element]:
        raise NotImplementedError

    def update_analysis(
        self, g: Grammar[NTS, TS], fs: dict[NTS, Element]
    ) -> dict[NTS, Element]:
        raise NotImplementedError

    def rhs_analysis(self, fs: dict[NTS, Element], alpha: list[Symbol]) -> Element:
        r = self.empty()
        for sym in alpha:
            match sym:
                case NT(nt):
                    r = self.concat(r, fs[nt])
                case ts:
                    r = self.concat(r, self.singleton([ts]))
        return r

    def run(self, g: Grammar[NTS, TS]) -> dict[NTS, Element]:
        initial_map = self.initial_analysis(g)
        update_map = partial(self.update_analysis, g)
        return fixed_point(initial_map, update_map, map_eq)


Lookaheads = frozenset[tuple[TS, ...]]


# convinience for printing str instantiated Lookaheads
pretty_string_lookaheads = lambda sets: str(
    {
        key: {reduce(lambda x, y: x + y, v, "") for v in value}
        for key, value in sets.items()
    }
)


@dataclass(frozen=True)
class FirstKAnalysis(GrammarAnalysis[NTS, TS, Lookaheads]):
    k: int

    def bottom(self):
        return frozenset([])

    def empty(self):
        return frozenset([()])

    def singleton(self, term):
        return frozenset([tuple(term)])

    def join(self, sl1, sl2):
        return sl1 | sl2

    def concat(self, x, y):
        return frozenset([(sx + sy)[: self.k] for sx in x for sy in y])

    def equal(self, x, y):
        return x == y

    def initial_analysis(self, g):
        return {n: self.bottom() for n in g.nonterminals}

    def update_analysis(self, g, fs):
        fs = fs.copy()
        for rule in g.rules:
            match rule:
                case Production(nt, alpha):
                    fs[nt] = self.join(self.rhs_analysis(fs, alpha), fs[nt])
        return fs


@dataclass(frozen=True)
class FollowKAnalysis(FirstKAnalysis[NTS, TS]):
    first_k: dict[NTS, Lookaheads]

    def initial_analysis(self, g):
        r = super().initial_analysis(g)
        r[g.start] = self.empty()
        return r

    def update_analysis(self, g, fs):
        fs = fs.copy()
        for rule in g.rules:
            match rule:
                case Production(nt, alpha):
                    for i in range(len(alpha)):
                        match alpha[i]:
                            case NT(n):
                                rst = self.rhs_analysis(self.first_k, alpha[i + 1 :])
                                fs[n] = self.join(fs[n], self.concat(rst, fs[nt]))
        return fs
