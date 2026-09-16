#!/usr/bin/env python3
"""Bounded first-line inspection of explicit JDAT text tables; Python 3.9+.

Run on the H100. No data rows are parsed or emitted. Header candidates must pass
conservative validation; invalid bytes and raw exceptions are never reported.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import sys


PREFIX = "2380791_CarDS_Outcomes_DM2_"
SUFFIXES = [
    "Patients.txt", "Inclusion_Dx.txt", "Medical_Hx.txt", "Problem_List.txt",
    "Meds.txt", "Outpatient_Enc.txt", "Outpatient_Enc_CPT.txt",
    "Outpatient_Enc_ICD_PX.txt", "Outpatient_Enc_Flo_Vitals.txt",
    "Outpatient_Enc_Med_Admin.txt", "Hosp_Enc_Med_Admin_1.txt",
    "Hosp_Enc_Med_Admin_2.txt",
] + [f"Hosp_Enc_Labs_{i}.txt" for i in range(1, 7)] + [
    "Hosp_Enc_Labs_1 copy.txt", "Hosp_Enc_Labs_1_2023_09_15.txt",
    "Outpatient_Enc_Labs_1.txt", "Outpatient_Enc_Labs_2.txt",
    "Outpatient_Enc_Labs_1_2023_09_15.txt",
]
NESTED = "2023.03.28 ECG&Echo_MissingMRNs/Data-2024-03-12/"
PRESET = [PREFIX + name for name in SUFFIXES] + [
    NESTED + f"2435227_CarDS_ECG_Labs_{i}.txt" for i in range(1, 13)
] + [NESTED + f"2435227_CarDS_ECG_Med_Admin_{i}.txt" for i in range(1, 4)]
ANCHORS = {"MRN", "PAT_MRN_ID", "PAT_ID", "PATIENT_ID", "PERSON_ID",
           "PAT_ENC_CSN_ID", "PAT_ENC_CSN", "CSN", "ENCOUNTER_ID"}
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_ .()/:-]{0,127}\Z")
DELIMITERS = {"tab": "\t", "pipe": "|", "comma": ","}


class SetupError(ValueError):
    """Static, non-sensitive setup diagnostic suitable for console output."""


def inventory_selection(directory, source, requested):
    """Use a completed source's saved paths, even if other roots are still scanning."""
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    roots = [r for r in summary.get("roots", []) if r.get("label") == source]
    if len(roots) != 1 or roots[0].get("status") != "complete":
        raise SetupError("inventory_source_not_complete_or_not_found")
    root = Path(roots[0]["resolved_root"])
    if not root.is_absolute():
        raise SetupError("invalid_inventory_root")
    expected = roots[0].get("counts", {}).get("file", 0)
    if not isinstance(expected, int) or expected <= 0:
        raise SetupError("inventory_source_has_no_files")
    wanted = {Path(p).name for p in requested}
    matches = {name: set() for name in wanted}
    seen = 0
    with (directory / "inventory.jsonl").open(encoding="utf-8") as stream:
        while seen < expected:
            line = stream.readline(1048577)
            if not line or len(line) > 1048576 or not line.endswith("\n"):
                raise SetupError("inventory_records_incomplete_or_oversized")
            record = json.loads(line)
            if record.get("source") != source or record.get("kind") != "file":
                continue
            seen += 1
            relative = record["path"]
            path = Path(relative)
            if path.is_absolute() or ".." in path.parts:
                raise SetupError("unsafe_inventory_path")
            if path.name in wanted:
                matches[path.name].add(relative)
    selected = {}
    for requested_path in requested:
        candidates = sorted(matches[Path(requested_path).name])
        if requested_path in candidates:
            selected[requested_path] = {"resolved_path": requested_path, "resolution": "exact_inventory_path"}
        elif len(candidates) == 1:
            selected[requested_path] = {"resolved_path": candidates[0], "resolution": "unique_inventory_basename"}
        else:
            selected[requested_path] = {
                "status": "unavailable", "reason": "ambiguous_inventory_basename" if candidates else "not_in_inventory",
                "candidate_paths": candidates,
            }
    return root, selected


def escape(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(
        ">", "&gt;").replace("|", "&#124;").replace("\n", "&#10;").replace(
        "\r", "&#13;").replace("`", "&#96;")


def parse_header(raw, encoding, delimiter):
    if not raw:
        return {"status": "rejected", "reason": "empty_file"}
    if b"\x00" in raw or raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return {"status": "rejected", "reason": "binary_or_unsupported_encoding"}
    if not raw.endswith(b"\n"):
        return {"status": "rejected", "reason": "no_complete_first_line"}
    try:
        text = raw.decode(encoding, errors="strict").rstrip("\r\n")
    except UnicodeError:
        return {"status": "rejected", "reason": "decode_failed"}
    valid = []
    for label, separator in DELIMITERS.items():
        if delimiter != "auto" and label != delimiter:
            continue
        try:
            names = next(csv.reader(io.StringIO(text), delimiter=separator, strict=True))
        except (csv.Error, StopIteration):
            continue
        names = [name.strip() for name in names]
        normalized = [name.upper() for name in names]
        if (len(names) >= 2 and len(set(normalized)) == len(names)
                and all(NAME.fullmatch(name) for name in names)
                and ANCHORS.intersection(normalized)):
            valid.append((label, names))
    if len(valid) != 1:
        return {"status": "rejected", "reason": "unrecognized_or_ambiguous_header"}
    label, names = valid[0]
    fingerprint = hashlib.sha256(json.dumps(names, ensure_ascii=True).encode()).hexdigest()
    return {"status": "header_candidate", "delimiter": label, "encoding": encoding,
            "columns": names, "column_count": len(names), "schema_sha256": fingerprint}


def inspect(root, relative, encoding="utf-8-sig", delimiter="auto", max_bytes=65536):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return {"status": "rejected", "reason": "invalid_relative_path"}
    if path.suffix.lower() != ".txt" or any(
        token in path.name.lower() for token in (".partial", ".tmp", ".download")
    ):
        return {"status": "rejected", "reason": "unsupported_or_partial_file"}
    candidate = root
    try:
        for part in path.parts:
            candidate = candidate / part
            if candidate.is_symlink():
                return {"status": "rejected", "reason": "symlink_not_followed"}
        info = candidate.stat()
        if not stat.S_ISREG(info.st_mode):
            return {"status": "unavailable", "reason": "not_regular_file"}
        size = info.st_size
        # Unbuffered binary readline stops at the first LF, without requesting
        # subsequent rows. A missing LF is bounded to max_bytes + one sentinel.
        with candidate.open("rb", buffering=0) as stream:
            raw = stream.readline(max_bytes + 1)
        if len(raw) > max_bytes:
            return {"status": "rejected", "reason": "header_exceeds_byte_limit",
                    "bytes_read": len(raw)}
        result = parse_header(raw, encoding, delimiter)
        return {**result, "bytes_read": len(raw), "file_bytes": size}
    except FileNotFoundError:
        return {"status": "unavailable", "reason": "file_missing"}
    except PermissionError:
        return {"status": "unavailable", "reason": "file_permission_denied"}
    except OSError as exc:
        return {"status": "unavailable", "reason": "filesystem_error", "errno": exc.errno}


def run(root, files, output, encoding, delimiter, max_bytes, selections=None):
    root = root.resolve()
    output = output.resolve()
    if output == root or root in output.parents or output in root.parents:
        raise ValueError("Source and output trees must be separate")
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    summary = {"version": 2, "status": "running", "source_root": str(root),
               "max_header_bytes": max_bytes, "encoding": encoding,
               "delimiter_policy": delimiter, "data_rows_parsed": False,
               "selection_mode": "saved_inventory" if selections is not None else "explicit_paths",
               "files": []}

    def save():
        temporary = output / "summary.json.tmp"
        temporary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        temporary.replace(output / "summary.json")

    save()
    try:
        with (output / "headers.md").open("x", encoding="utf-8") as report:
            report.write("# JDAT header candidates\n\nRestricted until reviewed. Columns are first-line candidates, "
                         "not validated semantics. No patient rows are printed.\n\n"
                         "Matching schema hashes do not prove equal records or a complete delivery.\n")
            report.write(f"\nResolved source root: {escape(root)}\n")
            try:
                info = root.stat()
                root_status = "available" if stat.S_ISDIR(info.st_mode) else "root_not_directory"
            except FileNotFoundError:
                root_status = "root_missing"
            except PermissionError:
                root_status = "root_permission_denied"
            except OSError:
                root_status = "root_filesystem_error"
            summary["root_check"] = root_status
            if root_status != "available":
                summary["status"] = "incomplete"
                report.write(f"\nRoot check: {root_status}. No source headers inspected.\n")
                print(f"Cannot inspect headers: {root_status}. Check the source mount/path on the H100.", flush=True)
                save()
                return summary
            for index, relative in enumerate(files, 1):
                print(f"Inspecting file {index}/{len(files)}...", flush=True)
                selection = selections[relative] if selections is not None else {"resolved_path": relative}
                if "resolved_path" in selection:
                    actual = selection["resolved_path"]
                    result = {"relative_path": actual, "requested_path": relative, **selection,
                              **inspect(root, actual, encoding, delimiter, max_bytes)}
                else:
                    result = {"relative_path": relative, "requested_path": relative, **selection}
                summary["files"].append(result)
                report.write(f"\n## File {index}: {escape(result['relative_path'])}\n\nStatus: {result['status']}\n\n")
                if result["relative_path"] != relative:
                    report.write(f"Requested: {escape(relative)}; resolved from saved inventory.\n\n")
                if result["status"] == "header_candidate":
                    report.write(f"Delimiter: {result['delimiter']}; columns: {result['column_count']}; "
                                 f"schema SHA-256: {result['schema_sha256']}\n\n")
                    for position, column in enumerate(result["columns"], 1):
                        report.write(f"{position}. {escape(column)}\n")
                else:
                    report.write(f"Reason: {result['reason']}\n")
                    for candidate in result.get("candidate_paths", []):
                        report.write(f"\n- Candidate (not opened): {escape(candidate)}\n")
                report.flush()
                save()
                print(f"  {result['status']}", flush=True)
        summary["status"] = "complete" if all(
            f["status"] == "header_candidate" for f in summary["files"]
        ) else "incomplete"
        save()
    except BaseException:
        summary["status"] = "failed"
        save()
        raise
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Source root; overrides saved inventory root if supplied")
    parser.add_argument("--inventory-dir", type=Path, help="Directory with inventory.jsonl and summary.json")
    parser.add_argument("--inventory-source", default="t2dm", help="Completed source label in the saved inventory")
    parser.add_argument("--preset", choices=["t2dm"])
    parser.add_argument("--file", action="append", default=[], help="Relative .txt path; repeat as needed")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--encoding", choices=["utf-8-sig", "latin-1"], default="utf-8-sig")
    parser.add_argument("--delimiter", choices=["auto", *DELIMITERS], default="auto")
    parser.add_argument("--max-header-bytes", type=int, default=65536)
    args = parser.parse_args(argv)
    if (args.root is not None and not args.root.is_absolute()) or not args.output_dir.is_absolute():
        parser.error("Source and output paths must be absolute")
    if args.root is None and args.inventory_dir is None:
        parser.error("Supply --root or --inventory-dir")
    if not 128 <= args.max_header_bytes <= 1048576:
        parser.error("Header byte limit must be between 128 and 1048576")
    files = list(dict.fromkeys((PRESET if args.preset else []) + args.file))
    if not files:
        parser.error("Supply --preset or at least one --file")
    try:
        selections = None
        root = args.root
        if args.inventory_dir is not None:
            saved_root, selections = inventory_selection(args.inventory_dir, args.inventory_source, files)
            root = root or saved_root
        result = run(root, files, args.output_dir, args.encoding, args.delimiter, args.max_header_bytes, selections)
    except SetupError as exc:
        print("Header inspection setup: " + str(exc), file=sys.stderr)
        return 2
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print("Header inspection failed: " + type(exc).__name__, file=sys.stderr)
        return 2
    print(f"Header inspection {result['status']}. Review headers.md on the cluster.", flush=True)
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    sys.exit(main())
