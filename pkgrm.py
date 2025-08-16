#!/usr/bin/env python3
from __future__ import annotations

import argparse
import plistlib
import subprocess
from dataclasses import dataclass

from path import Path
from rich import print


@dataclass
class PathInfo:
    pth: Path
    is_dir: bool


def clean_preserving_cache(roots: list[Path], cache_file: str) -> None:
    for root in roots:
        if not isinstance(root, Path) or not root.is_dir():
            raise TypeError(f"Root path '{root}' is not a directory")
        if not isinstance(cache_file, str):
            raise TypeError(f"cache_file is not str it is {type(cache_file)}")
        for f in root.walk():
            if f.is_dir():
                continue
            if f.name != cache_file:
                f.remove()
        for d in root.walkdirs():
            pcf = d / cache_file
            if not pcf.exists():
                d.rmtree()


def pkg_info(pkg_name: str) -> dict:
    info = plistlib.loads(
        subprocess.run(
            ["pkgutil", "--export-plist", pkg_name],
            text=False,
            capture_output=True,
            check=True,
        ).stdout
    )
    return info


def pkg_paths(pkg_name) -> list[PathInfo]:
    pkg_pths: list[PathInfo] = []
    info = pkg_info(pkg_name)
    root_dir = Path(info["volume"]) / Path(info["install-location"])
    for fip, fii in info["paths"].items():
        pth = root_dir / Path(fip)
        pkg_pths.append(PathInfo(pth, False))
    if len(pkg_pths) == 0:
        raise ValueError(f"no paths for {pkg_name}")
    return pkg_pths


def list_pkgs(search: str | None = None) -> list[str]:
    pkgs = subprocess.run(
        ["pkgutil", "--pkgs"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.split("\n")
    if search is None:
        return pkgs
    else:
        return [p for p in pkgs if search.lower() in p.lower()]


def real_main(args: argparse.Namespace) -> None:
    if args.list:
        print("pkgs:")
        pkgs = list_pkgs()
        print("\n".join(pkgs))
    elif args.list_pkg_files:
        print("pkg_paths:")
        pkg_pths = pkg_paths(args.pkg)
        print(pkg_pths)
    elif args.info:
        print("pkg_info:")
        pkg_inf = pkg_info(args.pkg)
        print(pkg_inf)
    elif args.pkg is not None:
        print(f"rm: '{args.pkg}")


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='pkgrm - "Uninstall" macOS .pkg\'s')
    parser.add_argument("-p", "--pkg", help="Package to operate on")
    parser.add_argument("-l", "--list", action="store_true", help="list packages")
    parser.add_argument("-i", "--info", action="store_true", help="info for package")

    parser.add_argument("-L", "--list-pkg-files", action="store_true", help="list package files")
    return parser


def main() -> None:
    real_main(get_arg_parser().parse_args())


if __name__ == "__main__":
    main()
