import torch

from . import fmha  # noqa: F401
from .fmha.attn_bias import AttentionBias  # noqa: F401


def memory_efficient_attention(q, k, v, attn_bias=None, p=0.0, scale=None):
    """Reference attention in BMHK layout (float32), used if the model runs on a GPU without real xformers."""
    B, M, H, K = q.shape
    scale = scale if scale is not None else 1 / K ** 0.5
    qh, kh, vh = (t.permute(0, 2, 1, 3).float() for t in (q, k, v))
    att = (qh * scale) @ kh.transpose(-2, -1)
    if attn_bias is not None:
        att = att + attn_bias.materialize((B, H, M, k.shape[1]), device=q.device, dtype=torch.float32)
    return (att.softmax(-1) @ vh).permute(0, 2, 1, 3).to(q.dtype)
