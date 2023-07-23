from grammar import *
from typing import Iterator


### ineffective, nondeterministic top-down parser ###


def parse(
    g: Grammar[NTS, TS], alpha: list[Symbol], inp: list[TS]
) -> Iterator[list[TS]]:
    match alpha:
        case []:
            yield inp
        case [NT(nt), *rest_alpha]:
            for rule in g.productions_with_lhs(nt):
                for rest_inp in parse(g, rule.rhs, inp):
                    yield from parse(g, rest_alpha, rest_inp)
        case [ts, *rest_alpha]:
            if inp and ts == inp[0]:
                yield from parse(g, rest_alpha, inp[1:])


# convenience
def parse_from_string(g: Grammar[NTS, str], s: str) -> Iterator[list[str]]:
    return parse(g, [NT(g.start)], list(s))
