#!/usr/bin/env bash
# Separate Python environment for CHS CLMBR-T encoding on BDC (CPU; femr 0.2.3 / meds 0.1.3 as at Yale and MIMIC-IV).
# Kept apart from /sbgenomics/workspace/pylib so torch/numpy versions never clash with the analysis scripts.
# xformers is NOT installed (its wheels pull a CUDA torch); scripts/bdc/chs_clmbr.py uses scripts/bdc/xformers_shim.
# Usage: bash scripts/bdc/setup_clmbr_env.sh [/sbgenomics/workspace/clmbr-env]
set -euo pipefail
ENV="${1:-/sbgenomics/workspace/clmbr-env}"
unset PYTHONPATH
PY="${PYTHON:-python3}"
"$PY" -m venv "$ENV"
"$ENV/bin/python" -m pip install --quiet --upgrade pip
"$ENV/bin/python" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
# numpy 1.x as at Yale (mosaic env); pip pyarrow >= 20 and datasets >= 4 need numpy 2, so they are capped too
if ! "$ENV/bin/python" -m pip install --quiet "femr==0.2.3" "meds==0.1.3" "transformers==4.44.2" "numpy<2" \
      "pyarrow>=15,<20" "datasets>=2.15,<4" "pandas<3" huggingface_hub safetensors msgpack; then
  echo "numpy<2 not installable on this Python; retrying without the pin" >&2
  "$ENV/bin/python" -m pip install --quiet "femr==0.2.3" "meds==0.1.3" "transformers==4.44.2" \
      pandas pyarrow huggingface_hub safetensors msgpack
fi
"$ENV/bin/python" - <<'EOF'
import importlib.metadata as m, sys
print(sys.version.split()[0], {p: m.version(p) for p in ("femr", "meds", "torch", "transformers", "numpy", "pyarrow", "pandas")})
import femr.models.tokenizer, femr.models.processor  # noqa: F401
print("femr imports OK (transformer module needs the xformers shim, loaded by chs_clmbr.py)")
EOF
