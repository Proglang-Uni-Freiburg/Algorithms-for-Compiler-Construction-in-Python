from grammar import *
from grammar_analysis import *
from dataclasses import dataclass
from functools import partial
from typing import Callable, cast
from lr_0_parser import is_final, State, Item


### continuation based LR(k) parser ###


def compute_closure(
    g: Grammar[NTS, TS],
    k: int,
    first_k: Callable[[list[Symbol]], Lookaheads],
    state: State,
) -> State:
    closure = set(state)
    new_closure: set[Item[NTS, TS]] = set()
    while closure != new_closure:
        new_closure = closure.copy()
        for item in closure:
            match item.rhs_rest():
                case [NT(nt), *rest]:
                    for lookahead in first_k(rest + list(item.lookahead)):
                        for rule in g.productions_with_lhs(nt):
                            new_closure.add(Item(rule, 0, lookahead))
    return frozenset(closure)


def goto(
    g: Grammar[NTS, TS],
    k: int,
    first_k: Callable[[list[Symbol]], Lookaheads],
    state: State,
    symbol: Symbol,
) -> State:
    return compute_closure(
        g,
        k,
        first_k,
        frozenset([item.shift() for item in state if item.can_shift(symbol)]),
    )


def initial_state(
    g: Grammar[NTS, TS], k: int, first_k: Callable[[list[Symbol]], Lookaheads]
) -> State:
    rules = g.productions_with_lhs(g.start)
    if len(rules) != 1:
        raise Exception("Grammar is not start-separated! (use function in grammar.py)")
    return compute_closure(
        g,
        k,
        first_k,
        frozenset(
            [
                Item(rule, 0, cast(tuple[TS], ()))
                for rule in g.productions_with_lhs(g.start)
            ]
        ),
    )


def reducable_items(state: State, prefix: tuple[TS]) -> list[Item[NTS, TS]]:
    items = []
    for item in state:
        if len(item.rhs_rest()) == 0 and item.lookahead == prefix:
            items.append(item)
    return items


def next_terminals(state: State) -> frozenset[TS]:
    terminals: set[TS] = set()
    for item in state:
        match item.rhs_rest():
            case [ts, *rest] if not isinstance(ts, NT):
                terminals.add(ts)
    return frozenset(terminals)


def nactive(state: State) -> int:
    return max(map(lambda item: len(item.rhs_start()), state))


def parse(g: Grammar[NTS, TS], k: int, inp: list[TS]) -> bool:
    fika = FirstKAnalysis[NTS, TS](k)
    first_k_nt = fika.run(g)  # first_k for NT's
    first_k = partial(fika.rhs_analysis, first_k_nt)  # complete first_k function

    def rec_parse(
        state: State,  # we recursively assume that state is a closure
        continuations: list[Callable[[Symbol, list[TS]], bool]],
        inp: list[TS],
    ) -> bool:
        if is_final(g, state) and len(inp) == 0:
            return True

        def c0(symbol: Symbol, inp: list[TS]) -> bool:
            next_state = goto(g, k, first_k, state, symbol)
            return rec_parse(
                next_state, [c0] + continuations[: nactive(next_state)], inp
            )

        can_shift = len(inp) > 0 and inp[0] in next_terminals(state)
        reducable = reducable_items(state, cast(tuple[TS], tuple(inp[:k])))
        if len(reducable) + can_shift > 1:
            print("Grammar is not LR(" + str(k) + ")")
        if can_shift:
            return c0(inp[0], inp[1:])
        if len(reducable) > 0:
            return ([c0] + continuations)[len(reducable[0].rhs_rest())](
                NT(reducable[0].lhs), inp
            )
        return False

    return rec_parse(initial_state(g, k, first_k), [], inp)


# convenience
def parse_from_string(g: Grammar[NTS, str], k: int, inp: str) -> bool:
    return parse(g, k, list(inp))
