"""treecap CLI — print a directory tree, capping entries shown per folder.

Unlike `tree --filelimit`, which hides a directory entirely once it has too
many entries, treecap always recurses but caps the *display* per directory,
collapsing the overflow into a "... (N more)" line.

The first layer (the root's direct children) is never capped tightly: it uses
a separate, generous `--top-width` so you always see the whole top level.

Three compression levels control how loose files are rendered:

  0  every entry on its own line (the classic tree)
  1  loose files in a folder collapse onto one comma-separated line
  2  like 1, plus a folder that contains *only* files is written inline
     in brackets:  name/ [a.py, b.py, c.py]

Defaults are read from ~/.treecap/settings.json (CLI flags override them);
`--save-config` writes the current options back to that file.
"""
import argparse
import json
import os
import sys

from . import __version__

# Directories we never descend into by default.
DEFAULT_SKIP = [".git", "node_modules", "__pycache__", ".venv", "venv"]

# Built-in defaults, lowest priority. Overridden by the settings file, which is
# in turn overridden by explicit command-line flags.
BUILTIN_DEFAULTS = {
    "width": 5,
    "top_width": 50,
    "level": None,
    "compress": 0,
    "all": False,
    "no_skip": False,
    "skip": list(DEFAULT_SKIP),
}

# Options that live in ~/.treecap/settings.json (everything but root/save flags).
CONFIG_KEYS = tuple(BUILTIN_DEFAULTS)


def settings_path():
    return os.path.join(os.path.expanduser("~"), ".treecap", "settings.json")


def load_settings():
    """Return the user's settings dict, or {} if there isn't a valid one."""
    try:
        with open(settings_path()) as f:
            data = json.load(f)
    except (FileNotFoundError, OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in CONFIG_KEYS}


def save_settings(config):
    path = settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


class Options:
    """Resolved, ready-to-render settings passed down the walk."""

    def __init__(self, cfg):
        self.width = None if cfg["width"] == 0 else cfg["width"]
        self.top_width = None if cfg["top_width"] == 0 else cfg["top_width"]
        self.level = cfg["level"]
        self.compress = cfg["compress"]
        self.all = cfg["all"]
        self.skip = set() if cfg["no_skip"] else set(cfg["skip"])

    def cap_for(self, depth):
        return self.top_width if depth == 0 else self.width


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


def join_names(names, cap):
    """Comma-join names, capping to `cap` with a trailing '... (N more)'."""
    if cap is not None and len(names) > cap:
        kept = names[:cap]
        return ", ".join(kept) + f", ... ({len(names) - cap} more)"
    return ", ".join(names)


def inline_dir(entry, opts):
    """Render a files-only directory inline:  name/ [a, b, c]  (compress 2)."""
    children = list_entries(entry.path, opts.all, opts.skip)
    names = [c.name for c in children]
    return f"{entry.name}/ [{join_names(names, opts.width)}]"


def only_files(entry, opts):
    """True if `entry` is a directory whose visible children are all files."""
    children = list_entries(entry.path, opts.all, opts.skip)
    return bool(children) and all(not c.is_dir() for c in children)


def inline_shown_files(entry, opts):
    """How many bracketed file names are actually visible for an inline dir."""
    n = len(list_entries(entry.path, opts.all, opts.skip))
    return n if opts.width is None else min(n, opts.width)


def walk(path, prefix, depth, opts):
    """Print the tree for `path`; return (dirs_shown, files_shown)."""
    if opts.level is not None and depth >= opts.level:
        return 0, 0
    entries = list_entries(path, opts.all, opts.skip)
    cap = opts.cap_for(depth)
    shown = entries if cap is None else entries[:cap]
    hidden = len(entries) - len(shown)

    # Build the list of rows for this directory. Each row is a (kind, payload)
    # tuple; kind is "dir", "inline", "files" or "more".
    rows = []
    if opts.compress == 0:
        rows.extend(("dir" if e.is_dir() else "file", e) for e in shown)
    else:
        dirs = [e for e in shown if e.is_dir()]
        files = [e for e in shown if not e.is_dir()]
        deeper_ok = opts.level is None or depth + 1 < opts.level
        for d in dirs:
            if opts.compress >= 2 and deeper_ok and only_files(d, opts):
                rows.append(("inline", d))
            else:
                rows.append(("dir", d))
        if files:
            rows.append(("files", files))
    if hidden > 0:
        rows.append(("more", hidden))

    sdirs = sfiles = 0
    for i, (kind, payload) in enumerate(rows):
        last = i == len(rows) - 1
        connector = "└── " if last else "├── "
        extension = "    " if last else "│   "
        if kind == "more":
            print(f"{prefix}{connector}... ({payload} more)")
        elif kind == "files":
            print(prefix + connector + join_names([f.name for f in payload], None))
            sfiles += len(payload)
        elif kind == "inline":
            print(prefix + connector + inline_dir(payload, opts))
            sdirs += 1
            sfiles += inline_shown_files(payload, opts)
        elif kind == "dir":
            print(prefix + connector + payload.name + "/")
            sdirs += 1
            d, f = walk(payload.path, prefix + extension, depth + 1, opts)
            sdirs += d
            sfiles += f
        else:  # file
            print(prefix + connector + payload.name)
            sfiles += 1
    return sdirs, sfiles


def count_tree(path, depth, opts):
    """Count (directories, files) in the tree, mirroring `walk`'s filters.

    Respects the same hidden/skip/level rules as the display walk, but ignores
    the per-directory display caps: it reports the true totals of the tree,
    not just the entries that fit on screen.
    """
    if opts.level is not None and depth >= opts.level:
        return 0, 0
    ndirs = nfiles = 0
    for e in list_entries(path, opts.all, opts.skip):
        if e.is_dir():
            ndirs += 1
            sub_dirs, sub_files = count_tree(e.path, depth + 1, opts)
            ndirs += sub_dirs
            nfiles += sub_files
        else:
            nfiles += 1
    return ndirs, nfiles


def summary_line(ndirs, nfiles):
    dir_word = "directory" if ndirs == 1 else "directories"
    file_word = "file" if nfiles == 1 else "files"
    return f"{ndirs} {dir_word}, {nfiles} {file_word}"


def build_parser():
    p = argparse.ArgumentParser(
        prog="treecap",
        description="A directory tree that caps how many entries are shown "
                    "per folder (the rest collapse into '... (N more)'). "
                    "Defaults come from ~/.treecap/settings.json.",
        argument_default=argparse.SUPPRESS,
    )
    p.add_argument("root", nargs="?", default=".",
                   help="directory to walk (default: current dir)")
    p.add_argument("-W", "--width", type=int, metavar="N",
                   help="max entries shown per directory below the top level "
                        "(default: 5; use 0 for unlimited)")
    p.add_argument("-T", "--top-width", type=int, metavar="N", dest="top_width",
                   help="max entries shown at the first/top level "
                        "(default: 50; use 0 for unlimited)")
    p.add_argument("-L", "--level", type=int, metavar="DEPTH",
                   help="max display depth (default: unlimited)")
    p.add_argument("-c", "--compress", type=int, metavar="LEVEL",
                   choices=(0, 1, 2),
                   help="compression: 0 = one entry per line (default); "
                        "1 = collapse loose files onto a comma line; "
                        "2 = also inline files-only folders as name/ [a, b]")
    p.add_argument("-a", "--all", action="store_true",
                   help="include hidden files/dirs (dotfiles)")
    p.add_argument("--no-skip", action="store_true", dest="no_skip",
                   help="don't skip .git/node_modules/__pycache__/.venv")
    p.add_argument("--save-config", action="store_true", dest="save_config",
                   help="write the current options to ~/.treecap/settings.json "
                        "and exit")
    p.add_argument("--version", action="version",
                   version=f"%(prog)s {__version__}")
    return p


def resolve_config(args):
    """Layer built-in defaults < settings file < explicit CLI flags."""
    cfg = dict(BUILTIN_DEFAULTS)
    cfg.update(load_settings())
    for key in CONFIG_KEYS:
        if hasattr(args, key):
            cfg[key] = getattr(args, key)
    return cfg


def main(argv=None):
    args = build_parser().parse_args(argv)
    cfg = resolve_config(args)

    if getattr(args, "save_config", False):
        path = save_settings(cfg)
        print(f"wrote {path}")
        return 0

    opts = Options(cfg)
    root = getattr(args, "root", ".")
    print(root.rstrip("/") + "/")
    try:
        shown_dirs, shown_files = walk(root, "", 0, opts)
        # Count the root itself, like `tree`, then everything beneath it.
        total_dirs, total_files = count_tree(root, 0, opts)
        total = summary_line(total_dirs + 1, total_files)
        shown = summary_line(shown_dirs + 1, shown_files)
        if (shown_dirs, shown_files) == (total_dirs, total_files):
            print("\n" + total)
        else:
            print("\n" + total + f" ({shown} shown)")
    except BrokenPipeError:  # e.g. piped into `head`
        try:
            sys.stdout.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
