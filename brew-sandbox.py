#!/usr/bin/env python3

import os
import sys


def build_sandbox_policy(packages: list[str]) -> str:
    lines = [
        "(version 1)",
        "(allow default)",
        # '(deny file* (literal "/opt/homebrew"))',
        # '(deny file* (subpath "/opt/homebrew"))',
        # '(allow file-read* (literal "/opt/homebrew"))',
        '(deny file* (literal "/opt/homebrew/include"))',
        '(deny file* (subpath "/opt/homebrew/include"))',
        # '(allow (with report) file* (literal "/opt/homebrew/include"))',
        # '(allow (with report) file* (subpath "/opt/homebrew/include"))',
        # '(allow file-read* (literal "/opt/homebrew/bin"))',
        # '(allow file-read* (literal "/opt/homebrew/lib"))',
        # '(allow file-read* (literal "/opt/homebrew/opt"))',
        # '(allow file-read* (literal "/opt/homebrew/Cellar"))',
        # '(allow file-map-executable (subpath "/opt/homebrew"))',
        # '(allow file-read* (subpath "/opt/homebrew/bin"))',
        # '(allow file-read* (subpath "/opt/homebrew/lib"))',
        # '(allow file-read* (subpath "/opt/homebrew/opt/pcre"))',
        # '(allow file-read* (literal "/opt/homebrew/Cellar/pcre/8.45/lib"))',
        # '(allow file-read* (literal "/opt/homebrew/Cellar/pcre"))',
        # '(allow file-read* (literal "/opt/homebrew/Cellar/pcre/8.45"))',
        # '(allow file-read* (literal "/opt/homebrew/Cellar/pcre/8.45/lib"))',
        # '(allow file-read* (subpath "/opt/homebrew/Cellar/pcre/8.45/lib"))',
        # '(allow file-read* (regex ".*\.dylib"))',
        # '(allow file-map-executable (regex ".*\.dylib"))',
    ]
    for pkg in packages:
        # Note: subpath directive is quoted, but parentheses, etc. will parse fine when passed as one argument.
        brew_opt_path = f"/opt/homebrew/opt/{pkg}"
        brew_cellar_path = os.readlink(brew_opt_path)
        brew_cellar_path = os.path.join(os.path.dirname(brew_opt_path), brew_cellar_path)
        brew_cellar_path = os.path.abspath(brew_cellar_path)
        lines.append(f'(allow file-read* (literal "{brew_opt_path}"))')
        lines.append(f'(allow file-read* (literal "{os.path.dirname(brew_cellar_path)}"))')
        lines.append(f'(allow file-read* (literal "{brew_cellar_path}"))')
        lines.append(f'(allow file* (subpath "{brew_opt_path}"))')
        lines.append(f'(allow file* (subpath "{brew_cellar_path}"))')
    # Flatten into a single space-separated string
    print("\n".join(lines))
    return " ".join(lines)


def main() -> None:
    if "--" not in sys.argv:
        print(f"Usage: {sys.argv[0]} <packages...> -- <command...>", file=sys.stderr)
        sys.exit(1)

    dash_index = sys.argv.index("--")
    packages = sys.argv[1:dash_index]
    command = sys.argv[dash_index + 1 :]

    if not command:
        print("No command specified after --", file=sys.stderr)
        sys.exit(1)

    # Build the single-line sandbox policy
    policy_str = build_sandbox_policy(packages)

    # Execute sandbox-exec with inline policy, replacing this process
    os.execv("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", policy_str, *command])


if __name__ == "__main__":
    main()
