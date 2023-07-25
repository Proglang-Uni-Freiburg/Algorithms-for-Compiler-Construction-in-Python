from regexp import *

"""
⟨digit⟩ ::= 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
⟨hexdigit⟩ ::= ⟨digit⟩ | A | B | C | D | E | F | a | b | c | d | e | f 
⟨hexprefix⟩ ::= 0x | 0X
⟨sign⟩ ::= ⟨empty⟩ | -
⟨empty⟩ ::=
⟨integer-literal⟩ ::= ⟨sign⟩ ⟨digit⟩+ | ⟨sign⟩ ⟨hexprefix⟩ ⟨hexdigit⟩+
⟨letter⟩ ::= A | B | C | ...| Z | a | b | c | ...| z 
⟨identifier-start⟩ ::= ⟨letter⟩ | $ | _
⟨identifier-part⟩ ::= ⟨identifier-start⟩ | ⟨digit⟩ 
⟨identifier⟩ ::= ⟨identifier-start⟩ ⟨identifier-part⟩*
"""

digit = class_regexp("0123456789")
hexdigit = alternative(digit, class_regexp("ABCDEFabcdef"))
hexprefix = alternative(string_regexp("0x"), string_regexp("0X"))
sign = optional(Symbol("-"))
integer_literal = concat(sign, repeat_one(digit))
integer_literal_js = alternative(
    concat(sign, repeat_one(digit)),
    concat_list([sign, hexprefix, repeat_one(hexdigit)]),
)
lc_letter = alternative_list(map(Symbol, map(chr, range(ord("a"), ord("z") + 1))))
uc_letter = alternative_list(map(Symbol, map(chr, range(ord("A"), ord("Z") + 1))))
letter = alternative(lc_letter, uc_letter)
identifier_start = alternative_list([letter, Symbol("$"), Symbol("_")])
identifier_part = alternative(identifier_start, digit)
identifier = concat(identifier_start, repeat(identifier_part))

blank_characters = "\t "
line_end_characters = "\n\r"
white_space = repeat_one(class_regexp(blank_characters + line_end_characters))
