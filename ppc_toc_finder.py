#!/usr/bin/env python3

import argparse
import array
import logging

import lief
from path import Path
from rich import print

logger = logging.getLogger("ppc_toc")
log = logger.info
dbg = logger.debug


def find_potential_tocs_raw(bin_buf: bytes, base: int) -> list[int]:
    maybe_tocs: list[int] = []
    iread: set[int] = set()

    raw_len = len(bin_buf)
    quad_off = raw_len % 8
    if (raw_len == 0) or (quad_off != 0):
        bin_buf = bin_buf + bytes(8 - quad_off)
    # bswap_bin = bytearray(bin_buf)
    # for i in range(0, raw_len, 8):
    #     bswap_bin[i : i + 8] = reversed(bswap_bin[i : i + 8])

    arr = array.array("Q", bin_buf)
    arr.byteswap()
    alen = len(arr)

    first8_int = arr[0]
    print(
        f"base: {base:#018x} alen: {alen:6} first8: 0x{bin_buf[:8].hex()} first8_int: {first8_int:#018x} raw_len: {raw_len} % 8: {quad_off}"
    )
    if first8_int == base + 0x8000:
        maybe_tocs.append(base)

    for i in range(alen - (0x8000 // 8)):
        this_addr = base + (i * 8)
        mb_toc_addr = this_addr + 0x8000
        this_value = arr[i]
        # print(f"this_addr: {this_addr:#x}")
        if this_addr in (0x1DBCF8, 0x1E3CF8):
            print(
                f"i: {i:7d} this_addr: {this_addr:#x} mb_toc_addr: {mb_toc_addr:#x} this_value: {this_value:#018x}"
            )
        if mb_toc_addr == this_value:
            maybe_tocs.append(this_addr)
        iread.add(i)

    return maybe_tocs


def find_potential_tocs(bin_path: Path, base: int | None = None) -> list[int]:
    maybe_tocs: list[int] = []

    if base is not None:
        bin_buf = open(bin_path, "rb").read()
        maybe_tocs = find_potential_tocs_raw(bin_buf, base)
    else:
        bin_obj = lief.parse(str(bin_path))
        if bin_obj is None:
            raise ValueError(f"couldn't parse {bin_path}")
        for i, seg in enumerate(bin_obj.sections):
            print(f"i: {i} seg: {seg}")
            seg_va = seg.virtual_address
            seg_buf = bytes(seg.content)
            if seg.name == ".got":
                open("got-dump.bin", "wb").write(seg_buf)
            maybe_tocs += find_potential_tocs_raw(seg_buf, seg_va)

    return maybe_tocs


def real_main(args: argparse.Namespace) -> None:
    maybe_tocs = find_potential_tocs(args.binary, args.base)
    maybe_tocs_strs = [f"{a:#010x}" for a in maybe_tocs]
    print(f"maybe_tocs: {', '.join(maybe_tocs_strs)}")


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
