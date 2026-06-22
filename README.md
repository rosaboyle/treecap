# treecap

**Treecap is the better `tree` for AI.** It shows the *full structure* of a
directory but caps how many entries are shown per folder. The overflow
collapses into a `... (N more)` line, so a folder with 698 files (or a million)
does not drown the rest of the tree or blow past an AI's context window.

Unlike `tree -L` (which limits depth) or `tree --filelimit` (which hides big
directories entirely), `treecap` always recurses but caps the *display* width
per directory. You keep the shape and the deep paths, you just lose the noise.

## Why? Feeding a huge directory to an AI

You want an AI to help you bump a transitive dependency to patch a CVE, or just
understand how a giant `node_modules` is laid out. So you try `tree`:

```console
$ tree node_modules | tail -1
5602 directories, 29866 files
```

29,866 files. That is hundreds of thousands of tokens. It blows past any model's
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

Same `node_modules`, but now every directory shows at most a handful of entries
and the rest collapse into `... (N more)`. You still see that `@babel` exists,
that there are 230 top-level packages, and how deep `@babel/core/lib` goes, all
in a few hundred lines instead of 30,000.

> Tip: `node_modules` is auto-skipped during recursion, so point `treecap`
> *at* it as the root (`treecap node_modules`) to inspect it. Widen busy levels
> with `-W` when you need more detail: `treecap -W 8 node_modules`.

## Example: a HuggingFace dataset with thousands of shards

A downloaded dataset is mostly the same parquet shard repeated thousands of
times. You do not need to see all 41 of them to understand the layout, you need
to see that they exist and how the splits are organized:

```console
$ treecap ~/.cache/huggingface/datasets/wikipedia
wikipedia/
├── 20231101.en/
│   ├── train-00000-of-00041.parquet
│   ├── train-00001-of-00041.parquet
│   ├── train-00002-of-00041.parquet
│   ├── train-00003-of-00041.parquet
│   ├── train-00004-of-00041.parquet
│   └── ... (36 more)
├── 20231101.de/
│   ├── train-00000-of-00020.parquet
│   ├── train-00001-of-00020.parquet
│   ├── train-00002-of-00020.parquet
│   ├── train-00003-of-00020.parquet
│   ├── train-00004-of-00020.parquet
│   └── ... (15 more)
├── dataset_infos.json
├── README.md
└── ... (38 more)
```

There could be a hundred thousand shards on disk. The tree is still 15 lines,
and you can hand it to a model and ask "which language splits are present and
how many shards each?" without sending a single full file listing.

## Example: wide logs next to deep code

This is where width-capping really pays off. Imagine an app directory with a
`logs/` folder holding a million rotated log files, sitting right next to the
source tree you actually care about. `tree` would spend a million lines on logs
before you ever reach `src/`. `treecap` caps the logs to a few and keeps
recursing into the parts with real structure:

```console
$ treecap /srv/app
app/
├── logs/
│   ├── 2026-06-01.log
│   ├── 2026-06-02.log
│   ├── 2026-06-03.log
│   ├── 2026-06-04.log
│   ├── 2026-06-05.log
│   └── ... (999995 more)
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── billing.py
│   │   │   ├── users.py
│   │   │   └── ... (12 more)
│   │   ├── __init__.py
│   │   └── server.py
│   ├── models/
│   │   ├── user.py
│   │   ├── account.py
│   │   └── ... (8 more)
│   └── main.py
├── config.yaml
└── ... (3 more)
```

One million log files collapse into a single `... (999995 more)` line, while the
`src/` branch stays fully expanded so the model can see `routes/auth.py`,
`routes/billing.py`, and the rest of the code that matters.

Great for: dependency audits, "where does this package live?", onboarding to an
unfamiliar repo, inspecting datasets, and handing an LLM a map of a codebase
without flooding its context window.

## Install

```bash
pipx install git+https://github.com/rosaboyle/treecap   # straight from GitHub
# or, from a local clone:
pipx install .        # recommended, isolated, on your PATH
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
treecap --no-skip       # do not auto-skip .git/node_modules/etc.
treecap > dir.tree      # save to a file
```

### Options

| Flag | Meaning |
|------|---------|
| `-W, --width N` | Max entries shown per directory (default 5; `0` = unlimited) |
| `-L, --level DEPTH` | Max display depth (default: unlimited) |
| `-a, --all` | Include hidden files/dirs |
| `--no-skip` | Do not skip `.git`, `node_modules`, `__pycache__`, `.venv`, `venv` |
| `--version` | Print version |

## Links

Source and issues: https://github.com/rosaboyle/treecap
