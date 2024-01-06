#!/usr/bin/env python3

import plistlib
import shutil
import subprocess
import sys
from typing import Callable

from rich import print


def run_cmd(*args, log: bool = False, **kwargs) -> str:
    args = (*args,)
    if log:
        print(f"Running: {' '.join(map(str, args))}", file=sys.stderr)
    r = subprocess.run(list(map(str, args)), capture_output=True, **kwargs)
    if r.returncode != 0:
        sys.stderr.buffer.write(r.stdout)
        sys.stderr.buffer.write(r.stderr)
        raise subprocess.CalledProcessError(r.returncode, args, r.stdout, r.stderr)
    try:
        r.out = r.stdout.decode()
    except UnicodeDecodeError:
        pass
    return r


def gen_cmd(bin_name: str) -> Callable:
    bin_path = shutil.which(bin_name)
    assert bin_path is not None
    return lambda *args, **kwargs: run_cmd(bin_path, *args, **kwargs)


java_home = gen_cmd("/usr/libexec/java_home")


def main() -> int:
    java_plist_xml = java_home("-X").out.encode()
    java_plist = plistlib.loads(java_plist_xml, fmt=plistlib.FMT_XML)
    print(java_plist)
    # java_selections: dict[tuple[Rational, bool], tuple[Path, str]] = {}
    for jvm in java_plist:
        # ver_str = jvm["JVMPlatformVersion"]
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
