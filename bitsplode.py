#!/usr/bin/env python3

import argparse
import sys

from path import Path


def real_main(args) -> int:
    assert args.in_file is not None
    assert args.out_file is not None
    in_buf = open(args.in_file, "rb").read()
    out_buf = bytearray(len(in_buf) * 8)
    for i, b in enumerate(in_buf):
        for j in range(8):
            out_buf[i * 8 + j] = b & 1
            b >>= 1
    open(args.out_file, "wb").write(out_buf)
    return 0


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="1 byte => 8 0/1 bytes")
    parser.add_argument("-i", "--in-file", required=True, type=Path, help="Input path")
    parser.add_argument("-o", "--out-file", required=True, type=Path, help="Output path")
    return parser


def main() -> int:
    return real_main(get_arg_parser().parse_args())


if __name__ == "__main__":
    sys.exit(main())
