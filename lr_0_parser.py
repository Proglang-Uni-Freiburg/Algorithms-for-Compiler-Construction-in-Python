from grammar import *
from dataclasses import dataclass
from typing import cast


### items for recursive-ascent-parsers ###


@dataclass(frozen=True)
class Item(Generic[NTS, TS]):
    rule: Production[NTS, TS]
    position: int
    lookahead: tuple[TS, ...] = ()

    def lhs(self) -> NTS:
        return self.rule.lhs

    def rhs(self) -> list[Symbol]:
        return list(self.rule.rhs)

    def rhs_start(self) -> list[Symbol]:
        return list(self.rule.rhs[: self.position])

    def rhs_rest(self) -> list[Symbol]:
        return list(self.rule.rhs[self.position :])


def equality(x: TS, y: TS) -> bool:
    return x == y


def can_shift(item, symbol: Symbol, eq: Callable[[TS, TS], bool] = equality) -> bool:
    if item.position >= len(item.rule.rhs):
        return False
    rhs_symbol = item.rule.rhs[item.position]
    match (rhs_symbol, symbol):
        case (NT(nt1), NT(nt2)):
            return nt1 == nt2
        case (NT(nt), ts) | (ts, NT(nt)):
            return False
        case (ts1, ts2):
            return eq(ts1, cast(TS, ts2))
    raise Exception(f"Unexpected case: {(rhs_symbol, symbol)}")


def shift_item(item: Item) -> Item:
    return Item(item.rule, item.position + 1, item.lookahead)


### stack based LR(0) parser ###


State = frozenset[Item[NTS, TS]]


def compute_closure(g: Grammar[NTS, TS], state: State) -> State:
    closure: set[Item[NTS, TS]] = set()
    new_closure = set(state)
    while closure != new_closure:
        closure = new_closure.copy()
        for item in closure:
            match item.rhs_rest():
                case [NT(nt), *rest]:
                    for rule in g.productions_with_lhs(nt):
                        new_closure.add(Item(rule, 0))
    return frozenset(new_closure)


def goto(g: Grammar[NTS, TS], state: State, symbol: Symbol) -> State:
    return compute_closure(
        g, frozenset([shift_item(item) for item in state if can_shift(item, symbol)])
    )


def initial_state(g: Grammar[NTS, TS]) -> State:
    rules = g.productions_with_lhs(g.start)
    if len(rules) != 1:
        raise Exception("Grammar is not start-separated! (use function in grammar.py)")
    return compute_closure(g, frozenset([Item(rules[0], 0)]))


def reducable_items(state: State) -> list[Item[NTS, TS]]:
    items = []
    for item in state:
        if len(item.rhs_rest()) == 0:
            items.append(item)
    return items


def is_final(g: Grammar[NTS, TS], state: State) -> bool:
    for item in state:
        if g.start == item.lhs() and len(item.rhs_rest()) == 0:
            return True
    return False


def parse(g: Grammar[NTS, TS], inp: list[TS]) -> bool:
    def rec_parse(stack: list[State], inp: list[TS]) -> bool:
        state = stack[-1]
        # len(stack) == 2 because the starting rule item will be completed after exactly
        # one shift i.e. adding one additional state to the stack
        if is_final(g, state) and len(stack) == 2 and len(inp) == 0:
            return True

        shiftable = []
        if len(inp) > 0:
            shiftable = [item for item in state if can_shift(item, inp[0])]
        reducable: list[Item[NTS, TS]] = reducable_items(state)
        if len(reducable) + (shiftable != []) > 1:
            print("Grammar is not LR(0)")
        if len(shiftable) > 0:
            return shift(shiftable[0].rhs_rest()[0], stack, inp[1:])
        if len(reducable) > 0:
            new_stack = stack[: len(stack) - len(reducable[0].rhs_start())]
            return shift(NT(reducable[0].lhs()), new_stack, inp)
        return False

    def shift(symbol: Symbol, stack: list[State], inp: list[TS]) -> bool:
        state = stack[-1]
        return rec_parse(stack + [goto(g, state, symbol)], inp)

    return rec_parse([initial_state(g)], inp)


# convenience
def parse_from_string(g: Grammar[NTS, str], inp: str) -> bool:
    return parse(g, list(inp))
