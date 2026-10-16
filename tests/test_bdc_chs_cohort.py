"""CHS emulation builder on synthetic dbGaP tables: eligibility, k-1 baseline window, ECG from the previous visit, outcomes."""
import gzip
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "bdc"))
import chs_cohort as CH  # noqa: E402


def wd(path: Path, D: pd.DataFrame):
    path.write_bytes(gzip.compress(("# dbGaP\n\n" + D.to_csv(sep="\t", index=False)).encode()))


FLAGS = ["ACE06", "ACED06", "CCB06", "AMLOD06", "NIFSR06", "NIFIR06", "HCTZ06", "HCTZK06", "BETA06", "BETAD06", "STTN06",
         "ASPIRIN"]


class CHSBuild(unittest.TestCase):
    def test_build(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "pf"
            d = root / "export_P" / "drs"
            d.mkdir(parents=True)
            n = 60
            ids = [str(5000 + i) for i in range(n)]
            ind = [f"C{i}" for i in ids]

            def visit(k, day, age, ccb=None, thz=None, sbp=None):
                D = pd.DataFrame({"dbGaP_Subject_ID": ids, "Individual_ID": ind})
                for f in FLAGS:
                    D[f] = 0
                if ccb is not None:
                    D.loc[ccb, "CCB06"] = 1
                if thz is not None:
                    D.loc[thz, "HCTZ06"] = 1
                if day is not None:
                    D["STDYTIME"] = day
                D[f"AGEY{k}" if k > 2 else "AGEBL_x"] = age
                if sbp is not None:
                    D["AVESYS"] = sbp
                return D
            ccb, thz = list(range(0, 20)), list(range(20, 40))
            pre = "phs000287.v7.pht0014{}.v1.p1.c1.{}.HMB-MDS.txt.gz"
            wd(d / pre.format("50", "BASE1"), visit(2, None, 72))
            wd(d / pre.format("51", "BASE2"), pd.DataFrame({"dbGaP_Subject_ID": ids, "NEWLVM43": 150.0, "LVEF43": 1}))
            wd(d / pre.format("52", "BASEBOTH"), pd.DataFrame({"dbGaP_Subject_ID": ids, "Individual_ID": ind, "PERSTAT": 1,
                                                                "AGEBL": 72, "GEND01": [i % 2 for i in range(n)], "RACE01": 1,
                                                                "BPHI": 1, "DIABADA": 1, "SMOKE": 0, "CRE44": 1.0}))
            wd(d / pre.format("88", "YR3"), visit(3, 365, 73, ccb, thz, sbp=None))
            # visit-4 SBP (after time zero for year-3 starters) must NOT be used as their held-out value
            wd(d / pre.format("89", "YR4"), visit(4, 730, 74, ccb, thz, sbp=999.0))
            es = pd.DataFrame({"dbGaP_Subject_ID": ids, "MIBLMOD": 0, "ANBLMOD": 0, "CHBLMOD": 0, "STBLMOD": 0, "INCMI": 0,
                               "TTOMI": 9999, "INCANG": 0, "TTOANG": 9999, "INCANGIO": 0, "TTOANGI": 9999, "INCBYPS": 0,
                               "TTOBYPS": 9999, "INCCHF": 0, "TTOCHF": 9999, "INCSTRK": 0, "TTOSTK": 9999, "DEATH": 0,
                               "TTODTH": 9999, "CAUSE80": 0})
            es.loc[0:2, "CHBLMOD"] = 1  # prevalent HF -> excluded from E1
            wd(d / pre.format("64", "EVENT_SUMMARY"), es)
            ev = pd.DataFrame({"dbGaP_Subject_ID": ids[3:8] + ids[20:22], "EVTYPE": 1, "TTOEVENT": [1000] * 5 + [100, 4000]})
            wd(d / pre.format("66", "CHS_Event16"), ev)  # 5 MIs after time zero (day 365) in CCB; one before t0, one after horizon
            wd(d / pre.format("65", "EVENT_TIME_TO_CENSUS"), pd.DataFrame({"dbGaP_Subject_ID": ids, "TTOFCNDT": 5000, "TTONFCND": 5000}))
            tsv = root / "export_I" / "tsv"
            tsv.mkdir(parents=True)
            pd.DataFrame({"id": [f"s{i}" for i in range(n)], "object.participant_id": ind}).to_csv(tsv / "subject.tsv", sep="\t", index=False)
            files = [f"CHS_ECG_VISIT01_19890101_{i:05d}.xml" for i in range(n)] + [f"CHS_ECG_VISIT02_19900101_{i + 100:05d}.xml" for i in range(n)]
            pd.DataFrame({"relations.dst_id": [f"s{i}" for i in range(n)] * 2, "object.file_name": files}).to_csv(
                tsv / "imaging_file.tsv", sep="\t", index=False)
            xd = root / "export_I" / "drs" / "data"
            xd.mkdir(parents=True)
            for f in files:
                (xd / f).write_text("<RestingECG/>")
            os.environ["BDC_TTE_OUT"], os.environ["BDC_RESTRICTED"] = f"{t}/o", f"{t}/r"
            CH.main(["--root", str(root)])
            R = pd.read_parquet(Path(t) / "r" / "chs_emulations.parquet") if (Path(t) / "r" / "chs_emulations.parquet").exists() \
                else pd.read_pickle(Path(t) / "r" / "chs_emulations.pkl")
            E1 = R[R.EMU == "E1_ccb_vs_thiazide"]
            self.assertEqual(len(E1), 37)                        # 40 new users minus 3 with prevalent HF
            self.assertEqual(int((E1.arm == 1).sum()), 17)
            self.assertTrue((E1.k == 3).all())
            self.assertTrue(E1.ECG_FILE.str.contains("VISIT01").all())  # ECG from year 2 (k-1), not year 3
            self.assertTrue(E1.ECG_XML_PATH.notna().all())
            self.assertTrue(E1.vital_sbp.isna().all())           # the visit-4 value (after time zero) is not used
            self.assertTrue((E1.echo_lv_mass == 150).all())
            self.assertEqual(int(E1[E1.arm == 1].E_primary.sum()), 5)   # MI at day 1000 (t0 = 365)
            self.assertEqual(int(E1[E1.arm == 0].E_primary.sum()), 0)   # one MI before t0, one beyond 60 months
            self.assertTrue((E1.HF == 0).all() and (E1.AGE == 72).all())
            rep = (Path(t) / "o" / "chs_cohort" / "report.md").read_text()
            self.assertNotIn("5003", rep)


if __name__ == "__main__":
    unittest.main()
