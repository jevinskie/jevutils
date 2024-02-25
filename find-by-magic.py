#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path

import magic

m = magic.Magic(raw=True)


def PathDir(string):
    path = Path(string)
    if not path.is_dir():
        msg = f"{path} is not a directory"
        raise argparse.ArgumentTypeError(msg)
    return path


def is_match(args, pth):
    ftype = m.from_buffer(open(pth, "rb").read(4096))
    if args.regexes is not None:
        for pat in args.regexes:
            if re.search(pat, ftype) is not None:
                return True
    if args.ftypes is not None:
        if ftype in args.ftypes:
            return True
    return False


def main(args):
    for pdir in args.dirs:
        for pth in pdir.glob("**/*"):
            if not pth.is_file():
                continue
            if args.exts is not None and pth.suffix not in args.exts:
                continue
            if is_match(args, pth):
                print(str(pth))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find files using libmagic")
    parser.add_argument("dirs", metavar="DIR", type=PathDir, nargs="+", help="Directory to search")
    parser.add_argument(
        "-t",
        "--type",
        metavar="TYPE",
        dest="ftypes",
        type=str,
        action="append",
        help="File type to find",
    )
    parser.add_argument(
        "-r",
        "--regex",
        metavar="REGEX",
        dest="regexes",
        type=lambda x: re.compile(x, flags=re.I),
        action="append",
        help="File type to find",
    )
    parser.add_argument(
        "-e",
        "--ext",
        metavar="EXTENSION",
        dest="exts",
        type=str,
        action="append",
        help="Required extension",
    )
    args = parser.parse_args()
    sys.exit(main(args))
