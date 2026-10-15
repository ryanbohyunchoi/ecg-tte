"""SPRINT cohort/linkage builder on a synthetic BioLINCC + Gen3 PFB tree (known HR, wrapped subject IDs, follow-up ECGs)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "bdc"))
import sprint_cohort as SC  # noqa: E402


def make_tree(root: Path, n=3000, seed=3):
    rng = np.random.default_rng(seed)
    data = root / "export_A" / "drs" / "b" / "BioLINCC" / "SPRINT_2023a"
    csv = data / "SPRINT" / "data" / "CSV"
    pop = data / "SPRINT-POP" / "data"
    bio = data / "Ancillary_Studies" / "Biomarkers"
    for d in (csv, pop, bio):
        d.mkdir(parents=True)
    ids = [f"S{i:05d}" for i in range(n)]
    arm = rng.integers(0, 2, n)
    egfr = rng.normal(70, 20, n)
    pd.DataFrame(dict(MASKID=ids, RANDASSIGN=arm)).to_csv(csv / "keyvar.csv", index=False)
    B = pd.DataFrame(dict(MASKID=ids, INTENSIVE=arm, AGE=rng.integers(50, 90, n), FEMALE=rng.integers(0, 2, n),
                          RACE_BLACK=rng.integers(0, 2, n), RACE4="WHITE", SBP=rng.normal(140, 15, n), DBP=78,
                          N_AGENTS=2, SMOKE_3CAT=1, ASPIRIN=1, STATIN=0, EGFR=egfr, SCREAT=1.0, SUB_CKD=0, SUB_CVD=0,
                          SUB_CLINICALCVD=0, SUB_SUBCLINICALCVD=0, CHR=190, GLUR=97, HDL=50, TRR=110, UMALCR=9.5,
                          BMI=29, RISK10YRS=18))
    B.to_csv(pop / "baseline.csv", index=False)
    pd.DataFrame(dict(MASKID=ids, HRAVG=67, LVHCOMPECG=0, CVDPOINTS=17, CIGSMOKER=0)).to_csv(csv / "incl_excl.csv", index=False)
    pd.DataFrame(dict(MASKID=ids, ATRIALFIB=0, CONHEARTFAIL=0, HEARTATT=0, EDUCATION=7)).to_csv(csv / "bl_history.csv", index=False)
    pd.DataFrame(dict(MASKID=ids * 2, VISITCODE=["RZ"] * n + ["12M"] * n, NT_PROBNP=100.0, HSTNI=4.0)).to_csv(
        bio / "sprint_biomarker_as_shared.csv", index=False)
    # outcomes with true HR 0.7 for the intensive arm
    lam = 0.0002 * np.exp(np.log(0.7) * arm)
    T = rng.exponential(1 / lam)
    cens = 1600
    O = pd.DataFrame(dict(MASKID=ids, EVENT_PRIMARY=(T < cens).astype(int), T_PRIMARY=np.minimum(T, cens).round(),
                          EVENT_DEATH=0, T_DEATH=cens, EVENT_PRIMARYORDEATH=(T < cens).astype(int),
                          T_PRIMARYORDEATH=np.minimum(T, cens).round(), EVENT_HF=0, T_HF=cens, EVENT_CVDDEATH=0, T_CVDDEATH=cens))
    O.to_csv(pop / "outcomes.csv", index=False)
    for nm in ("primarysurv", "alldeath"):
        pd.DataFrame(dict(MASKID=ids, EVENT=O.EVENT_PRIMARY, EVENTDAYS=O.T_PRIMARY, EVENTDAYS_POSTI=0)).to_csv(csv / f"{nm}.csv", index=False)
    # reading-centre ECGs: baseline (day 0) for all but the last 100; 2-year ECG for even participants
    rows, files, sub = [], [], []
    serial = 0
    for i, m in enumerate(ids):
        days = ([0] if i < n - 100 else []) + ([730] if i % 2 == 0 else [])
        y0 = 2011 + i % 3
        for d in days:
            rows.append(dict(MASKID=m, ECGDAYS=d, QRSDURATION=92, CV=1400, CVP=150, SL=1900, LVHCV=0, LVHCVP=0,
                             LVHMC=0, LVHSL=0, LVHANY3=0, AFIBFLUTTER=0, QUAL=0))
            serial += 1
            files.append(dict(id=f"f{serial}", **{"object.file_name": f"SPRINT_ECG_VISIT01_{y0 + d // 365}0101_{serial:05d}.xml",
                                                   "object.object_id": f"dg.4503/x{serial}", "relations.dst_id": f"sub{i}"}))
        sub.append({"id": f"sub{i}", "object.submitter_id": f"SPRINT_{m}", "object.participant_id": i + 100000})
    pd.DataFrame(rows).to_csv(csv / "ecg.csv", index=False)
    tsv = root / "export_B" / "tsv"
    tsv.mkdir(parents=True)
    pd.DataFrame(sub).to_csv(tsv / "subject.tsv", sep="\t", index=False)
    F = pd.DataFrame(files)
    F.to_csv(tsv / "imaging_file.tsv", sep="\t", index=False)
    xml = root / "export_B" / "drs" / "img" / "data"
    xml.mkdir(parents=True)
    for f in F["object.file_name"]:
        (xml / f).write_text("<RestingECG/>")
    return n


class CohortTest(unittest.TestCase):
    def test_build(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "project-files"
            n = make_tree(root)
            os.environ["BDC_TTE_OUT"] = str(Path(t) / "out")
            os.environ["BDC_RESTRICTED"] = str(Path(t) / "restricted")
            SC.main(["--root", str(root)])
            R = json.loads((Path(t) / "out" / "sprint_cohort" / "report.json").read_text())
            self.assertNotIn("linkage_error", R)
            self.assertEqual(R["subject_key_column"], "object.submitter_id")  # token match through 'SPRINT_<MASKID>'
            self.assertEqual(R["baseline_xml"]["assigned"], n - 100)
            self.assertEqual(R["aligned_year_spacing_consistent"]["files"], R["aligned_year_spacing_consistent"]["consistent"])
            h = R["randomized_hr"]["primary (SPRINT-POP; published 0.75, 0.64-0.89)"]
            self.assertTrue(h["lo"] < 0.7 < h["hi"], h)
            self.assertLess(R["max_abs_smd_between_randomized_arms"], 0.1)
            text = (Path(t) / "out" / "sprint_cohort" / "report.json").read_text()
            self.assertNotIn("S00017", text)
            C = pd.read_parquet(Path(t) / "restricted" / "sprint_cohort.parquet") if (
                Path(t) / "restricted" / "sprint_cohort.parquet").exists() else pd.read_pickle(Path(t) / "restricted" / "sprint_cohort.pkl")
            self.assertEqual(len(C), n)
            self.assertEqual(int(C.HAS_BASELINE_XML.sum()), n - 100)
            # the assigned file is the participant's earliest (baseline) file
            self.assertTrue(C.ECG_FILE_YEAR.dropna().between(2011, 2013).all())

    def test_cox_matches_lifelines(self):
        try:
            from lifelines import CoxPHFitter
        except ImportError:
            self.skipTest("lifelines not installed")
        rng = np.random.default_rng(1)
        x = rng.integers(0, 2, 800)
        t = np.round(rng.exponential(1 / np.exp(-0.4 * x)) * 50)  # rounding creates ties
        e = (rng.random(800) < 0.7).astype(int)
        hr = SC.cox_binary(pd.Series(t), pd.Series(e), pd.Series(x))
        f = CoxPHFitter().fit(pd.DataFrame(dict(t=t, e=e, x=x)), "t", "e")
        # lifelines uses Efron ties; Breslow differs slightly with ties
        self.assertAlmostEqual(np.log(hr[0]), float(f.params_["x"]), delta=0.02)


if __name__ == "__main__":
    unittest.main()
