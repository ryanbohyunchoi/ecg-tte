import torch


class AttentionBias:
    def materialize(self, shape, dtype=torch.float32, device="cpu"):
        raise NotImplementedError


class BlockDiagonalMask(AttentionBias):
    def __init__(self, seqlens, window=None, causal=False):
        self.seqlens = [int(s) for s in seqlens]
        self.window = window
        self.causal = causal

    @classmethod
    def from_seqlens(cls, q_seqlen, kv_seqlen=None):
        if kv_seqlen is not None and list(kv_seqlen) != list(q_seqlen):
            raise NotImplementedError("shim: query and key sequence lengths must match")
        return cls(q_seqlen)

    def make_causal(self):
        return BlockDiagonalCausalMask(self.seqlens, None, True)

    def make_local_attention(self, window_size):
        return BlockDiagonalCausalLocalAttentionMask(self.seqlens, int(window_size), True)

    def materialize(self, shape, dtype=torch.float32, device="cpu"):
        n = sum(self.seqlens)
        if shape[-1] != n or shape[-2] != n:
            raise ValueError("shim: mask shape does not match the sequence lengths")
        seq = torch.repeat_interleave(torch.arange(len(self.seqlens), device=device),
                                      torch.tensor(self.seqlens, device=device))
        i = torch.arange(n, device=device)
        ok = seq[:, None] == seq[None, :]
        if self.causal:
            ok &= i[None, :] <= i[:, None]
        if self.window is not None:
            ok &= (i[:, None] - i[None, :]) < self.window
        m = torch.zeros((n, n), dtype=dtype, device=device).masked_fill(~ok, float("-inf"))
        return m.expand(*shape).contiguous()


class BlockDiagonalCausalMask(BlockDiagonalMask):
    pass


class BlockDiagonalCausalLocalAttentionMask(BlockDiagonalCausalMask):
    pass
