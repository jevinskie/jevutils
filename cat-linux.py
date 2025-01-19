#!/usr/bin/env python3

from path import Path


def do_want(p: Path) -> bool:
    # print(f"p: {p} suffix: {p.suffix}")
    if not p.is_file():
        return False
    if p.suffix != ".c" and p.suffix != ".h":
        return False
    return True


clf = open("../cat-linux.c", "wb")

for f in Path().walkfiles(do_want):
    with open(f, "rb") as inf:
        clf.write(inf.read())
