#!/usr/bin/env python3

import argparse
import array

from elftools.elf.elffile import ELFFile
from path import Path
from rich import print


def find_potential_tocs(binary: bytes) -> list[int]:
    maybe_tocs: list[int] = []
    iread: set[int] = set()

    raw_len = len(binary)
    quad_off = raw_len % 8
    print(f"raw_len: {raw_len} % 8: {quad_off}")
    if raw_len:
        binary = binary + bytes(8 - quad_off)

    bswap_bin = bytearray(binary)
    for i in range(0, raw_len, 8):
        bswap_bin[i : i + 8] = reversed(bswap_bin[i : i + 8])

    arr = array.array("Q", bswap_bin)
    alen = len(arr)
    print(f"len(arr): {alen}")

    for i in range(alen - (0x8000 // 8)):
        ai = arr[i]
        io = i + 0x8000
        if ((i * 8) + 0x10000) in (0x1DBCF8, 0x1E3CF8):
            print(f"i: {i} ai: {ai:#018x} io: {io:#018x}")
        if ai == io:
            maybe_tocs.append(i * 8)
        iread.add(i)

    return maybe_tocs


def real_main(args: argparse.Namespace) -> None:
    efb = open(args.binary, "rb").read()
    efb_len = len(efb)
    print(f"efb_len: {efb_len:#x} {efb_len}")
    efh = open(args.binary, "rb")
    ef = ELFFile(efh)
    print(ef)
    print(list(ef.iter_sections()))
    base: int = args.base
    if args.base is None:
        base = 0
    print(f"base: {base:#018x}")
    # maybe_tocs = find_potential_tocs(efb)
    # print(f"maybe_tocs: {maybe_tocs}")


def parse_hex_int_str(s: str) -> int:
    return int(s, 16)


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ppc_toc_finder - Find TOC value for PPC(64) binaries"
    )
    parser.add_argument("binary", type=Path, help="Binary file")
    parser.add_argument(
        "-b", "--base", required=False, type=parse_hex_int_str, help="Base address (hex)"
    )
    return parser


def main() -> None:
    real_main(get_arg_parser().parse_args())


if __name__ == "__main__":
    main()
