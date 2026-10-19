"""CHS CLMBR-T transfer: code normalisation, xformers shim mask, timeline builder on synthetic CHS tables, and (where femr
and the local CLMBR-T copy exist) encoding with the causal-prefix check and shim-vs-xformers parity."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts" / "bdc"))
sys.path.insert(0, str(HERE))
import chs_clmbr as CL  # noqa: E402

MODEL = Path("/mnt/raid0/eo287/clmbr")
MOS = Path("/mnt/raid0/rbc58/ecg-tte/software/mosaic-env")


class Codes(unittest.TestCase):
    def test_icd9(self):
        self.assertEqual(CL.icd9cm_dotted("4280"), "428.0")
        self.assertEqual(CL.icd9cm_dotted("428.0"), "428.0")
        self.assertEqual(CL.icd9cm_dotted("V4581"), "V45.81")
        self.assertEqual(CL.icd9cm_dotted("E8790"), "E879.0")
        M = {"428.0": ["SNOMED/a"], "250": ["SNOMED/b"]}
        self.assertEqual(CL.map_dx("428.0", M), ["SNOMED/a"])
        self.assertEqual(CL.map_dx("250.02", M), ["SNOMED/b"])      # falls back to the 3-digit category
        self.assertEqual(CL.map_dx("999.9", M), [])
        self.assertEqual(CL.map_px("3606", {"36.06"}), ["ICD9Proc/36.06"])
        self.assertEqual(CL.map_px("88.72", {"88.7"}), ["ICD9Proc/88.7"])
        self.assertEqual(CL.map_px("1", {"1"}), [])
        R = {"361": ["SNOMED/399261000"], "3722": ["SNOMED/67629009"]}
        self.assertEqual(CL.map_px("36.12", {"36.06"}, R), ["SNOMED/399261000"])   # curated category rule
        self.assertEqual(CL.map_px("37.22", set(), R), ["SNOMED/67629009"])
        self.assertEqual(CL.map_px("36.06", {"36.06"}, R), ["ICD9Proc/36.06"])     # exact in-vocabulary code first
        self.assertTrue(CL.is_chronic("428.0") and CL.is_chronic("2500") and CL.is_chronic("V45.81"))
        self.assertFalse(CL.is_chronic("486") or CL.is_chronic("820.0"))


class Shim(unittest.TestCase):
    def test_mask(self):
        try:
            import torch
        except ImportError:
            self.skipTest("torch not installed")
        sys.path.insert(0, str(HERE.parent / "scripts" / "bdc" / "xformers_shim"))
        from xformers.ops.fmha import attn_bias as ab
        if not getattr(sys.modules["xformers"], "__version__", "").endswith("chs-shim"):
            self.skipTest("real xformers already imported")
        m = ab.BlockDiagonalMask.from_seqlens([3, 2]).make_local_attention(2).materialize((5, 5))
        ok = torch.isfinite(m)
        exp = torch.tensor([[1, 0, 0, 0, 0], [1, 1, 0, 0, 0], [0, 1, 1, 0, 0], [0, 0, 0, 1, 0], [0, 0, 0, 1, 1]], dtype=torch.bool)
        self.assertTrue(torch.equal(ok, exp))


class Timeline(unittest.TestCase):
    def test_timeline(self):
        import chs_cohort as CH
        from test_bdc_chs_cohort import write_synthetic
        with tempfile.TemporaryDirectory() as t:
            root, ids = write_synthetic(t)
            os.environ["BDC_TTE_OUT"], os.environ["BDC_RESTRICTED"] = f"{t}/o", f"{t}/r"
            CH.main(["--root", str(root)])
            mp = dict(version=CL.MAP_VERSIONS[-1], icd9cm={"428.0": ["SNOMED/42343007"], "250": ["SNOMED/44054006"],
                                                     "410": ["SNOMED/22298006"]},
                      icd9proc=["36.06"], med={"THYR06": ["RxNorm/T"], "CCB06": [], "HCTZ06": ["RxNorm/H"],
                                               "ASPIRIN": ["RxNorm/A"]},
                      history={"HF": ["SNOMED/42343007"], "HTN": ["SNOMED/38341003"]},
                      visit={"clinic": "Visit/OP", "admission": "Visit/IP"})
            (Path(t) / "map.json").write_text(json.dumps(mp))
            CL.main(["timeline", "--map", f"{t}/map.json", "--root", str(root)])
            X = pd.read_parquet(Path(t) / "r" / "chs_clmbr_events.parquet")
            Q = pd.read_parquet(Path(t) / "r" / "chs_clmbr_queries.parquet")
            R = pd.read_parquet(Path(t) / "r" / "chs_emulations.parquet")
            self.assertEqual(set(Q.row), set(R.row))                       # every emulation row has a query
            first = X.groupby("subject_id").head(1)
            self.assertTrue((first.code == "MEDS_BIRTH").all())             # birth first in every timeline
            self.assertEqual(int((X.code == "MEDS_BIRTH").sum()), X.subject_id.nunique())
            E1 = R[R.EMU == "E1_ccb_vs_thiazide"]
            subj = Q[Q.row.isin(set(E1.row))].subject_id
            self.assertFalse(X[X.subject_id.isin(set(subj))].code.isin(["RxNorm/H"]).any())   # exposure flags removed
            self.assertTrue(X[X.subject_id.isin(set(subj))].code.eq("RxNorm/T").any())        # other meds kept
            # id 5 (k-1 = year 2, day 0): admissions on days 100 and 900 lie after its cutoff
            q5 = Q[Q.row == E1[E1.id == ids[5]].row.iloc[0]].iloc[0]
            x5 = X[X.subject_id == q5.subject_id]
            self.assertFalse(x5[x5.time < q5.cutoff].code.isin(["SNOMED/44054006", "SNOMED/22298006"]).any())
            # id 0 has an admission on day -1 with 428.0 (HF): before the cutoff, and prevalent HF is excluded from E1 anyway
            rep = json.loads((Path(t) / "o" / "chs_clmbr" / "timeline.json").read_text())
            self.assertGreater(rep["dx_mapped_share"], 0)
            self.assertNotIn("5003", json.dumps(rep))
            # --rich: ongoing conditions repeated at later clinic visits; separate output names
            CL.main(["timeline", "--map", f"{t}/map.json", "--root", str(root), "--rich", "--tag", "rich"])
            Xr = pd.read_parquet(Path(t) / "r" / "chs_clmbr_rich_events.parquet")
            self.assertTrue((Path(t) / "r" / "chs_clmbr_events.parquet").exists())
            self.assertGreater(len(Xr), len(X))
            htn = X[X.code == "SNOMED/38341003"].groupby("subject_id").size()
            htn_r = Xr[Xr.code == "SNOMED/38341003"].groupby("subject_id").size()
            self.assertTrue((htn_r.reindex(htn.index) >= htn).all() and (htn_r > 1).any())
            self.assertTrue((Xr.groupby("subject_id").head(1).code == "MEDS_BIRTH").all())
            self.assertFalse(Xr[Xr.subject_id.isin(set(subj))].code.isin(["RxNorm/H"]).any())
            rr = json.loads((Path(t) / "o" / "chs_clmbr" / "timeline_rich.json").read_text())
            self.assertGreater(rr["coverage"]["carried_forward_events"], 0)

    @unittest.skipUnless(MODEL.exists() and (MOS / "bin" / "python").exists(), "local CLMBR-T copy / femr env missing")
    def test_encode_local(self):
        """Encode a synthetic timeline set with the real model on CPU (mosaic env): real xformers vs the shim, and the
        causal-prefix check."""
        import chs_cohort as CH
        from test_bdc_chs_cohort import write_synthetic
        with tempfile.TemporaryDirectory() as t:
            root, _ids = write_synthetic(t)
            env = dict(os.environ, BDC_TTE_OUT=f"{t}/o", BDC_RESTRICTED=f"{t}/r")
            os.environ.update(BDC_TTE_OUT=f"{t}/o", BDC_RESTRICTED=f"{t}/r")
            CH.main(["--root", str(root)])
            mp = dict(version=CL.MAP_VERSIONS[-1], icd9cm={"428.0": ["SNOMED/42343007"], "250": ["SNOMED/44054006"]},
                      icd9proc=[], med={"THYR06": ["RxNorm/10582"]}, history={"HTN": ["SNOMED/38341003"]},
                      visit={"clinic": "Visit/OP", "admission": "Visit/IP"})
            (Path(t) / "map.json").write_text(json.dumps(mp))
            CL.main(["timeline", "--map", f"{t}/map.json", "--root", str(root)])
            env.update(CUDA_VISIBLE_DEVICES="", LD_PRELOAD=str(MOS / "lib" / "libstdc++.so.6"))
            env.pop("PYTHONPATH", None)
            outs = {}
            for mode in ("real", "shim"):
                env["CHS_CLMBR_FORCE_SHIM"] = "1" if mode == "shim" else "0"
                r = subprocess.run([str(MOS / "bin" / "python"), str(HERE.parent / "scripts" / "bdc" / "chs_clmbr.py"), "encode",
                                    "--model-root", str(MODEL), "--limit", "100000", "--verify", "20", "--device", "cpu",
                                    "--threads", "4"], env=env, cwd=t, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr[-3000:])
                rep = json.loads((Path(t) / "o" / "chs_clmbr" / "encode_smoke.json").read_text())
                self.assertEqual(rep["xformers_shim"], mode == "shim")
                self.assertTrue(rep["model_sha256_ok"])
                self.assertGreater(rep["prefix_check_n"], 0)
                self.assertLess(rep["prefix_check_max_abs_diff"], 1e-3)
                outs[mode] = pd.read_parquet(Path(t) / "r" / "chs_clmbr_smoke.parquet").set_index("row").sort_index()
            self.assertLess(float((outs["real"] - outs["shim"]).abs().max().max()), 1e-4)


if __name__ == "__main__":
    unittest.main()
