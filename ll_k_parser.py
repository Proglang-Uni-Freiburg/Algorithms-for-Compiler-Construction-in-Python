from grammar import *
from grammar_analysis import *
from scanner import Token
from functools import partial
from typing import Optional


### LL(k) parser ###


def equality(x: TS, y: TS) -> bool:
    return x == y


def token_equality(x: Token, y: Token) -> bool:
    return type(x) == type(y)


def parse(
    g: Grammar[NTS, TS], k: int, inp: list[TS], eq: Callable[[TS, TS], bool] = equality
) -> bool:
    fika = FirstKAnalysis[NTS, TS](k)
    first_k_nt = fika.run(g)  # first_k for NT's
    first_k = partial(fika.rhs_analysis, first_k_nt)  # complete first_k function
    foka = FollowKAnalysis[NTS, TS](k, first_k_nt)
    follow_k = foka.run(g)

    def lookahead(rule: Production) -> Lookaheads:
        return fika.concat(first_k(rule.rhs), follow_k[rule.lhs])

    def accept_symbol(sym: Symbol, inp: list[TS]) -> Optional[list[TS]]:
        match sym:
            case NT(nt):
                prefix = tuple(inp[:k])
                candidates = []
                # check if prefix matches one of the lookaheads of a rule
                for rule in g.productions_with_lhs(nt):
                    for la in lookahead(rule):
                        if len(la) == len(prefix):
                            if all(eq(l, p) for l, p in zip(la, prefix)):
                                candidates.append(rule)
                                break
                if len(candidates) > 1:
                    print("Grammar is not LL(" + str(k) + ")")
                if len(candidates) > 0:
                    return accept_list(list(candidates[0].rhs), inp)
            case t:
                if len(inp) > 0 and eq(t, inp[0]):
                    return inp[1:]
        return None

    def accept_list(alpha: list[Symbol], inp: list[TS]) -> Optional[list[TS]]:
        for sym in alpha:
            new_inp = accept_symbol(sym, inp)
            if new_inp is None:
                return None
            inp = new_inp
        return inp

    result = accept_symbol(NT(g.start), inp)
    # The parser can not be used for prefix acceptance because of cases where the length
    # of a lookahead of a rule is strictly less than the rest of the input and k.
    return result is not None and len(result) == 0


# convenience
def parse_from_string(g: Grammar[NTS, str], k: int, inp: str) -> bool:
    return parse(g, k, list(inp), equality)


# convenience
def parse_from_tokens(g: Grammar[NTS, Token], k: int, inp: list[Token]) -> bool:
    return parse(g, k, inp, token_equality)
