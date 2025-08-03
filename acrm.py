#!/usr/bin/env python3

import argparse

import anytree
from attrs import define, field
from path import Path
from rich import print
from rich.pretty import pprint


def is_cached_file(p: Path) -> bool:
    if not p.is_file():
        return False
    return p.name == "config.cache"


@define
class CachedDir(anytree.NodeMixin):
    fspath: Path = field()

    @fspath.validator  # type: ignore
    def _check_p(self, attr, p: Path):
        if not p.is_file():
            raise TypeError(f"CachedDir fspath '{p}' is not a file")

    def parts(self):
        return self.fspath.parts()


def get_cached_dirs(root: Path) -> list[CachedDir]:
    if not root.is_dir():
        raise TypeError(f"Root path '{root}' is not a directory")
    cached_files: list[Path] = list(root.walkfiles(is_cached_file))  # type: ignore
    print("cached_files:")
    pprint(cached_files)
    return [CachedDir(cf) for cf in cached_files]


def real_main(args: argparse.Namespace) -> None:
    dirpath: Path = args.directory
    cached_dirs = get_cached_dirs(dirpath)
    print("cached_dirs:")
    pprint(cached_dirs)


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="acrm - Clear out directory trees except for autoconf cache files"
    )
    parser.add_argument(
        "directory", type=Path, help="Directory to [[WARNING]] RECURSIVELY DELETE [[[WARNING]]]"
    )
    return parser


def main() -> None:
    real_main(get_arg_parser().parse_args())


if __name__ == "__main__":
    main()
