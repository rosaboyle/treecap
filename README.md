# treecap

A directory tree that shows the **full structure** but caps how many entries
are shown per folder. The overflow collapses into a `... (N more)` line — so a
folder with 698 files doesn't drown the rest of the tree.

Unlike `tree -L` (which limits depth) or `tree --filelimit` (which hides big
directories entirely), `treecap` always recurses but caps the *display* width
per directory.

## Why? A real example: feeding `node_modules` to an AI

You want an AI to help you bump a transitive dependency to patch a CVE, or just
understand how a giant `node_modules` is laid out. So you try `tree`:

```console
$ tree node_modules | tail -1
5602 directories, 29866 files
```

29,866 files. That's hundreds of thousands of tokens — it blows past any model's
context window and buries the *shape* of the tree in noise. `tree -L 2` helps,
but then you lose all the deep paths that actually matter.

`treecap` keeps the full depth but caps the **width** of every folder, so the
whole structure stays legible and small enough to paste into a prompt:

```console
$ treecap node_modules
node_modules/
├── @babel/
│   ├── code-frame/
│   │   ├── lib/
│   │   │   ├── index.js
│   │   │   └── index.js.map
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── compat-data/
│   │   ├── data/
│   │   │   ├── corejs2-built-ins.json
│   │   │   ├── corejs3-shipped-proposals.json
│   │   │   ├── native-modules.json
│   │   │   ├── overlapping-plugins.json
│   │   │   ├── plugin-bugfixes.json
│   │   │   └── ... (1 more)
│   │   ├── corejs2-built-ins.js
│   │   ├── corejs3-shipped-proposals.js
│   │   ├── LICENSE
│   │   ├── native-modules.js
│   │   └── ... (5 more)
│   ├── core/
│   │   ├── lib/
│   │   │   ├── config/
│   │   │   │   ├── files/
│   │   │   │   │   ├── configuration.js
│   │   │   │   │   ├── configuration.js.map
│   │   │   │   │   ├── import.cjs
│   │   │   │   │   ├── import.cjs.map
│   │   │   │   │   ├── index-browser.js
│   │   │   │   │   └── ... (13 more)
│   │   │   │   └── ... (5 more)
│   │   │   └── ... (4 more)
│   │   └── ... (2 more)
│   └── ... (15 more)
└── ... (229 more)
```

Same `node_modules` — but now every directory shows at most a handful of
entries and the rest collapse into `... (N more)`. You still see that `@babel`
exists, that there are 230 top-level packages, and how deep `@babel/core/lib`
goes — all in a few hundred lines instead of 30,000.

> **Tip:** `node_modules` is auto-skipped during recursion, so point `treecap`
> *at* it as the root (`treecap node_modules`) to inspect it. Widen busy levels
> with `-W` when you need more detail: `treecap -W 8 node_modules`.

Great for: dependency audits, "where does this package live?", onboarding to an
unfamiliar repo, and handing an LLM a map of a codebase without flooding its
context window.

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
