# treecap

A directory tree that shows the **full structure** but caps how many entries
are shown per folder. The overflow collapses into a `... (N more)` line — so a
folder with 698 files doesn't drown the rest of the tree.

Unlike `tree -L` (which limits depth) or `tree --filelimit` (which hides big
directories entirely), `treecap` always recurses but caps the *display* width
per directory.

## Install

```bash
pipx install .        # recommended — isolated, on your PATH
# or
pip install -e .      # editable install into the current environment
```

## Usage

```bash
treecap                 # current dir, 5 entries per folder
treecap -W 10           # show 10 entries per folder
treecap -L 3            # limit display depth to 3 levels
treecap -W 5 -L 4 data  # 5 per folder, 4 deep, starting at ./data
treecap -a              # include hidden dotfiles
treecap --no-skip       # don't auto-skip .git/node_modules/etc.
treecap > dir.tree      # save to a file
```

### Options

| Flag | Meaning |
|------|---------|
| `-W, --width N` | Max entries shown per directory (default 5; `0` = unlimited) |
| `-L, --level DEPTH` | Max display depth (default: unlimited) |
| `-a, --all` | Include hidden files/dirs |
| `--no-skip` | Don't skip `.git`, `node_modules`, `__pycache__`, `.venv`, `venv` |
| `--version` | Print version |
