"""BDC probe on a synthetic Seven Bridges-like tree (MUSE XML, CSV, dbGaP txt.gz, zip, data dictionary)."""
import base64
import gzip
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "bdc"))
import bdc_common as BC  # noqa: E402
import bdc_probe as P  # noqa: E402

LEADS = ["I", "II", "V1", "V2", "V3", "V4", "V5", "V6"]


def muse_xml(rng, fs=500, n=5000):
    leads = []
    for ld in LEADS:
        a = (rng.normal(0, 200, n) / 4.88).astype("<i2")
        leads.append(f"<LeadData><LeadSampleCountTotal>{n}</LeadSampleCountTotal><LeadAmplitudeUnitsPerBit>4.88"
                     f"</LeadAmplitudeUnitsPerBit><LeadAmplitudeUnits>MICROVOLTS</LeadAmplitudeUnits><LeadID>{ld}</LeadID>"
                     f"<WaveFormData>{base64.b64encode(a.tobytes()).decode()}</WaveFormData></LeadData>")
    return (f"<RestingECG><PatientDemographics><PatientID>SECRET123</PatientID></PatientDemographics>"
            f"<TestDemographics><AcquisitionDate>01-01-2012</AcquisitionDate><AcquisitionDevice>MAC1200</AcquisitionDevice>"
            f"</TestDemographics><Diagnosis><DiagnosisStatement><StmtText>SECRET TEXT</StmtText></DiagnosisStatement></Diagnosis>"
            f"<Waveform><WaveformType>Rhythm</WaveformType><SampleBase>{fs}</SampleBase>{''.join(leads)}</Waveform>"
            f"</RestingECG>")


class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.root = t / "project-files"
        os.environ["BDC_TTE_OUT"] = str(t / "out")
        rng = np.random.default_rng(0)
        ecg = self.root / "img_SPRINT_GRU" / "data"
        ecg.mkdir(parents=True)
        for i in range(25):
            (ecg / f"SPRINT_ECG_VISIT01_{2010 + i % 3}0101_{i:05d}.xml").write_text(muse_xml(rng))
        whi = self.root / "img_WHI_HMB"
        whi.mkdir()
        with zipfile.ZipFile(whi / "WHI_ECG_VISIT03.zip", "w") as z:
            for i in range(12):
                z.writestr(f"data/WHI_ECG_VISIT03_19000101_{i:05d}.xml", muse_xml(rng))
        ph = self.root / "sprint_pheno"
        ph.mkdir()
        D = pd.DataFrame({"MASKID": [f"S{i}" for i in range(200)], "INTENSIVE": rng.integers(0, 2, 200),
                          "EGFR": rng.normal(70, 20, 200), "SEX": rng.choice(["F", "M"], 200)})
        D.loc[:5, "EGFR"] = np.nan
        D.to_csv(ph / "baseline.csv", index=False)
        (ph / "baseline.sas7bdat").write_bytes(b"not really SAS")  # twin of baseline.csv: must be skipped
        (ph / "sprint_a_20230622145936p959_14.sas7bdat").write_bytes(b"x")  # cloning artifact: skipped
        txt = "# dbGaP header line\n# another\n" + D.to_csv(sep="\t", index=False)
        (ph / "phs000200.v12.pht000998.v6.p3.c1.WHI_test.HMB-IRB.txt.gz").write_bytes(gzip.compress(txt.encode()))
        with zipfile.ZipFile(ph / "bundle.zip", "w") as z:
            z.writestr("outcomes.csv", D[["MASKID", "INTENSIVE"]].to_csv(index=False))
        pd.DataFrame({"variable": ["EGFR"], "description": ["eGFR"]}).to_csv(ph / "data_dictionary.csv", index=False)
        # imaging 'DD_' file that is really a per-file table with subject IDs: must be summarised, never copied
        pd.DataFrame({"SUBJECT_ID": [f"SUBJ{i:04d}" for i in range(4000)], "visit": 1}).to_csv(
            ph / "DD_WHI_Imaging_c1.csv", index=False)

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("BDC_TTE_OUT", None)

    def test_probe(self):
        P.main(["--roots", str(self.root), "--only", "files,tables,xml,pfb", "--xml-sample", "10"])
        out = BC.out_root() / "probe"
        R = json.loads((out / "probe.json").read_text())
        self.assertEqual(R["errors"], {})
        v = {(x["study"], x["visit"]): x["n_files"] for x in R["files"]["ecg_xml_by_visit"]}
        self.assertEqual(v[("SPRINT", "VISIT01")], 25)
        self.assertEqual(v[("WHI", "VISIT03")], 12)
        self.assertEqual(R["xml"]["WHI"]["n_sampled"], 10)
        self.assertEqual(R["xml"]["WHI"]["parse_errors"], {})
        yrs = {x["year"]: x["n_files"] for x in R["files"]["ecg_xml_by_year"]}
        self.assertEqual(yrs["2010"], "1-10")  # 9 files -> suppressed
        T = {t["table"]: t for t in R["tables"]["tables"]}
        self.assertIn("sprint_pheno/bundle.zip::outcomes.csv", T)
        self.assertFalse(any(k.endswith(".sas7bdat") for k in T))
        whi = [k for k in T if "pht000998" in k][0]
        self.assertEqual(T[whi]["sheets"][""]["n_cols"], 4)  # comment lines skipped
        cols = {c["column"]: c for c in T["sprint_pheno/baseline.csv"]["sheets"][""]["columns"]}
        self.assertTrue(cols["MASKID"]["id_like"])
        self.assertNotIn("values", cols["MASKID"])
        self.assertAlmostEqual(cols["EGFR"]["nonmissing_frac"], 0.97, places=2)
        self.assertTrue(T["sprint_pheno/data_dictionary.csv"]["documentation"])
        self.assertTrue(any((out / "docs_extract").iterdir()))
        X = R["xml"]["SPRINT"]
        self.assertEqual(X["n_sampled"], 10)
        w = X["waveforms"]["Rhythm"]
        self.assertEqual(w["n_leads"], {"8": 10})
        self.assertEqual(w["sample_count_matches_declared"], 80)
        self.assertEqual(X["acquisition_years"], {"2012": 10})
        text = (out / "probe.json").read_text() + (out / "probe.md").read_text() + (out / "probe_columns.tsv").read_text()
        self.assertFalse(T["sprint_pheno/DD_WHI_Imaging_c1.csv"]["documentation"])
        self.assertEqual(len(list((out / "docs_extract").iterdir())), 1)
        for secret in ("SECRET123", "SECRET TEXT", "S17", "_00017", "SUBJ0007"):
            self.assertNotIn(secret, text)


if __name__ == "__main__":
    unittest.main()
