"""v1 audit: print aggregate values behind paper2.md Results numbers (S32 unless stated)."""
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
C = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core/"
S = pd.read_csv(C + "sensitivity.csv"); F = pd.read_csv(C + "flagscv.csv"); R = pd.read_csv(C + "retention_sens.csv")
HD = pd.read_csv(C + "headline_domains.csv")
def r(con, cfg="main", st="S32", df=S):
    x = df[(df.set == st) & (df.config == cfg) & (df.contrast == con)]; assert len(x) == 1, (con, cfg, st, len(x)); return x.iloc[0]
cols = ["m54_b", "m54_a", "relred54", "relred54_lo", "relred54_hi", "m54_better", "m54_p", "m54_cluster_p", "q_m54_p_fam", "lt01_54_b", "lt01_54_a", "relred58"]
acols = ["absd_b", "absd_a", "absd_b_pair", "absd_a_pair", "n_agree_pair", "absd_better", "absd_p", "absd_cluster_p", "q_absd_p_fam", "bshuf_p", "q_bshuf_p_fam", "b_r", "a_r", "b_ea", "a_ea", "b_cons", "a_cons", "a_retain", "b_retain"]
def show(cons, cfgs=("main",), st="S32", df=S, c=cols):
    rows = []
    for cfg in cfgs:
        for k in cons:
            x = r(k, cfg, st, df); rows.append(pd.Series({"cfg": cfg, "contrast": k, **{z: x[z] for z in c}}))
    print(pd.DataFrame(rows).round(4).to_string(index=False))
P5 = ["P5: ECG vs base", "P5: CLMBR vs base", "P5: ECG+CLMBR vs base", "P5: shufECG vs base", "P5: shufCLMBR vs base", "P5: CLMBR vs ECG",
      "P5: ECG+CLMBR vs CLMBR", "P5: ECG+CLMBR vs ECG", "P5: CLMBR32 vs base"]
print("## Covariate balance with PS-CVD5"); show(P5)
print("## ladder"); show(["P1: ECG vs base", "P1: CLMBR vs base", "P1: ECG+CLMBR vs base", "P1: CLMBR vs ECG", "hdPS200: ECG vs base", "hdPS200: ECG vs shufECG",
                          "hdPS200: CLMBR vs base", "hdPS200: CLMBR vs ECG", "Flags: ECG vs base", "Flags: CLMBR vs base", "clinical: ECG vs base", "clinical: CLMBR vs base"])
print("## learned vs hand-built"); show(["P1+CLMBR vs Flags base", "P1+CLMBR32 vs Flags base", "P1+CLMBR vs hdPS200 base", "P5+CLMBR vs hdPS200 base", "P5+CLMBR vs clinical base"])
show(["P1+CLMBR vs Flags base"], c=acols)
show(["P5+CLMBR vs clinical base", "P1+CLMBR vs Flags base", "P1+CLMBR vs hdPS200 base"], cfgs=("gbm", "iptw"))
print("## flagscv"); print(F[["set", "set_k", "config", "contrast", "relred54", "relred54_lo", "relred54_hi", "m54_better", "m54_p", "absd_b_pair", "absd_a_pair", "absd_better", "absd_p", "bshuf_p", "b_retain", "a_retain"]].round(4).to_string(index=False))
print("## agreement"); show(["P5: ECG vs base", "P5: CLMBR vs base", "P5: ECG+CLMBR vs base", "P5: shufECG vs base", "P5: shufCLMBR vs base"], c=acols)
print("## replication"); show(["P5: ECG vs base", "P5: CLMBR vs base", "P5: ECG+CLMBR vs base", "P5: shufECG vs base", "P5: CLMBR vs ECG", "P5: ECG+CLMBR vs CLMBR"], cfgs=("cal01", "m13", "iptw", "overlap", "gbm"))
show(["P5: ECG vs base", "P5: CLMBR vs base", "P5: ECG+CLMBR vs base"], cfgs=("main", "cal01", "m13", "iptw", "overlap", "gbm"), c=["absd_p", "q_absd_p_fam", "bshuf_p", "q_bshuf_p_fam"])
print("## S38"); show(["P5: ECG vs base", "P5: CLMBR vs base", "P5: ECG+CLMBR vs base", "P1+CLMBR vs Flags base"], st="S38")
s38 = S[(S.set == "S38") & ((S.q_absd_p_fam < .05) | (S.q_bshuf_p_fam < .05) | (S.q_cons_p_fam < .05))]
print("S38 agreement rows q<.05:", len(s38), s38[["config", "contrast", "q_absd_p_fam", "q_bshuf_p_fam"]].round(4).to_string(index=False))
print("## retention_sens"); print(R.round(4).to_string(index=False))
print("## domains P5 main"); d = HD[(HD.set == "S32") & (HD.contrast.isin(["P5: ECG vs base", "P5: CLMBR vs base", "P5: CLMBR vs ECG"]))]
print(d[d.config.isin(["main", "m13", "overlap", "cal01", "gbm", "iptw"])][["config", "contrast", "domain", "relred", "relred_lo", "relred_hi", "p", "q_domain_fam"]].round(4).to_string(index=False))
