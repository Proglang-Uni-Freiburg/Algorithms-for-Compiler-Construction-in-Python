### use pytest to test this file ###

from regexp import *


def test_base_case():
    assert not matches(null, "")
    assert not matches(null, "a")

    assert matches(epsilon, "")
    assert not matches(epsilon, "a")

    assert matches(Symbol("a"), "a")
    assert not matches(Symbol("a"), "b")
    assert not matches(Symbol("a"), "aa")


def test_connectives():
    assert not matches(Concat(null, null), "")
    assert not matches(Concat(null, epsilon), "")
    assert not matches(Concat(Symbol("a"), null), "a")
    assert matches(Concat(epsilon, Symbol("a")), "a")
    assert matches(Concat(epsilon, epsilon), "")
    assert matches(Concat(Symbol("a"), Symbol("b")), "ab")
    assert not matches(Concat(Symbol("a"), Symbol("b")), "ba")

    assert not matches(Alternative(null, null), "")
    assert matches(Alternative(null, epsilon), "")
    assert matches(Alternative(Symbol("a"), null), "a")
    assert matches(Alternative(epsilon, Symbol("a")), "a")
    assert matches(Alternative(epsilon, Symbol("a")), "")
    assert matches(Alternative(Symbol("a"), Symbol("b")), "a")
    assert matches(Alternative(Symbol("a"), Symbol("b")), "b")
    assert not matches(Alternative(Symbol("a"), Symbol("b")), "ab")

    assert matches(Repeat(null), "")
    assert not matches(Repeat(null), "a")
    assert matches(Repeat(epsilon), "")
    assert not matches(Repeat(epsilon), "a")
    assert matches(Repeat(Symbol("a")), "a")
    assert matches(Repeat(Symbol("a")), "aaaa")
    assert matches(Repeat(Symbol("a")), "")
    assert not matches(Repeat(Symbol("a")), "b")
    assert not matches(Repeat(Symbol("a")), "aaaab")


def test_constructors():
    assert concat(null, null) == null
    assert concat(null, epsilon) == null
    assert concat(Symbol("a"), null) == null
    assert concat(Symbol("a"), epsilon) == Symbol("a")
    assert concat(concat(Symbol("a"), Symbol("b")), Symbol("c")) == Concat(
        Symbol("a"), Concat(Symbol("b"), Symbol("c"))
    )

    assert alternative(null, null) == null
    assert alternative(null, epsilon) == epsilon
    assert alternative(Symbol("a"), null) == Symbol("a")
    assert alternative(Symbol("a"), epsilon) == Alternative(Symbol("a"), epsilon)
    assert alternative(
        alternative(Symbol("a"), Symbol("b")), Symbol("c")
    ) == Alternative(Symbol("a"), Alternative(Symbol("b"), Symbol("c")))

    assert repeat(null) == epsilon
    assert repeat(epsilon) == epsilon
    assert repeat(Symbol("a")) == Repeat(Symbol("a"))
    assert repeat(repeat(Symbol("a"))) == Repeat(Symbol("a"))


digit = char_range_regexp("0", "9")
number = alternative(digit, concat(char_range_regexp("1", "9"), repeat_one(digit)))
alphabet = alternative(char_range_regexp("a", "z"), char_range_regexp("A", "Z"))
identifier = concat(alphabet, repeat(alternative(alphabet, digit)))
operator = class_regexp("+-*/")
relation = alternative_list(map(string_regexp, "<= >= == !=".split()))
left = Symbol("(")
right = Symbol(")")
end = Symbol(";")
if_keyword = string_regexp("if")
then_keyword = string_regexp("then")
else_keyword = string_regexp("else")
return_keyword = string_regexp("return")
print_keyword = string_regexp("print")
assign_keyword = string_regexp(":=")
white_space = repeat_one(class_regexp(" \t\n"))


def test_complex_case():
    # print(if identifiert relation number then identifiert else identifier operator number)
    lst = [
        print_keyword,
        left,
        if_keyword,
        identifier,
        relation,
        number,
        then_keyword,
        identifier,
        else_keyword,
        identifier,
        operator,
        number,
        right,
        end,
    ]
    ignore = optional(white_space)
    pattern = [ignore]
    for elt in lst:
        pattern += [elt, ignore]
    pattern = concat_list(pattern)
    assert matches(pattern, "print(if a >= 1 then a else a + 1);")
    assert matches(pattern, "print(if abc0 != 1 then efg1 else hij2 - 1);")
    assert matches(pattern, "print(if abc == 123 then efg else hij / 0);")
    assert matches(pattern, "print (   if   a >= 1   then a   else a + 1 \t ) \n ;")
    assert matches(pattern, "print(ifa >= 1thena elsea + 1);")
    assert matches(pattern, "print(ifa >= 1thenaelsea + 1);")
    assert not matches(pattern, "print(ifa >= 1thenelsea + 1);")
    assert not matches(pattern, "pri nt(if a >= 1 then a else a + 1);")
    assert not matches(pattern, "print(if 1aa >= 1 then a else a + 1);")
    assert not matches(pattern, "print(if a >= 1 then a else a ! 1);")
    assert not matches(pattern, "print(if a >= 1 else a then a - 1);")
    assert not matches(pattern, "print(if a + 1 then a else a - 1);")
    assert not matches(pattern, "(if a >= 1 then a else a + 1);")
    assert not matches(pattern, "print if a >= 1 then a else a + 1;")
    assert not matches(pattern, "print(if a >= 1 then a else a + 1)")
