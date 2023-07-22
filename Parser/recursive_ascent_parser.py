from grammar import *
from grammar_analysis import *
from dataclasses import dataclass
from functools import partial
from typing import Callable, cast


### items for recursive-ascent-parsers ###


@dataclass(frozen=True)
class Item(Generic[NTS, TS]):
    rule: Production[NTS, TS]
    position: int
    lookahead: tuple[TS]

    def lhs(self) -> NTS:
        return self.rule.lhs

    def rhs(self) -> list[Symbol]:
        return self.rule.rhs

    def rhs_start(self) -> list[Symbol]:
        return self.rule.rhs[: self.position]

    def rhs_rest(self) -> list[Symbol]:
        return self.rule.rhs[self.position :]

    def can_shift(self, symbol: Symbol) -> bool:
        return (
            self.position < len(self.rule.rhs)
            and self.rule.rhs[self.position] == symbol
        )

    def shift(self) -> Item:
        return Item(self.rule, self.position + 1, self.lookahead)


State = frozenset[Item[NTS, TS]]


### stack based LR(0) parser ###


def lr_0_accept(g: Grammar[NTS, TS], inp: list[TS]) -> bool:
    rules = g.productions_with_lhs(g.start)
    if len(rules) != 1:
        raise Exception("Grammar is not start-separated! (use function in grammar.py)")

    def compute_closure(state: State) -> State:
        closure = set(state)
        new_closure: set[Item[NTS, TS]] = set()
        while closure != new_closure:
            new_closure = closure.copy()
            for item in closure:
                match item.rhs_rest():
                    case [NT(nt), *rest]:
                        for rule in g.productions_with_lhs(nt):
                            new_closure.add(Item(rule, 0, cast(tuple[TS], ())))
        return frozenset(closure)

    def goto(state: State, symbol: Symbol) -> State:
        return compute_closure(
            frozenset([item.shift() for item in state if item.can_shift(symbol)])
        )

    def initial_state() -> State:
        return compute_closure(frozenset([Item(rules[0], 0, cast(tuple[TS], ()))]))

    def reducable_items(state: State) -> list[Item[NTS, TS]]:
        items = []
        for item in state:
            if len(item.rhs_rest()):
                items.append(item)
        return items

    def is_final(state: State) -> bool:
        return rules[0] in [item.rule for item in state]

    def parse(stack: list[State], inp: list[TS]) -> bool:
        state = stack[-1]
        if is_final(state) and len(stack) == 1 and len(inp) == 0:
            return True

        shiftable = []
        if len(inp) > 0:
            shiftable = [item for item in state if item.can_shift(inp[0])]
        reducable = reducable_items(state)
        if len(reducable) + len(shiftable) > 1:
            print("Grammar is not LR(0)")
        if len(shiftable) > 0:
            return shift(shiftable[0].rhs_rest()[0], stack, inp[1:])
        if len(reducable) > 0:
            new_stack = stack[: len(stack) - len(reducable[0].rhs_start())]
            return shift(reducable[0].lhs, new_stack, inp)
        return False

    def shift(symbol: Symbol, stack: list[State], inp: list[TS]) -> bool:
        state = stack[-1]
        return parse(stack + [goto(state, symbol)], inp)

    return parse([initial_state()], inp)


def next_terminals(state: State) -> frozenset[TS]:
    terminals: set[TS] = set()
    for item in state:
        match item.rhs_rest():
            case [ts, *rest] if not isinstance(ts, NT):
                terminals.add(ts)
    return frozenset(terminals)


def nactive(state: State) -> int:
    return max(map(lambda item: len(item.rhs_start()), state))


### continuation based LR(k) parser ###


def lr_k_accept(g: Grammar[NTS, TS], k: int, inp: list[TS]) -> bool:
    fika = FirstKAnalysis[NTS, TS](k)
    first_k_nt = fika.run(g)  # first_k for NT's
    first_k = partial(fika.rhs_analysis, first_k_nt)  # complete first_k function

    def compute_closure(state: State) -> State:
        closure = set(state)
        new_closure: set[Item[NTS, TS]] = set()
        while closure != new_closure:
            new_closure = closure.copy()
            for item in closure:
                match item.rhs_rest():
                    case [NT(nt), *rest]:
                        for lookahead in first_k(tuple(rest) + item.lookahead):
                            for rule in g.productions_with_lhs(nt):
                                new_closure.add(Item(rule, 0, lookahead))
        return frozenset(closure)

    def goto(state: State, symbol: Symbol) -> State:
        return compute_closure(
            frozenset([item.shift() for item in state if item.can_shift(symbol)])
        )

    def initial_state() -> State:
        return compute_closure(
            frozenset([Item(rule, 0, cast(tuple[TS], ())) for rule in g.productions_with_lhs(g.start)])
        )

    def reducable_items(state: State, prefix: tuple[TS]) -> list[Item[NTS, TS]]:
        items = []
        for item in state:
            if len(item.rhs_rest()) == 0 and item.lookahead == prefix:
                items.append(item)
        return items

    def is_final(items: State) -> bool:
        for item in items:
            if g.start == item.lhs and len(item.rhs_rest()) == 0:
                return True
        return False

    def parse(
        state: State,  # we recursively assume that state is a closure
        continuations: list[Callable[[Symbol, list[TS]], bool]],
        inp: list[TS],
    ) -> bool:
        if is_final(state) and len(inp) == 0:
            return True

        def c0(symbol: Symbol, inp: list[TS]) -> bool:
            next_state = goto(state, symbol)
            return parse(next_state, [c0] + continuations[: nactive(next_state)], inp)

        can_shift = len(inp) > 0 and inp[0] in next_terminals(state)
        reducable = reducable_items(state, cast(tuple[TS], tuple(inp[:k])))
        if len(reducable) + can_shift > 1:
            print("Grammar is not LR(" + str(k) + ")")
        if can_shift:
            return c0(inp[0], inp[1:])
        if len(reducable) > 0:
            return ([c0] + continuations)[len(reducable[0].rhs_rest())](NT(reducable[0].lhs), inp)
        return False

    return parse(initial_state(), [], inp)
