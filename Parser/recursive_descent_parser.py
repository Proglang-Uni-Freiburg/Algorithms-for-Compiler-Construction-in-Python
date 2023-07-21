from grammar import *
from dataclasses import dataclass
from functools import partial, reduce
from typing import Any, Callable, Iterator, Optional, Generic, TypeVar, Union, cast


### ineffective, nondeterministic parser ###


def td_parse(
    g: Grammar[NTS, TS], alpha: list[Symbol], inp: list[TS]
) -> Iterator[list[TS]]:
    match alpha:
        case []:
            yield inp
        case [NT(nt), *rest_alpha]:
            for rule in g.productions_with_lhs(nt):
                for rest_inp in td_parse(g, rule.rhs, inp):
                    yield from td_parse(g, rest_alpha, rest_inp)
        case [ts, *rest_alpha]:
            if inp and ts == inp[0]:
                yield from td_parse(g, rest_alpha, inp[1:])


def parse_from_string(g: Grammar[NTS, str], s: str) -> Iterator[list[str]]:
    return td_parse(g, [NT(g.start)], list(s))


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


def update_empty(g: Grammar[NTS, TS], fs: EmptySet) -> None:
    for n in g.nonterminals:
        fn = fs[n]
        for rule in g.productions_with_lhs(n):
            fn = fn or derives_empty(fs, rule.rhs)
        fs[n] = fn


FirstSet = dict[NTS, frozenset[TS]]


def initial_first(g: Grammar[NTS, TS]) -> FirstSet:
    return {n: frozenset() for n in g.nonterminals}


def first(es: EmptySet, fs: FirstSet, alpha: list[Symbol]) -> frozenset[TS]:
    match alpha:
        case [NT(nt), *rest] if es[nt]:
            return fs[nt] | first(es, fs, rest)
        case [NT(nt), *rest]:
            return fs[nt]
        case [t, *rest]:
            return frozenset([cast(TS, t)])
        case []:
            return frozenset([cast(TS, "")])
    raise Exception(f"Unexpected case: {alpha}")


def update_first(g: Grammar[NTS, TS], es: EmptySet, fs: FirstSet):
    for n in g.nonterminals:
        fn = fs[n]
        for rule in g.productions_with_lhs(n):
            fn = fn | first(es, fs, rule.rhs)
        fs[n] = fn


Key = TypeVar("Key")
Value = TypeVar("Value")


def fixed_point(
    current_map: dict[Key, Value], update: Callable[[dict[Key, Value]], None]
) -> dict[Key, Value]:
    next_map = None
    while next_map is None or any(current_map[k] != next_map[k] for k in current_map):
        next_map = current_map
        current_map = current_map.copy()
        update(current_map)
    return current_map


def calculate_empty(g: Grammar[NTS, TS]) -> EmptySet:
    es = initial_empty(g)
    return fixed_point(es, partial(update_empty, g))


def calculate_first(g: Grammar[NTS, TS], es: EmptySet) -> FirstSet:
    fs = initial_first(g)
    return fixed_point(fs, partial(update_first, g, es))


### calculating first_k/follow_k sets ###


Element = TypeVar("Element")  # semilattice element


@dataclass(frozen=True)
class GrammarAnalysis(Generic[NTS, TS, Element]):
    # abstract semilattice methods
    def bottom(self) -> Element:
        raise NotImplementedError

    def empty(self) -> Element:
        raise NotImplementedError

    def singleton(self, term: tuple[TS]) -> Element:
        raise NotImplementedError

    def join(self, x: Element, y: Element) -> Element:
        raise NotImplementedError

    def concat(self, x: Element, y: Element) -> Element:
        raise NotImplementedError

    def equal(self, x: Element, y: Element) -> bool:
        raise NotImplementedError

    def initial_analysis(self, g: Grammar[NTS, TS]) -> dict[NTS, Element]:
        raise NotImplementedError

    def update_analysis(self, g: Grammar[NTS, TS], fs: dict[NTS, Element]):
        raise NotImplementedError

    # reusable analysis methods
    def rhs_analysis(self, fs: dict[NTS, Element], alpha: list[Symbol]):
        r = self.empty()
        for sym in alpha:
            match sym:
                case NT(nt):
                    r = self.concat(r, fs[nt])
                case ts:
                    r = self.concat(r, self.singleton((ts,)))
        return r

    def run(self, g: Grammar[NTS, TS]) -> dict[NTS, Element]:
        initial_map = self.initial_analysis(g)
        update_map = partial(self.update_analysis, g)
        return fixed_point(initial_map, update_map)


@dataclass(frozen=True)
class First_K_Analysis(GrammarAnalysis[NTS, TS, Element]):
    k: int

    def bottom(self):
        return frozenset([])

    def empty(self):
        return frozenset([()])

    def singleton(self, term):
        return frozenset([term])

    def join(self, sl1, sl2):
        return sl1 | sl2

    def concat(self, x, y):
        return frozenset([(sx + sy)[: self.k] for sx in x for sy in y])

    def equal(self, x, y):
        return x == y

    def initial_analysis(self, g):
        return {n: self.bottom() for n in g.nonterminals}

    def update_analysis(self, g, fs):
        for rule in g.rules:
            match rule:
                case Production(nt, alpha):
                    fs[nt] = self.join(self.rhs_analysis(fs, alpha), fs[nt])


@dataclass(frozen=True)
class Follow_K_Analysis(First_K_Analysis[NTS, TS, Element]):
    first_k: dict[NTS, Element]

    def initial_analysis(self, g):
        r = super().initial_analysis(g)
        r[g.start] = self.empty()
        return r

    def update_analysis(self, g, fs):
        for rule in g.rules:
            match rule:
                case Production(nt, alpha):
                    for i in range(len(alpha)):
                        match alpha[i]:
                            case NT(n):
                                rst = self.rhs_analysis(self.first_k, alpha[i + 1 :])
                                fs[n] = self.join(fs[n], self.concat(rst, fs[nt]))


### LL(k) parser ###


def accept(g: Grammar[NTS, TS], k: int, inp: list[TS]) -> Optional[list[TS]]:
    fika = First_K_Analysis[NTS, TS, frozenset[tuple[TS]]](k)
    first_k = fika.run(g)
    foka = Follow_K_Analysis[NTS, TS, frozenset[tuple[TS]]](k, first_k)
    follow_k = foka.run(g)

    def lookahead(rule: Production) -> frozenset[Symbol]:
        return fika.concat(fika.rhs_analysis(first_k, rule.rhs), follow_k[rule.lhs])

    def accept_symbol(sym: Symbol, inp: list[TS]) -> Optional[list[TS]]:
        match sym:
            case NT(nt):
                prefix = tuple(inp[:k])
                candidates = [
                    rule
                    for rule in g.productions_with_lhs(nt)
                    if prefix in lookahead(rule)
                ]
                if len(candidates) > 1:
                    print("Grammar is not LL(" + str(k) + ")")
                if len(candidates) > 0:
                    return accept_list(candidates[0].rhs, inp)
            case t:
                if inp[:1] == [t]:
                    return inp[1:]
        return None

    def accept_list(alpha: list[Symbol], inp: list[TS]) -> Optional[list[TS]]:
        for sym in alpha:
            new_inp = accept_symbol(sym, inp)
            if new_inp is None:
                return None
            inp = new_inp
        return inp

    return accept_symbol(NT(g.start), inp)


def accept_from_string(
    g: Grammar[NTS, str], k: int, inp: str
) -> tuple[Optional[str], str]:
    result = accept(g, k, list(inp))
    if result is None:
        return None, inp
    return inp[:len(inp)-len(result)], "".join(result)
