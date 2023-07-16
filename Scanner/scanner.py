from dataclasses import dataclass
from typing import Callable, Iterator
from regexp import *

@dataclass(frozen=True)
class Token:
    pass

Position = int
LexResult = tuple[Token, Position]
LexAction = Callable[[str, Position, Position], LexResult]

@dataclass(frozen=True)
class LexRule:
    re: Regexp
    action: LexAction

LexState = list[LexRule]

@dataclass(frozen=True)
class Match:
    action: LexAction
    final: Position

class ScanError (Exception):
    pass

def is_stuck(state: LexState) -> bool:
    return not state

def next_state(state: LexState, ss: str, i: int) -> LexState:
    return list(filter(lambda rule: not (is_null(rule.re)),
                       [LexRule(after_symbol(ss[i], rule.re), rule.action)
                       for rule in state]))

def matched_rules(state: LexState) -> LexState:
    return [rule for rule in state if accepts_empty(rule.re)]

@dataclass
class Scan:
    spec: LexState

    def scan_one(self) -> Callable[[str, Position], LexResult]:
        return lambda ss, i: self.scan_one_token(ss, i)

    def scan_one_token(self, ss: str, i: Position) -> LexResult:
        state = self.spec
        j = i
        last_match = None
        while j < len(ss) and not is_stuck(state):
            state = next_state(state, ss, j); j += 1
            all_matches = matched_rules(state)
            if all_matches:
                this_match = all_matches[0]
                last_match = Match(this_match.action, j)
        match last_match:
            case None:
                raise ScanError("no lexeme found:", ss[i:])
            case Match(action, final):
                return action(ss, i, final)
        raise ScanError("internal error: last_match=", last_match)

def make_scanner(scan_one: Callable[[str, Position], LexResult], ss: str) -> Iterator[Token]:
    i = 0
    while i < len(ss):
        (token, i) = scan_one(ss, i)
        yield token
