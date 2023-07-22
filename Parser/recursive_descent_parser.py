from grammar import *
from grammar_analysis import *
from dataclasses import dataclass
from functools import partial, reduce
from typing import Iterator, Optional, cast


### ineffective, nondeterministic top-down parser ###


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


def td_parse_from_string(g: Grammar[NTS, str], s: str) -> Iterator[list[str]]:
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


def calculate_empty(g: Grammar[NTS, TS]) -> EmptySet:
    es = initial_empty(g)
    return fixed_point(es, partial(update_empty, g))


def calculate_first(g: Grammar[NTS, TS], es: EmptySet) -> FirstSet:
    fs = initial_first(g)
    return fixed_point(fs, partial(update_first, g, es))


### LL(k) parser ###


def ll_k_accept(g: Grammar[NTS, TS], k: int, inp: list[TS]) -> Optional[list[TS]]:
    fika = FirstKAnalysis[NTS, TS](k)
    first_k_nt = fika.run(g)  # first_k for NT's
    first_k = partial(fika.rhs_analysis, first_k_nt)  # complete first_k function
    foka = FollowKAnalysis[NTS, TS](k, first_k_nt)
    follow_k = foka.run(g)

    def lookahead(rule: Production) -> frozenset[Symbol]:
        return fika.concat(first_k(rule.rhs), follow_k[rule.lhs])

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


def ll_k_parse_from_string(
    g: Grammar[NTS, str], k: int, inp: str
) -> tuple[Optional[str], str]:
    result = ll_k_accept(g, k, list(inp))
    if result is None:
        return None, inp
    return inp[: len(inp) - len(result)], "".join(result)
