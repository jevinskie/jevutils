#!/usr/bin/env python3
from __future__ import annotations

import argparse

from path import Path


def clean_preserving_cache(root: Path, cache_file: str) -> None:
    if not root.is_dir():
        raise TypeError(f"Root path '{root}' is not a directory")
    for f in root.walk():
        if f.is_dir():
            continue
        if f.name != cache_file:
            f.remove()
    for d in root.walkdirs():
        pcf = d / cache_file
        if not pcf.exists():
            d.rmtree()


def real_main(args: argparse.Namespace) -> None:
    dir_path: Path = args.directory
    clean_preserving_cache(dir_path, args.cache_file)


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="acrm - Clear out directory trees except for autoconf cache files"
    )
    parser.add_argument(
        "directory", type=Path, help="Directory to [[WARNING]] RECURSIVELY DELETE [[[WARNING]]]"
    )
    parser.add_argument("-C", "--cache-file", default="config.cache", help="config cache name")
    return parser


def main() -> None:
    real_main(get_arg_parser().parse_args())


if __name__ == "__main__":
    main()
