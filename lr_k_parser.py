from grammar import *
from grammar_analysis import *
from dataclasses import dataclass
from functools import partial
from typing import Callable, cast
from ll_k_parser import equality, token_equality
from lr_0_parser import is_final, State, Item, shift_item, can_shift, equality
from scanner import Token


### continuation based LR(k) parser ###


def compute_closure(
    g: Grammar[NTS, TS],
    k: int,
    first_k: Callable[[list[Symbol]], Lookaheads],
    state: State,
) -> State:
    closure: set[Item[NTS, TS]] = set()
    new_closure = set(state)
    while closure != new_closure:
        closure = new_closure.copy()
        for item in closure:
            match item.rhs_rest():
                case [NT(nt), *rest]:
                    for lookahead in first_k(rest + list(item.lookahead)):
                        for rule in g.productions_with_lhs(nt):
                            new_closure.add(Item(rule, 0, lookahead))
    return frozenset(new_closure)


def goto(
    g: Grammar[NTS, TS],
    k: int,
    first_k: Callable[[list[Symbol]], Lookaheads],
    state: State,
    symbol: Symbol,
    eq: Callable[[TS, TS], bool],
) -> State:
    return compute_closure(
        g,
        k,
        first_k,
        frozenset([shift_item(item) for item in state if can_shift(item, symbol, eq)]),
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
        frozenset([Item(rule, 0, ()) for rule in g.productions_with_lhs(g.start)]),
    )


def reducable_items(
    state: State, prefix: tuple[TS, ...], eq: Callable[[TS, TS], bool]
) -> list[Item[NTS, TS]]:
    items = []
    for item in state:
        if len(item.rhs_rest()) == 0 and len(item.lookahead) == len(prefix):
            if all(eq(l, p) for l, p in zip(item.lookahead, prefix)):
                items.append(item)
    return items


def nactive(state: State) -> int:
    return max(map(lambda item: len(item.rhs_start()), state), default=0)


def parse(
    g: Grammar[NTS, TS],
    k: int,
    inp: list[TS],
    # TS equality function (e.g. tokens need type equality other than strings)
    eq: Callable[[TS, TS], bool] = equality,
) -> tuple[bool, Any]:
    fika = FirstKAnalysis[NTS, TS](k)
    first_k_nt = fika.run(g)
    first_k = partial(fika.rhs_analysis, first_k_nt)
    # used to store sub parts of the current parse structure (e.g. an AST)
    constructs: list[Any] = []

    def rec_parse(
        state: State,  # we recursively assume that state is a closure
        continuations: list[Callable[[Symbol, list[TS]], bool]],
        inp: list[TS],
    ) -> bool:
        nonlocal constructs

        if is_final(g, state) and len(inp) == 0:
            return True

        def c0(
            symbol: Symbol,
            inp: list[TS],
        ) -> bool:
            next_state = goto(g, k, first_k, state, symbol, eq)
            return rec_parse(
                next_state, [c0] + continuations[: nactive(next_state) - 1], inp
            )

        shiftable = []
        if len(inp) > 0:
            shiftable = [item for item in state if can_shift(item, inp[0], eq)]
        reducable = cast(
            list[Item[NTS, TS]], reducable_items(state, tuple(inp[:k]), eq)
        )
        if len(reducable) + (shiftable != []) > 1:
            print("Grammar is not LR(" + str(k) + ")")
        if len(shiftable) > 0:
            # constructing the parse structure
            constructs = [inp[0]] + constructs
            # calling the continuation
            return c0(inp[0], inp[1:])
        if len(reducable) > 0:
            rule = reducable[0].rule
            # constructing the parse structure
            arity = len(rule.rhs)
            construct = (
                None  # default construct is None if rule.ext is None
                if rule.ext is None
                else rule.ext(*constructs[:arity][::-1])
            )
            constructs = [construct] + constructs[arity:]
            # calling the continuation
            return ([c0] + continuations)[len(rule.rhs)](NT(rule.lhs), inp)
        return False

    result = rec_parse(initial_state(g, k, first_k), [], inp)
    return result, constructs[0] if result else None


# convenience
def parse_from_string(g: Grammar[NTS, str], k: int, inp: str) -> tuple[bool, Any]:
    return parse(g, k, list(inp), equality)


# convenience
def parse_from_tokens(
    g: Grammar[NTS, Token], k: int, inp: list[Token]
) -> tuple[bool, Any]:
    return parse(g, k, inp, token_equality)
