#!/usr/bin/env python3

from rich import print as rprint

alnum: list[str] = []
printable: list[str] = []
to_escape_hand: list[str] = []

for i in range(0x80):
    s = chr(i)
    if s.isalnum():
        alnum.append(s)
    if s.isprintable():
        printable.append(s)
        if not s.isalnum():
            to_escape_hand.append(s)

rprint(f"alnum: {alnum}")
rprint(f"printable: {printable}")
rprint(f"to_escape_hand: {to_escape_hand}")
rprint(f"len(to_escape_hand): {len(to_escape_hand)}")
rprint(f"len(alnum): {len(alnum)}")

emap_print: dict[int, int] = {
    ord(k): ord(v)
    for k, v in {
        " ": "S",
        "\t": "T",
        "\n": "N",
        "\r": "R",
        "?": "W",
        "!": "E",
        "`": "t",
        '"': "Q",
        "'": "q",
        "#": "H",
        "$": "D",
        "%": "P",
        "&": "A",
        "(": "l",
        ")": "r",
        "{": "i",
        "}": "j",
        "[": "b",
        "]": "B",
        "*": "O",
        "+": "X",
        ",": "c",
        "-": "m",
        ".": "d",
        "/": "F",
        ":": "o",
        ";": "p",
        "<": "v",
        ">": "V",
        "=": "u",
        "@": "a",
        "\\": "s",
        "^": "C",
        "~": "w",
        "|": "I",
        "_": "_",
    }.items()
}

for k, v in emap_print.items():
    assert 0 <= k <= 0xFF
    assert 0 <= v <= 0xFF

print_set: set[int] = {ord(s) for s in printable}
nonprint_set: set[int] = set(range(0x100)).difference(print_set)

nonprintable: list[int] = list(sorted(nonprint_set))

emap_nonprint: dict[int, int] = {}

for k, v in emap_nonprint:
    assert 0 <= k <= 0xFF
    assert 0 <= v <= 0xFF


for k, v in emap_print.items():
    if not chr(v).isalnum():
        print(
            f"bad emap_print mapping: {k:#04x} '{chr(k)}' -> {v:#04x} '{chr(v)}' '{chr(v)}' is not alnum"
        )


rprint(f"nonprintable: {nonprintable}")
rprint(f"len(nonprintable): {len(nonprintable)}")


rprint(f"emap_print: {emap_print}")
rprint(f"len(emap_print): {len(emap_print)}")
rprint(f"len(set(emap_print.keys()): {len(set(emap_print.keys()))}")
rprint(f"len(set(emap_print.values()): {len(set(emap_print.values()))}")

print_enc_tbl: list[str] = ["'#'"] * 0x80
for i in range(len(print_enc_tbl)):
    if i in emap_print:
        print_enc_tbl[i] = f"'\\x{emap_print[i]:02x}'"

enctab = "uint8_t print_enc_tbl[0x80] = {" + ", ".join(print_enc_tbl) + "};"
print(enctab)
