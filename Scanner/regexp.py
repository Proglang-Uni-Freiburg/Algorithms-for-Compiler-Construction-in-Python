from dataclasses import dataclass
from functools import reduce
from typing import cast, Iterable

#####################
# Types and Classes #
#####################

@dataclass
class Regexp:
    """abstract class for AST of regular expressions"""
    pass

@dataclass
class Null (Regexp):
    """empty set: {}"""
    pass

@dataclass
class Epsilon (Regexp):
    """empty word: { "" }"""

@dataclass
class Symbol (Regexp):
    """single symbol: { "a" }"""
    sym: str

@dataclass
class Concat(Regexp):
    """concatenation: r1.r2"""
    left: Regexp
    right: Regexp

@dataclass
class Alternative(Regexp):
    """alternative: r1|r2"""
    left: Regexp
    right: Regexp

@dataclass
class Repeat(Regexp):
    """Kleene star: r*"""
    body: Regexp

################
# Constructors #
################

def concat(r1: Regexp, r2: Regexp) -> Regexp:
    match (r1, r2):
        case (Null(), _) | (_, Null()):
            return Null()
        case (Epsilon(), _):
            return r2
        case (_, Epsilon()):
            return r1
        case (Concat(r11, r12), _):
            return Concat(r11, concat(r12, r2))
        case _:
            return Concat(r1, r2)

def alternative(r1: Regexp, r2: Regexp) -> Regexp:
    match (r1, r2):
        case (Null(), _):
            return r2
        case (_, Null()):
            return r1
        case (Alternative(r11, r12), _):
            return Alternative(r11, alternative(r12, r2))
        case _:
            return Alternative(r1, r2)

def repeat(r: Regexp) -> Regexp:
    match r:
        case Null() | Epsilon():
            return Epsilon()
        case Repeat(r1):
            return r
        case _:
            return Repeat(r)

def optional(r: Regexp) -> Regexp:
    return alternative(r, Epsilon())

def repeat_one(r: Regexp) -> Regexp:
    return concat(r, repeat(r))

def concat_list(rs: Iterable[Regexp]) -> Regexp:
    return reduce(lambda out, r: concat(out, r), rs, cast(Regexp, Epsilon()))

def alternative_list(rs : Iterable[Regexp]) -> Regexp:
    return reduce(lambda out, r: alternative(out, r), rs, cast(Regexp, Null()))

def after_symbol(s: str, r: Regexp) -> Regexp:
    """produces regexp after r consumes symbol s"""
    match r:
        case Null() | Epsilon():
            return Null()
        case Symbol(s_expected):
            return Epsilon() if s == s_expected else Null()
        case Alternative(r1, r2):
            return alternative(after_symbol(s, r1), after_symbol(s, r2))
        case Concat(r1, r2):
            return alternative(concat(after_symbol(s, r1), r2),
                   after_symbol(s, r2) if accepts_empty(r1) else Null())
        case Repeat(r1):
            return concat(after_symbol(s, r1), Repeat(r1))
    raise Exception("Unexpected case!")

##############
# Properties #
##############

def is_null(r: Regexp) -> bool:
    match r:
        case Null():
            return True
    return False

def accepts_empty(r: Regexp) -> bool:
    match r:
        case Null():
            return False
        case Epsilon():
            return True
        case Symbol(s):
            return False
        case Concat(r1, r2):
            return accepts_empty(r1) and accepts_empty(r2)
        case Alternative(r1, r2):
            return accepts_empty(r1) or accepts_empty(r2)
    raise Exception("Unexpected case!")

def matches(r: Regexp, ss: str) -> bool:
    i = 0
    while i < len(ss):
        r = after_symbol(ss[i], r)
        if is_null(r):
            return False
        i += 1
    # reached end of string
    return accepts_empty(r)
