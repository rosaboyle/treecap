#!/usr/bin/env python3
"""Count tokens in files (or stdin) for comparing tree-output formats.

Reports characters, bytes, lines, and token counts under one or more
tokenizers, so you can measure which compact format is actually cheaper to
feed to an LLM.

Examples
--------
    # Count tokens in a file with the default OpenAI tokenizers
    python workspace/count_tokens.py out.txt

    # Compare several format candidates side by side
    python workspace/count_tokens.py classic.txt compact.txt flat.txt

    # Pipe output straight from a tree command
    treecap /path/to/linux | python workspace/count_tokens.py -

    # Also measure a Hugging Face tokenizer
    python workspace/count_tokens.py out.txt --hf meta-llama/Llama-3.1-8B

Deps: see workspace/requirements-dev.txt  (tiktoken, optionally transformers)
"""
import argparse
import sys

# OpenAI encodings to measure by default.
#   o200k_base -> GPT-4o / o-series
#   cl100k_base -> GPT-4 / GPT-3.5
DEFAULT_ENCODINGS = ["o200k_base", "cl100k_base"]


def read_source(path):
    """Return (label, text) for a path, or for '-' read stdin."""
    if path == "-":
        return "<stdin>", sys.stdin.read()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return path, f.read()


def load_tiktoken_encoders(names):
    try:
        import tiktoken
    except ImportError:
        sys.exit(
            "tiktoken not installed.\n"
            "  pip install -r workspace/requirements-dev.txt"
        )
    encoders = {}
    for name in names:
        encoders[name] = tiktoken.get_encoding(name)
    return encoders


def load_hf_tokenizer(model):
    try:
        from transformers import AutoTokenizer
    except ImportError:
        sys.exit(
            "transformers not installed (needed for --hf).\n"
            "  pip install -r workspace/requirements-dev.txt"
        )
    return AutoTokenizer.from_pretrained(model)


def count(text, tiktoken_encoders, hf_tokenizer):
    """Return an ordered dict of metric -> count for one text blob."""
    metrics = {
        "chars": len(text),
        "bytes": len(text.encode("utf-8")),
        "lines": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
    }
    for name, enc in tiktoken_encoders.items():
        metrics[f"tok:{name}"] = len(enc.encode(text))
    if hf_tokenizer is not None:
        ids = hf_tokenizer(text, add_special_tokens=False)["input_ids"]
        metrics[f"tok:hf"] = len(ids)
    return metrics


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", help="files to measure ('-' for stdin)")
    p.add_argument("--encoding", action="append", metavar="NAME",
                   help="tiktoken encoding(s) to use "
                        "(default: o200k_base, cl100k_base)")
    p.add_argument("--hf", metavar="MODEL",
                   help="also count with this Hugging Face tokenizer "
                        "(e.g. meta-llama/Llama-3.1-8B)")
    args = p.parse_args(argv)

    encodings = args.encoding or DEFAULT_ENCODINGS
    tiktoken_encoders = load_tiktoken_encoders(encodings)
    hf_tokenizer = load_hf_tokenizer(args.hf) if args.hf else None

    rows = []
    for path in args.files:
        label, text = read_source(path)
        rows.append((label, count(text, tiktoken_encoders, hf_tokenizer)))

    # Column order: label first, then the metrics in insertion order.
    metric_names = list(rows[0][1].keys())
    headers = ["file"] + metric_names
    widths = [len(h) for h in headers]
    for label, metrics in rows:
        widths[0] = max(widths[0], len(label))
        for i, m in enumerate(metric_names, start=1):
            widths[i] = max(widths[i], len(f"{metrics[m]:,}"))

    def fmt_row(cells):
        return "  ".join(c.rjust(w) if i else c.ljust(w)
                         for i, (c, w) in enumerate(zip(cells, widths)))

    print(fmt_row(headers))
    print(fmt_row(["-" * w for w in widths]))
    for label, metrics in rows:
        print(fmt_row([label] + [f"{metrics[m]:,}" for m in metric_names]))

    # If we measured more than one file, show savings vs. the first (baseline).
    if len(rows) > 1:
        base_label, base = rows[0]
        print(f"\nSavings vs. baseline ({base_label}):")
        for label, metrics in rows[1:]:
            parts = []
            for m in metric_names:
                if base[m]:
                    pct = 100.0 * (base[m] - metrics[m]) / base[m]
                    parts.append(f"{m} {pct:+.1f}%")
            print(f"  {label}: " + "  ".join(parts))


if __name__ == "__main__":
    main()
