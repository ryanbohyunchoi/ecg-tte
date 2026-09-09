#!/usr/bin/env python3
"""List explicitly supplied source trees without opening any source file contents.

Python 3.9+; standard library only. Run on the H100, not through assistant SSH.
Detailed reports may contain sensitive filenames and must remain on the cluster
until reviewed. Console output contains counts/status only.
"""

import argparse
from collections import Counter
import errno
import json
import os
from pathlib import Path
import re
import stat
import sys


VERSION = "1"


def category(filename):
    """Filename hints only: no clinical semantics or availability are verified."""
    name = filename.lower()
    rules = [
        ("documentation", r"dictionary|readme|specification|manifest|layout"),
        ("medication administration", r"med.*admin"),
        ("medications", r"meds|medication|prescription|pharmacy|dispens"),
        ("echocardiography", r"echo|tte"),
        ("ECG", r"ecg|ekg"),
        ("clinical notes", r"notes?|narrative"),
        ("labs", r"labs?|laboratory"),
        ("vitals", r"vital|flowsheet"),
        ("diagnoses", r"diagnos|condition|problem"),
        ("procedures", r"procedure"),
        ("mortality", r"death|mortality|deceased"),
        ("encounters", r"encounter|_enc_|admission|hospital"),
        ("demographics", r"demograph|patient|person"),
    ]
    for label, pattern in rules:
        if re.search(pattern, name):
            return label
    return "unclassified"


def md(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(
        ">", "&gt;"
    ).replace("|", "&#124;").replace("\n", "&#10;").replace("\r", "&#13;").replace(
        "`", "&#96;"
    )


def beneath(path, parent):
    return path == parent or parent in path.parents


def parse_root(value):
    label, separator, path = value.partition("=")
    if not separator or not path or not re.fullmatch(r"[A-Za-z0-9_-]+", label):
        raise argparse.ArgumentTypeError("Use --root LABEL=/absolute/source/path")
    p = Path(path).expanduser()
    if not p.is_absolute():
        raise argparse.ArgumentTypeError("Source roots must be absolute paths")
    return label, p


def scan(root, emit):
    """Stream records, holding at most one directory listing at a time.

    Explicit root aliases are resolved by the caller. Descendant symlinks are
    recorded but never followed. Directory errors leave an incomplete report.
    """
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            # Recheck before descent, including directories replaced by symlinks.
            if directory.is_symlink():
                emit({"kind": "symlink", "path": str(directory.relative_to(root))})
                continue
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: item.name)
        except OSError as exc:
            emit({"kind": "error", "path": str(directory.relative_to(root)),
                  "operation": "list_directory", "errno": exc.errno})
            continue
        children = []
        for entry in entries:
            rel = str(Path(entry.path).relative_to(root))
            try:
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    emit({"kind": "symlink", "path": rel})
                elif stat.S_ISDIR(info.st_mode):
                    children.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    parts = Path(rel).parts
                    emit({"kind": "file", "path": rel, "bytes": info.st_size,
                          "category_hint": category(entry.name),
                          "origin_hint": "derived-directory" if any(
                              p.lower() in {"omop_database", "pool", "runs", "embeddings"}
                              for p in parts[:-1]) else "unverified"})
                else:
                    emit({"kind": "special", "path": rel})
            except OSError as exc:
                emit({"kind": "error", "path": rel, "operation": "stat",
                      "errno": exc.errno})
        pending.extend(reversed(children))


def inventory(roots, output):
    roots = [(label, p.resolve()) for label, p in roots]
    output = output.expanduser().resolve()
    labels = [label for label, _ in roots]
    if len(set(labels)) != len(labels):
        raise ValueError("Root labels must be unique")
    for index, (_, root) in enumerate(roots):
        if beneath(output, root) or beneath(root, output):
            raise ValueError("Output and source trees must be separate")
        for _, other in roots[:index]:
            if beneath(root, other) or beneath(other, root):
                raise ValueError("Source roots must not overlap, including resolved aliases")
    # Existing outputs are never reused, even after a failed run.
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    summary = {"inventory_version": VERSION, "status": "running", "roots": [],
               "contents_read": False, "category_basis": "filename hints only",
               "scope": "All regular files; descendant symlinks not followed; archives not expanded"}
    summary_path = output / "summary.json"

    def checkpoint():
        temporary = output / "summary.json.tmp"
        temporary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        temporary.replace(summary_path)

    checkpoint()
    try:
        with (output / "inventory.jsonl").open("x", encoding="utf-8") as records, (
            output / "inventory.md"
        ).open("x", encoding="utf-8") as report:
            report.write("# JDAT file inventory\n\nRestricted report: filenames and paths require review before sharing.\n\n"
                         "File contents were not opened. Categories are filename hints, not validated semantics.\n"
                         "No files are excluded by extension; archive members are not listed.\n")
            for label, root in roots:
                counts = Counter()
                groups = Counter()
                total_bytes = 0
                report.write(f"\n## {md(label)}\n\nRoot: {md(root)}\n\n"
                             "| Relative path | Kind / category hint | Bytes | Origin hint |\n"
                             "|---|---|---:|---|\n")

                def emit(record):
                    nonlocal total_bytes
                    record = {"source": label, **record}
                    counts[record["kind"]] += 1
                    if record["kind"] == "file":
                        total_bytes += record["bytes"]
                        groups[record["category_hint"]] += 1
                    records.write(json.dumps(record, ensure_ascii=True) + "\n")
                    detail = record.get("category_hint", record["kind"])
                    if record["kind"] == "error":
                        detail += " (" + str(record.get("operation")) + ", errno=" + str(record.get("errno")) + ")"
                    report.write(f"| {md(record['path'])} | {md(detail)} | "
                                 f"{record.get('bytes', '')} | {record.get('origin_hint', '')} |\n")

                try:
                    info = root.stat()
                    if not stat.S_ISDIR(info.st_mode):
                        emit({"kind": "error", "path": ".", "operation": "root_not_directory",
                              "errno": errno.ENOTDIR})
                    else:
                        scan(root, emit)
                except OSError as exc:
                    emit({"kind": "error", "path": ".", "operation": "root_stat", "errno": exc.errno})
                result = {"label": label, "resolved_root": str(root), "counts": dict(counts),
                          "bytes": total_bytes, "categories": dict(sorted(groups.items())),
                          "status": "incomplete" if counts["error"] else "complete"}
                summary["roots"].append(result)
                report.write(f"\nStatus: {result['status']}. Files: {counts['file']}; "
                             f"symlinks skipped: {counts['symlink']}; errors: {counts['error']}.\n")
                checkpoint()
            summary["status"] = "incomplete" if any(
                r["status"] != "complete" for r in summary["roots"]
            ) else "complete"
        checkpoint()
    except BaseException:
        summary["status"] = "failed"
        checkpoint()
        raise
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=parse_root, action="append", required=True,
                        help="Repeat LABEL=/absolute/path for each source tree")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="New, separate cluster directory for restricted reports")
    args = parser.parse_args(argv)
    if not args.output_dir.is_absolute():
        parser.error("Output directory must be an absolute path")
    try:
        result = inventory(args.root, args.output_dir)
    except (ValueError, OSError) as exc:
        # Do not echo paths or arbitrary exception text to the console.
        reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print("Inventory failed: " + reason, file=sys.stderr)
        return 2
    files = sum(r["counts"].get("file", 0) for r in result["roots"])
    errors = sum(r["counts"].get("error", 0) for r in result["roots"])
    print(f"Inventory {result['status']}: {files} files, {errors} errors.")
    print("Review inventory.md and summary.json in the requested output directory on the cluster.")
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    sys.exit(main())
