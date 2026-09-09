"""
scripts/drug_explorer_app.py

Streamlit app for interactive drug_master exploration.
Run on cluster, access via SSH tunnel:
    cluster:  streamlit run scripts/drug_explorer_app.py -- --drug-master /path/to/drug_master_v2.parquet
    local:    ssh -L 8501:localhost:8501 <cluster>
    browser:  http://localhost:8501

Features:
  - Drug search: filter by keyword (searches drug_name + generic_name)
  - Timeline: prescriptions per month, grouped by setting / cohort / order_class
  - Delta-time mode: time relative to each patient's first prescription of the drug
  - Knobs: date range slider, setting filter, cohort filter, bin width
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ── CLI args (passed after --) ────────────────────────────────────────────────
def _get_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--drug-master", default="",
                   help="Path to drug_master_v2.parquet")
    # Streamlit passes its own args before --, so we parse only what's after
    try:
        idx = sys.argv.index("--")
        args, _ = p.parse_known_args(sys.argv[idx + 1:])
    except ValueError:
        args, _ = p.parse_known_args([])
    return args


@st.cache_data(show_spinner="Loading drug master...")
def load_dm(path: str) -> pd.DataFrame:
    dm = pd.read_parquet(path)
    dm["order_date"] = pd.to_datetime(dm["order_date"], errors="coerce")
    dm["drug_upper"] = dm["drug_name"].astype(str).str.upper()
    if "generic_name" in dm.columns:
        dm["generic_upper"] = dm["generic_name"].astype(str).str.upper()
    else:
        dm["generic_upper"] = ""
    return dm


def main() -> None:
    st.set_page_config(
        page_title="Drug Master Explorer",
        page_icon="💊",
        layout="wide",
    )

    cli = _get_args()

    st.title("Drug Master Explorer")
    st.caption("Aggregate view only — no patient-level data displayed")

    # ── Sidebar: data path ────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Data")
        dm_path = st.text_input(
            "drug_master.parquet path",
            value=cli.drug_master or "",
            placeholder="/mnt/raid0/rbc58/mm_vhd/drug/drug_master_v2.parquet",
        )

    if not dm_path or not Path(dm_path).exists():
        st.warning("Enter a valid drug_master.parquet path in the sidebar.")
        return

    dm = load_dm(dm_path)

    # ── Sidebar: filters ──────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Filters")

        drug_query = st.text_input(
            "Drug keyword (e.g. SACUBITRIL, METOPROLOL, ENALAPRIL)",
            value="SACUBITRIL|ENTRESTO",
        )

        settings_available = sorted(dm["setting"].dropna().unique().tolist())
        settings_sel = st.multiselect(
            "Setting", settings_available, default=settings_available
        )

        cohorts_available = sorted(dm["cohort"].dropna().unique().tolist())
        cohorts_sel = st.multiselect(
            "Cohort", cohorts_available, default=cohorts_available
        )

        if "order_class" in dm.columns:
            oc_vals = ["(all)"] + sorted(
                dm["order_class"].dropna().astype(str).unique().tolist()
            )
            order_class_sel = st.selectbox("Order class", oc_vals)
        else:
            order_class_sel = "(all)"

        min_date = dm["order_date"].min().date()
        max_date = dm["order_date"].max().date()
        date_range = st.slider(
            "Date range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
        )

        st.header("Display")
        bin_width = st.selectbox(
            "Time bin width",
            ["Month", "Quarter", "Year"],
            index=0,
        )
        color_by = st.selectbox(
            "Color by",
            ["setting", "cohort", "order_class"],
            index=0,
        )
        delta_mode = st.checkbox(
            "Delta-time mode (x = days from patient's first Rx)",
            value=False,
        )
        if delta_mode:
            delta_bin_days = st.slider(
                "Delta-time bin width (days)",
                min_value=7, max_value=365, value=30, step=7,
            )
        show_raw_counts = st.checkbox("Show raw counts table", value=False)

    # ── Filter data ───────────────────────────────────────────────────────────
    mask = pd.Series(True, index=dm.index)

    if drug_query.strip():
        pattern = drug_query.strip().upper()
        mask &= (
            dm["drug_upper"].str.contains(pattern, regex=True, na=False)
            | dm["generic_upper"].str.contains(pattern, regex=True, na=False)
        )

    if settings_sel:
        mask &= dm["setting"].isin(settings_sel)

    if cohorts_sel:
        mask &= dm["cohort"].isin(cohorts_sel)

    if order_class_sel != "(all)" and "order_class" in dm.columns:
        mask &= dm["order_class"].astype(str) == order_class_sel

    mask &= dm["order_date"].dt.date >= date_range[0]
    mask &= dm["order_date"].dt.date <= date_range[1]
    mask &= dm["order_date"].notna()

    sub = dm[mask].copy()

    # ── Summary bar ───────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Matching records", f"{len(sub):,}")
    col2.metric("Unique patients", f"{sub['MRN'].nunique():,}")
    col3.metric("Unique drug names", f"{sub['drug_name'].nunique():,}")
    col4.metric(
        "Date range",
        f"{sub['order_date'].min().date()} -> {sub['order_date'].max().date()}"
        if len(sub) else "—",
    )

    if sub.empty:
        st.warning("No records match the current filters.")
        return

    # ── Timeline or Delta-time plot ───────────────────────────────────────────
    st.subheader(
        "Prescriptions over time"
        if not delta_mode
        else "Prescriptions relative to first Rx (delta-time)"
    )

    if delta_mode:
        # Compute days from each patient's first matching prescription
        first_rx = sub.groupby("MRN")["order_date"].min().rename("first_rx_date")
        sub = sub.join(first_rx, on="MRN")
        sub["delta_days"] = (sub["order_date"] - sub["first_rx_date"]).dt.days
        sub["bin"] = (sub["delta_days"] // delta_bin_days) * delta_bin_days

        counts = (
            sub.groupby(["bin", color_by])
            .size()
            .reset_index(name="count")
        )
        fig = px.bar(
            counts, x="bin", y="count", color=color_by,
            labels={"bin": f"Days from first Rx (binned {delta_bin_days}d)", "count": "Records"},
            title=f"Records by delta-time ({drug_query})",
            barmode="stack",
        )
        fig.update_xaxes(title=f"Days from first Rx")
    else:
        freq_map = {"Month": "ME", "Quarter": "QE", "Year": "YE"}
        sub["bin"] = sub["order_date"].dt.to_period(
            freq_map[bin_width][0]
        ).dt.to_timestamp()

        counts = (
            sub.groupby(["bin", color_by])
            .size()
            .reset_index(name="count")
        )
        fig = px.bar(
            counts, x="bin", y="count", color=color_by,
            labels={"bin": f"Date ({bin_width})", "count": "Records"},
            title=f"Records per {bin_width.lower()} ({drug_query})",
            barmode="stack",
        )

    fig.update_layout(height=450, legend_title=color_by)
    st.plotly_chart(fig, use_container_width=True)

    # ── Drug name breakdown ───────────────────────────────────────────────────
    st.subheader("Top matching drug names")
    top_drugs = (
        sub["drug_name"].value_counts().head(30).reset_index()
    )
    top_drugs.columns = ["drug_name", "count"]
    fig2 = px.bar(
        top_drugs, x="count", y="drug_name", orientation="h",
        labels={"drug_name": "", "count": "Records"},
        height=max(300, 20 * len(top_drugs)),
    )
    fig2.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig2, use_container_width=True)

    # ── Setting breakdown pie ─────────────────────────────────────────────────
    st.subheader("Records by setting")
    setting_counts = sub["setting"].value_counts().reset_index()
    setting_counts.columns = ["setting", "count"]
    fig3 = px.pie(
        setting_counts, names="setting", values="count",
        title="Setting distribution",
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Raw counts table (opt-in) ─────────────────────────────────────────────
    if show_raw_counts:
        st.subheader("Counts table (aggregate)")
        grp_cols = ["drug_name", "setting", "cohort"]
        if "order_class" in sub.columns:
            grp_cols.append("order_class")
        tbl = (
            sub.groupby(grp_cols)
            .agg(count=("MRN", "size"), unique_patients=("MRN", "nunique"))
            .reset_index()
            .sort_values("count", ascending=False)
        )
        st.dataframe(tbl, use_container_width=True)


if __name__ == "__main__":
    main()
