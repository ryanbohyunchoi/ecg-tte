"""Synthetic-only inventory checks. No cluster access or archive imports."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "inventory_jdat", Path(__file__).resolve().parents[1] / "scripts" / "inventory_jdat.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / "source"
        self.source.mkdir()
        self.output = self.base / "output"

    def run_inventory(self):
        return MODULE.inventory([("synthetic", self.source)], self.output)

    def test_lists_all_files_without_reading_contents(self):
        (self.source / "Meds.txt").write_text("SYNTHETIC_SECRET")
        (self.source / ".hidden").write_bytes(b"abc")
        sub = self.source / "nested"
        sub.mkdir()
        (sub / "Labs.parquet.gz").write_bytes(b"not a real parquet")
        original = Path.open

        def guarded_open(path, mode="r", *args, **kwargs):
            if MODULE.beneath(path.resolve(), self.source):
                raise AssertionError("Source contents opened")
            return original(path, mode, *args, **kwargs)

        with patch.object(Path, "open", guarded_open):
            result = self.run_inventory()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["roots"][0]["counts"]["file"], 3)
        report = (self.output / "inventory.md").read_text()
        self.assertIn("nested/Labs.parquet.gz", report)
        self.assertNotIn("SYNTHETIC_SECRET", report)

    def test_symlinks_not_followed_and_special_files_not_opened(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "do_not_list.txt").write_text("synthetic")
        (self.source / "linked").symlink_to(outside, target_is_directory=True)
        (self.source / "cycle").symlink_to(self.source, target_is_directory=True)
        os.mkfifo(self.source / "pipe")
        result = self.run_inventory()
        self.assertEqual(result["roots"][0]["counts"], {"symlink": 2, "special": 1})
        self.assertNotIn("do_not_list", (self.output / "inventory.md").read_text())

    def test_missing_root_keeps_other_results_but_returns_incomplete(self):
        (self.source / "file.txt").touch()
        result = MODULE.inventory([("present", self.source), ("missing", self.base / "missing")], self.output)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["roots"][0]["counts"]["file"], 1)
        self.assertEqual(result["roots"][1]["counts"]["error"], 1)

    def test_unreadable_directory_reported_without_exception_text(self):
        with patch.object(MODULE.os, "scandir", side_effect=PermissionError(13, "SYNTHETIC_SECRET")):
            result = self.run_inventory()
        self.assertEqual(result["status"], "incomplete")
        self.assertNotIn("SYNTHETIC_SECRET", (self.output / "inventory.jsonl").read_text())

    def test_refuses_overwrite_and_source_output_overlap(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_inventory()
        with self.assertRaises(ValueError):
            MODULE.inventory([("source", self.source)], self.source / "results")
        self.assertFalse((self.source / "results").exists())

    def test_refuses_duplicate_and_overlapping_roots(self):
        with self.assertRaises(ValueError):
            MODULE.inventory([("one", self.source), ("two", self.source / "nested")], self.output)
        with self.assertRaises(ValueError):
            MODULE.inventory([("one", self.source), ("one", self.base / "other")], self.output)

    def test_console_hides_filenames_and_report_escapes_them(self):
        filename = "SYNTHETIC_IDENTIFIER|<name>\n.txt"
        (self.source / filename).touch()
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            code = MODULE.main(["--root", "synthetic=" + str(self.source), "--output-dir", str(self.output)])
        self.assertEqual(code, 0)
        self.assertNotIn("SYNTHETIC_IDENTIFIER", console.getvalue())
        self.assertIn("&#124;&lt;name&gt;&#10;", (self.output / "inventory.md").read_text())
        records = [json.loads(line) for line in (self.output / "inventory.jsonl").read_text().splitlines()]
        self.assertEqual(records[0]["path"], filename)


if __name__ == "__main__":
    unittest.main()
