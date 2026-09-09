import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "headers", Path(__file__).resolve().parents[1] / "scripts" / "inspect_jdat_headers.py")
H = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(H)


class HeaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.out = Path(self.temp.name) / "report"

    def write(self, content, name="table.txt"):
        (self.root / name).write_bytes(content)
        return name

    def test_delimiters_bom_quotes_and_crlf(self):
        for delimiter in [b"\t", b"|", b","]:
            raw = b'\xef\xbb\xbf"PAT_MRN_ID"' + delimiter + b'"RESULT_VALUE"\r\n'
            result = H.parse_header(raw, "utf-8-sig", "auto")
            self.assertEqual(result["columns"], ["PAT_MRN_ID", "RESULT_VALUE"])

    def test_reads_exactly_header_not_patient_row(self):
        header = b"PAT_MRN_ID\tRESULT_VALUE\n"
        stream = io.BytesIO(header + b"SYNTHETIC_SECRET\t123\n")
        name = self.write(header)
        class KeepOpen(io.BytesIO):
            def close(self):
                pass
        stream = KeepOpen(stream.getvalue())
        with patch.object(Path, "open", return_value=stream):
            result = H.inspect(self.root, name)
        self.assertEqual(stream.tell(), len(header))
        self.assertEqual(result["bytes_read"], len(header))
        self.assertNotIn("SYNTHETIC_SECRET", json.dumps(result))

    def test_rejects_bad_headers_without_echo(self):
        for raw in [b"", b"123\tSYNTHETIC_SECRET\n", b"MRN\tMRN\n",
                    b'MRN\t"unclosed\n', b"MRN\tFIELD", b"MRN\t\x00FIELD\n",
                    b"MRN\t\xffFIELD\n"]:
            result = H.parse_header(raw, "utf-8-sig", "auto")
            self.assertEqual(result["status"], "rejected")
            self.assertNotIn("SYNTHETIC_SECRET", json.dumps(result))
            self.assertNotIn("columns", result)

    def test_oversized_line_bounded(self):
        name = self.write(b"M" * 1000 + b"\n")
        result = H.inspect(self.root, name, max_bytes=128)
        self.assertEqual(result["reason"], "header_exceeds_byte_limit")
        self.assertEqual(result["bytes_read"], 129)

    def test_partial_symlink_traversal_and_binary_not_opened(self):
        self.write(b"MRN\tVALUE\n", "table.txt.partial")
        (self.root / "link.txt").symlink_to(self.root / "table.txt.partial")
        with patch.object(Path, "open", side_effect=AssertionError("must not open")):
            for name in ["table.txt.partial", "link.txt", "../table.txt", "/table.txt", "file.gz"]:
                self.assertEqual(H.inspect(self.root, name)["status"], "rejected")

    def test_report_progress_missing_file_and_no_row_output(self):
        self.write(b"MRN\tVALUE\nSYNTHETIC_SECRET\t12\n", "SYNTHETIC_FILENAME.txt")
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            code = H.main(["--root", str(self.root), "--file", "SYNTHETIC_FILENAME.txt",
                           "--file", "absent.txt", "--output-dir", str(self.out)])
        self.assertEqual(code, 2)
        self.assertIn("Inspecting file 1/2", console.getvalue())
        self.assertNotIn("SYNTHETIC_FILENAME", console.getvalue())
        for file in self.out.iterdir():
            self.assertNotIn("SYNTHETIC_SECRET", file.read_text())
        self.assertEqual(json.loads((self.out / "summary.json").read_text())["status"], "incomplete")

    def test_no_overwrite_or_source_output(self):
        with self.assertRaises(ValueError):
            H.run(self.root, ["file.txt"], self.root / "output", "utf-8-sig", "auto", 128)
        self.out.mkdir()
        with self.assertRaises(FileExistsError):
            H.run(self.root, ["file.txt"], self.out, "utf-8-sig", "auto", 128)

    def test_schema_fingerprint_tracks_order_not_patient_rows(self):
        a = H.parse_header(b"MRN\tVALUE\n", "utf-8-sig", "auto")
        b = H.parse_header(b"VALUE\tMRN\n", "utf-8-sig", "auto")
        self.assertNotEqual(a["schema_sha256"], b["schema_sha256"])
        self.assertEqual(len(H.PRESET), len(set(H.PRESET)))
        self.assertFalse(any(".partial" in p for p in H.PRESET))


if __name__ == "__main__":
    unittest.main()
