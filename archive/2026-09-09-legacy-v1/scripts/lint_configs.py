"""
scripts/lint_configs.py

Schema linter for all configs/*.yaml files.
Runs validate_config() on every non-underscore YAML file.
Prints a pass/fail report and exits non-zero if any config is invalid.

Usage:
    python scripts/lint_configs.py                     # lint all configs/*.yaml
    python scripts/lint_configs.py configs/comet.yaml  # lint specific file
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cohort_utils import load_trial_config


def main() -> None:
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        cfg_dir = Path(__file__).resolve().parent.parent / "configs"
        paths = sorted(p for p in cfg_dir.glob("*.yaml") if not p.name.startswith("_"))

    if not paths:
        print("No YAML files found.")
        sys.exit(0)

    passed: list[str] = []
    failed: list[tuple[str, str]] = []

    for path in paths:
        try:
            cfg = load_trial_config(str(path))
            passed.append(path.name)
            key  = cfg["trial"].get("key", "?")
            name = cfg["trial"].get("name", "?")
            arms = [a["name"] for a in cfg["arms"]]
            ecg  = cfg["ecg"].get("window_days", "?")
            comps = [c["type"] for c in cfg["endpoint"]["primary"]["components"]]
            print(f"  ✓ {path.name:<30} key={key}  arms={arms}  ecg={ecg}d  ep={comps}")
        except Exception as e:
            failed.append((path.name, str(e)))
            print(f"  ✗ {path.name:<30} ERROR: {e}")

    print(f"\n{len(passed)} passed  {len(failed)} failed")
    if failed:
        print("\nFailed configs:")
        for name, err in failed:
            print(f"  {name}: {err}")
        sys.exit(1)
    else:
        print("All configs valid.")


if __name__ == "__main__":
    main()
