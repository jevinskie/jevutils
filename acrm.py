#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Self

from anytree import NodeMixin, RenderTree
from attrs import define, field
from path import Path
from rich import print as rprint
from rich.pretty import pprint
from rich.traceback import install as rtinstall

rtinstall(show_locals=True)


def is_cached_file(p: Path) -> bool:
    if not p.is_file():
        return False
    return p.name == "config.cache"


@define(init=False, slots=False)
class PTree(NodeMixin):
    fspath: Path = field()
    cache_path: Path | None = field(default=None)

    def __init__(self, path: Path, parent: PTree | None, cache_path: Path | None = None) -> None:
        super().__init__()
        if cache_path is not None:
            if not cache_path.is_file():
                raise TypeError(f"CachedDir cache_path '{cache_path}' is not a file")
        self.fspath = path
        self.parent = parent
        self.cache_path = cache_path

    @property
    def cached(self) -> bool:
        return self.cache_path is not None

    @property
    def parts(self):
        return self.fspath.parts()

    @classmethod
    def from_cache_file(cls, cache_file: Path, root: Path) -> Self:
        if not cache_file.is_file():
            raise TypeError(f"CachedDir cache_file '{cache_file}' is not a file")
        dir_path = cache_file.parent
        dpp = dir_path.parent
        is_root = dir_path.samefile(root)
        return cls(
            dir_path,
            parent=cls.from_dir(dpp, root) if not is_root else None,
            cache_path=cache_file,
        )

    @classmethod
    def from_dir(cls, dir_path: Path, root: Path) -> Self:
        if not dir_path.is_dir():
            raise TypeError(f"CachedDir dir_path '{dir_path}' is not a directory")
        dpp = dir_path.parent
        cache_path = dir_path / "cached.dir"
        is_root = dir_path.samefile(root)
        if cache_path.exists() and cache_path.is_file():
            return cls(
                dir_path,
                parent=cls.from_dir(dpp, root) if not is_root else None,
                cache_path=cache_path,
            )
        else:
            return cls(dir_path, parent=cls.from_dir(dpp, root) if not is_root else None)

    def dump(self):
        for pre, fill, node in RenderTree(self):
            rprint(f"[yellow]{pre}[/]{node.name}")

    @property
    def name(self) -> str:
        return str(self.fspath.name)


def get_cached_dirs(root: Path) -> list[PTree]:
    if not root.is_dir():
        raise TypeError(f"Root path '{root}' is not a directory")
    root = root.absolute()
    cached_files: list[Path] = list(root.walkfiles(is_cached_file))  # type: ignore
    print("cached_files:")
    pprint(cached_files)
    return [PTree.from_cache_file(cf, root) for cf in cached_files]


def real_main(args: argparse.Namespace) -> None:
    dir_path: Path = args.directory
    cached_dirs = get_cached_dirs(dir_path)
    print("cached_dirs:")
    pprint(cached_dirs)
    for cd in cached_dirs:
        cd.dump()


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
