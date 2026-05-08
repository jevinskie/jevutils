#!/usr/bin/env python3
from __future__ import annotations

import argparse

from path import Path
from transformers import AutoTokenizer


def get_files(paths: list[Path]) -> set[Path]:
    files: list[Path] = []
    for pth in paths:
        if pth.is_dir():
            files += pth.files()
        elif pth.is_file():
            files.append(pth)
        else:
            raise ValueError(f"must be a file or directory: '{pth}'")
    return set(files)


def count_tokens(paths: list[Path], model: str) -> None:
    files = get_files(paths)
    tokenizer = AutoTokenizer.from_pretrained(model)
    ntok = 0
    for f in files:
        with open(f) as fh:
            fstr = fh.read()
            toks = tokenizer(fstr)
            ntok += len(toks["input_ids"])
    print(f"num_tokens: {ntok}")


def real_main(args: argparse.Namespace) -> None:
    paths: list[Path] = args.paths
    count_tokens(paths, args.model)


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tokc - count model tokens in files")
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        metavar="files | directories",
        help="Files or directories to count tokens over",
    )
    parser.add_argument(
        "-m", "--model", default="unsloth/Qwen3-0.6B", help="huggingface model name"
    )
    return parser


def main() -> None:
    real_main(get_arg_parser().parse_args())


if __name__ == "__main__":
    main()
