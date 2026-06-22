# TODO

## Goal: a token-minimal `tree` (and later `grep`)

`treecap` already caps entries per directory. The next idea is to make the
*output format itself* cheaper to feed to an LLM — fewer tokens than the output
of `tree`, `ls -R`, `find`, or our own current format.

The classic `tree` output wastes tokens on **drawing characters and
indentation whitespace**:

```
├── src/
│   ├── treecap/
│   │   ├── cli.py
│   │   └── __init__.py
```

Every `│`, `├──`, `└──`, and run of spaces is tokens that carry almost no
information. The structure can be conveyed far more cheaply.

### Ideas to try for a compressed / low-token format
- [ ] Drop box-drawing characters (`│ ├ └ ─`) entirely.
- [ ] Replace deep indentation with a compact depth marker (e.g. a leading
      depth number, or 1-space-per-level instead of 4).
- [ ] Path-prefix / indentation-run-length style output, so common parent
      paths aren't repeated.
- [ ] Try a "flat with relative paths" mode vs. an "indented" mode and measure
      which tokenizes smaller.
- [ ] A `--format=mintok` (or `--compact`) flag on `treecap`.
- [ ] Later: apply the same idea to a `grep`-style output (line matches with
      minimal surrounding noise / minimal repeated file headers).

### Measure, don't guess
- [ ] Use `workspace/count_tokens.py` to count tokens of each candidate format.
- [ ] Compare against baselines: real `tree`, `ls -R`, `find .`.
- [ ] Track both **character count** and **token count** — they don't always
      move together.

### Benchmark corpora (run it against real, big trees)
- [ ] **Linux kernel** source tree — the canonical huge tree.
- [ ] A large `node_modules`.
- [ ] CPython source tree.
- [ ] This repo itself (sanity check / fast iteration).

For each: generate output with `tree`, `treecap`, and each candidate compact
format, pipe to `count_tokens.py`, and record tokens saved (%).

### Tokenizers to measure against
- [ ] OpenAI via `tiktoken` (`o200k_base` for GPT-4o/o-series, `cl100k_base`
      for GPT-4/3.5).
- [ ] A Hugging Face tokenizer (e.g. a Llama / Qwen tokenizer) for comparison —
      different tokenizers reward different formats.

> Dev/benchmarking dependencies live in `workspace/requirements-dev.txt` and are
> intentionally kept OUT of `pyproject.toml` so the published `treecap` wheel
> stays dependency-free.
