"""Minimal pure-PyTorch stand-in for the parts of xformers that femr 0.2.3 uses (CHS CLMBR-T on BDC, CPU).

femr.models.transformer imports xformers for BlockDiagonalMask.from_seqlens(...).make_local_attention(w) and, on GPU only,
memory_efficient_attention. On CPU femr already uses its reference attention with the materialised mask, so this shim
only has to materialise the same mask (block-diagonal, causal, local window: key j is visible from query i iff both are
in the same sequence, j <= i and i - j < w). tests/test_bdc_chs_clmbr.py checks it against real xformers.
Put on sys.path ONLY when real xformers is not installed (scripts/bdc/chs_clmbr.py does this).
"""
__version__ = "0.0.0+chs-shim"
