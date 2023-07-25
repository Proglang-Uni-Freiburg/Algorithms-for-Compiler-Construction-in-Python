from grammar import *
from grammar_analysis import *
from functools import partial
from typing import Optional


### LL(k) parser ###


def parse(g: Grammar[NTS, TS], k: int, inp: list[TS]) -> Optional[list[TS]]:
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
                    return accept_list(list(candidates[0].rhs), inp)
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


# convenience
def parse_from_string(
    g: Grammar[NTS, str], k: int, inp: str
) -> tuple[Optional[str], str]:
    result = parse(g, k, list(inp))
    if result is None:
        return None, inp
    return inp[: len(inp) - len(result)], "".join(result)
