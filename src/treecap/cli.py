"""treecap CLI — print a directory tree, capping entries shown per folder.

Unlike `tree --filelimit`, which hides a directory entirely once it has too
many entries, treecap always recurses but caps the *display* per directory,
collapsing the overflow into a "... (N more)" line.
"""
import argparse
import os
import sys

from . import __version__

# Directories we never descend into by default.
DEFAULT_SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def list_entries(path, show_all, skip):
    try:
        entries = sorted(
            os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())
        )
    except (PermissionError, FileNotFoundError):
        return []
    out = []
    for e in entries:
        if not show_all and e.name.startswith("."):
            continue
        if e.is_dir() and e.name in skip:
            continue
        out.append(e)
    return out


def walk(path, prefix, width, max_depth, depth, show_all, skip):
    if max_depth is not None and depth >= max_depth:
        return
    entries = list_entries(path, show_all, skip)
    shown = entries if width is None else entries[:width]
    hidden = len(entries) - len(shown)

    for i, e in enumerate(shown):
        last = (i == len(shown) - 1) and hidden == 0
        connector = "└── " if last else "├── "
        print(prefix + connector + e.name + ("/" if e.is_dir() else ""))
        if e.is_dir():
            extension = "    " if last else "│   "
            walk(e.path, prefix + extension, width, max_depth,
                 depth + 1, show_all, skip)

    if hidden > 0:
        print(prefix + f"└── ... ({hidden} more)")


def build_parser():
    p = argparse.ArgumentParser(
        prog="treecap",
        description="A directory tree that caps how many entries are shown "
                    "per folder (the rest collapse into '... (N more)').",
    )
    p.add_argument("root", nargs="?", default=".",
                   help="directory to walk (default: current dir)")
    p.add_argument("-W", "--width", type=int, default=5, metavar="N",
                   help="max entries shown per directory (default: 5; "
                        "use 0 for unlimited)")
    p.add_argument("-L", "--level", type=int, default=None, metavar="DEPTH",
                   help="max display depth (default: unlimited)")
    p.add_argument("-a", "--all", action="store_true",
                   help="include hidden files/dirs (dotfiles)")
    p.add_argument("--no-skip", action="store_true",
                   help="don't skip .git/node_modules/__pycache__/.venv")
    p.add_argument("--version", action="version",
                   version=f"%(prog)s {__version__}")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    width = None if args.width == 0 else args.width
    skip = set() if args.no_skip else DEFAULT_SKIP

    print(args.root.rstrip("/") + "/")
    try:
        walk(args.root, "", width, args.level, 0, args.all, skip)
    except BrokenPipeError:  # e.g. piped into `head`
        try:
            sys.stdout.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
