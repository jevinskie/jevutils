#!/usr/bin/env python3

import argparse

from elftools.elf.elffile import ELFFile
from path import Path
from rich import print


def real_main(args: argparse.Namespace) -> None:
    efh = open(args.binary, "rb")
    ef = ELFFile(efh)
    print(ef)
    print(list(ef.iter_sections()))


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ppc_toc_finder - Find TOC value for PPC(64) binaries"
    )
    parser.add_argument("binary", type=Path, help="Binary file")
    return parser


def main() -> None:
    real_main(get_arg_parser().parse_args())


if __name__ == "__main__":
    main()
