from dataclasses import dataclass
from functools import reduce
from typing import cast, Iterable


"""
The first phase of a compiler is called `lexical analysis` implemented by a `scanner` or `lexer`.
It breaks a program into a sequence `lexemes`: 
    meaningful substrings of the input.
It also transforms lexemes into `tokens`: 
    symbolic representations of lexemes with some internalized information.

The classic, state-of-the-art method to specify lexemes is by regular expressions.
"""

"""
Representation of regular expressions.
"""

### types and classes ###


@dataclass(frozen=True)
class Regexp:
    """abstract class for AST of regular expressions"""

    pass


@dataclass(frozen=True)
class Null(Regexp):
    """empty set: {}"""

    pass


@dataclass(frozen=True)
class Epsilon(Regexp):
    """empty word: { "" }"""


@dataclass(frozen=True)
class Symbol(Regexp):
    """single symbol: { "a" }"""

    sym: str


@dataclass(frozen=True)
class Concat(Regexp):
    """concatenation: r1.r2"""

    left: Regexp
    right: Regexp


@dataclass(frozen=True)
class Alternative(Regexp):
    """alternative: r1|r2"""

    left: Regexp
    right: Regexp


@dataclass(frozen=True)
class Repeat(Regexp):
    """Kleene star: r*"""

    body: Regexp


"""
Smart constructors for regular expressions
goal: construct regexps in "normal form"
    * avoid Null() subexpressions
    * Epsilon() subexpressions as much as possible
    * nest concatenation and alternative to the right
"""

null = Null()
epsilon = Epsilon()


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
            return epsilon
        case Repeat(r1):
            return r
        case _:
            return Repeat(r)


### convinience ###


def optional(r: Regexp) -> Regexp:
    return alternative(r, epsilon)


def repeat_one(r: Regexp) -> Regexp:
    return concat(r, repeat(r))


def concat_list(rs: Iterable[Regexp]) -> Regexp:
    return reduce(lambda out, r: concat(out, r), rs, cast(Regexp, epsilon))


def alternative_list(rs: Iterable[Regexp]) -> Regexp:
    return reduce(lambda out, r: alternative(out, r), rs, cast(Regexp, null))


def char_range_regexp(c1: str, c2: str) -> Regexp:
    return alternative_list(map(Symbol, map(chr, range(ord(c1), ord(c2) + 1))))


def string_regexp(s: str) -> Regexp:
    return concat_list(map(Symbol, s))


def class_regexp(s: str) -> Regexp:
    return alternative_list(map(Symbol, s))


### properties and functions ###


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
        case Repeat(r):
            return True
    raise Exception(f"Unexpected case: {r}")


"""
The transition function of a (deterministic) finite automaton maps 
state `r0` and symbol `s` to the next state, say, `r1`.
If the state `r0` recognizes any words `w` that start with `s` (w[0] == s),
then state `r1` recognizes all those words `w` with the first letter removed (w[1:]).
This construction is called the `derivative` of a language by symbol `s`:

derivative(L, s) = { w[1:] | w in L and w[0] == s }

If L is the language recognized by regular expression `r0`, 
then we can effectively compute a regular expression for derivative(L, s)!
As follows:
"""


def after_symbol(s: str, r: Regexp) -> Regexp:
    """produces regexp after r consumes symbol s"""
    match r:
        case Null() | Epsilon():
            return null
        case Symbol(s_expected):
            return epsilon if s == s_expected else null
        case Alternative(r1, r2):
            return alternative(after_symbol(s, r1), after_symbol(s, r2))
        case Concat(r1, r2):
            return alternative(
                concat(after_symbol(s, r1), r2),
                after_symbol(s, r2) if accepts_empty(r1) else null,
            )
        case Repeat(r1):
            return concat(after_symbol(s, r1), Repeat(r1))
    raise Exception(f"Unexpected case: {r}")


"""
Executing regular expressions:

The standard method to 'execute' regular expressions is to transform them into finite automata.
Here we use a different method to execute them directly using `derivatives`.
This method uses regular expressions themselves as states of an automaton without constructing it.

We consider a regexp a final state if it accepts the empty word "".
This condition can be checked by a simple function on the regexp.
"""


def matches(r: Regexp, ss: str) -> bool:
    """determins whether string ss is in the language of the regular expression r"""
    i = 0
    while i < len(ss):
        r = after_symbol(ss[i], r)
        if is_null(r):
            return False
        i += 1
    # reached end of string
    return accepts_empty(r)
