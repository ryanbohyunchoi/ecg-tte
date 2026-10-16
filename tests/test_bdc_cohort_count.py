"""CHS new-user counter on synthetic dbGaP-format tables + Gen3 PFB tables."""
import gzip
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "bdc"))
import cohort_count as CC  # noqa: E402


def write_dbgap(path: Path, D: pd.DataFrame):
    txt = "# Study accession: phs000287.v7.p1\n# Table accession: x\n\n" + D.to_csv(sep="\t", index=False)
    path.write_bytes(gzip.compress(txt.encode()))


class CHSCount(unittest.TestCase):
    def test_counts(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "pf"
            d = root / "export_P" / "drs" / "chs"
            d.mkdir(parents=True)
            ids = [f"{1000 + i}" for i in range(40)]
            base = dict(dbGaP_Subject_ID=ids, ACE06=0, ACED06=0, CCB06=0, AMLOD06=0, NIFSR06=0, NIFIR06=0, HCTZ06=0,
                        HCTZK06=0, BETA06=0, BETAD06=0, STTN06=0, ASPIRIN=0)
            V2 = pd.DataFrame(base)
            V3 = pd.DataFrame(base)
            V3.loc[0:14, "ACE06"] = 1       # 15 ACEi starters at year 3
            V3.loc[15:26, "CCB06"] = 1      # 12 CCB starters
            V3.loc[27, ["ACED06", "CCB06"]] = 1  # starts both comparators -> excluded from ACEi vs CCB
            V4 = V3.copy()
            write_dbgap(d / "phs000287.v7.pht001450.v1.p1.c1.BASE1.HMB-MDS.txt.gz", V2)
            write_dbgap(d / "phs000287.v6.pht001450.v1.p1.c1.BASE1.HMB-IRB-MDS.txt.gz", V2.iloc[:3])  # older version: ignored
            write_dbgap(d / "phs000287.v7.pht001488.v1.p1.c1.YR3.HMB-MDS.txt.gz", V3)
            write_dbgap(d / "phs000287.v7.pht001489.v1.p1.c1.YR4.HMB-MDS.txt.gz", V4)
            echo = pd.DataFrame(dict(dbGaP_Subject_ID=ids, NEWLVM43=[150.0] * 30 + [np.nan] * 10))
            write_dbgap(d / "phs000287.v7.pht001451.v1.p1.c1.BASE2.HMB-MDS.txt.gz", echo)
            tsv = root / "export_I" / "tsv"
            tsv.mkdir(parents=True)
            pd.DataFrame({"id": [f"s{i}" for i in range(40)], "object.submitter_id": ids}).to_csv(tsv / "subject.tsv", sep="\t", index=False)
            # baseline (year 2 -> VISIT01) ECG for the first 20 participants only
            pd.DataFrame({"relations.dst_id": [f"s{i}" for i in range(20)],
                          "object.file_name": [f"CHS_ECG_VISIT01_19890101_{i:05d}.xml" for i in range(20)]}).to_csv(
                tsv / "imaging_file.tsv", sep="\t", index=False)
            os.environ["BDC_TTE_OUT"] = f"{t}/o"
            CC.main(["--cohort", "CHS", "--root", str(root)])
            C = pd.read_csv(Path(t) / "o" / "cohort_count" / "CHS" / "counts.csv")
            r = C[C.comparison == "ACEI vs CCB"].set_index("arm")
            self.assertEqual(int(r.loc["ACEI", "n_new_users"]), 15)
            self.assertEqual(int(r.loc["CCB", "n_new_users"]), 12)
            self.assertEqual(int(r.loc["ACEI", "n_with_prior_ecg"]), 15)   # ids 0-14 have a VISIT01 ECG
            self.assertEqual(str(r.loc["CCB", "n_with_prior_ecg"]), "1-10")  # ids 15-19 only -> 5 -> suppressed
            rep = (Path(t) / "o" / "cohort_count" / "CHS" / "report.md").read_text()
            self.assertIn("subjects_matched", rep)
            self.assertNotIn("1003", rep)


class MESACount(unittest.TestCase):
    def test_statin_vs_none(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "pf"
            d = root / "export_P" / "drs" / "mesa"
            d.mkdir(parents=True)
            ids = list(range(3000, 3060))
            def exam(k, statin):
                D = pd.DataFrame({"dbGaP_Subject_ID": ids, "sidno": ids})
                for c in ("ace", "aced", "a2a", "a2ad", "ccb", "hctz", "beta", "betad", "htnmed"):
                    D[f"{c}{k}c"] = 0
                D[f"sttn{k}c"] = statin
                if k == 1:
                    D["olvedm1"] = [140.0] * 50 + [np.nan] * 10
                return D
            s2 = np.zeros(60, int)
            s2[:25] = 1  # 25 statin starters at exam 2
            for k, st in ((1, 0), (2, s2)):
                write_dbgap(d / f"phs000209.v13.pht00111{5 + k}.v8.p3.c1.MESA_Exam{k}Main.HMB.txt.gz", exam(k, st))
            tsv = root / "export_I" / "tsv"
            tsv.mkdir(parents=True)
            pd.DataFrame({"id": [f"m{i}" for i in ids], "object.submitter_id": [str(i) for i in ids]}).to_csv(
                tsv / "subject.tsv", sep="\t", index=False)
            pd.DataFrame({"relations.dst_id": [f"m{i}" for i in ids[:40]],
                          "object.file_name": [f"MESA_ECG_VISIT01_20010101_{i:05d}.xml" for i in range(40)]}).to_csv(
                tsv / "imaging_file.tsv", sep="\t", index=False)
            os.environ["BDC_TTE_OUT"] = f"{t}/o"
            CC.main(["--cohort", "MESA", "--root", str(root)])
            C = pd.read_csv(Path(t) / "o" / "cohort_count" / "MESA" / "counts.csv")
            r = C[C.comparison == "STATIN vs none"].set_index("arm")
            self.assertEqual(int(r.loc["STATIN", "n_new_users"]), 25)
            self.assertEqual(int(r.loc["STATIN", "n_with_prior_ecg"]), 25)       # first 40 have an exam-1 ECG
            self.assertEqual(int(r.loc["none", "n_new_users"]), 35)
            self.assertEqual(int(r.loc["none", "n_with_prior_ecg"]), 15)
            self.assertEqual(int(r.loc["none", "n_with_ecg_and_heldout"]), 15)  # ids 25-39 have CMR


if __name__ == "__main__":
    unittest.main()
