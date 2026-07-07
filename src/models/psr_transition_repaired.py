"""
PSR Transition Head -- Repaired Architecture
=============================================
Replaces the original PSR transition head with a repaired version that:
  1. Re-initializes output bias to 0.0 (was -1.0)
  2. Replaces ReLU(inplace=True) with LeakyReLU(0.01)
  3. Uses Xavier/Glorot uniform initialization for all linear layers

Architecture (same as original):
  FPN P3 [B, 256, H/8, W/8]  --+
  FPN P4 [B, 256, H/16, W/16] --+-- concat(768) -> MLP -> [B, 256] -> Transformer -> Heads
  FPN P5 [B, 256, H/32, W/32] --+

  - Per-frame MLP: Linear(768, 512) -> LayerNorm -> GELU -> Dropout(0.1)
                   -> Linear(512, 256) -> LayerNorm
  - Causal Transformer: 3 layers, 4 heads, d_model=256, FFN=1024,
                        pre-norm, GELU, dropout=0.2
  - Per-component heads: 11 separate Sequential(Linear(256, 64), LeakyReLU(0.01),
                          Dropout(0.06), Linear(64, 1))
  - Output: [B, 12] where [..., :11] = component logits, [..., 11:] = confidence
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.init import xavier_uniform_, zeros_, constant_


# ============================================================================
# Repaired Transition Heads (per-component output heads)
# ============================================================================


class TransitionHeads(nn.Module):
    """
    Per-component output heads.

    REPAIRED (vs original):
      - Activation: LeakyReLU(0.01)  [was ReLU(inplace=True)]
      - Final Linear bias init: 0.0  [was -1.0]
      - All Linear layers: Xavier/Glorot uniform init
    """

    def __init__(
        self,
        num_components: int = 11,
        hidden_dim: int = 64,
        input_dim: int = 256,
        dropout: float = 0.06,
    ):
        super().__init__()
        self.num_components = num_components

        heads = []
        for _ in range(num_components):
            heads.append(
                nn.Sequential(
                    nn.Linear(input_dim, hidden_dim),
                    nn.LeakyReLU(negative_slope=0.01),  # REPAIRED: was ReLU(inplace=True)
                    nn.Dropout(dropout),
                    nn.Linear(hidden_dim, 1),
                )
            )
        self.heads = nn.ModuleList(heads)

        self._init_weights()

    def _init_weights(self):
        """Xavier/Glorot uniform init for all linear layers (REPAIRED)."""
        for head in self.heads:
            for m in head.modules():
                if isinstance(m, nn.Linear):
                    # Xavier/Glorot uniform init
                    xavier_uniform_(m.weight, gain=1.0)
                    if m.out_features == 1:
                        # Output bias: 0.0 (REPAIRED: was -1.0)
                        zeros_(m.bias)
                    else:
                        zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, 256] transformer output

        Returns:
            logits: [B, 12] where [:, :11] = component logits, [:, 11:] = confidence
        """
        component_logits = []
        for head in self.heads:
            component_logits.append(head(x))  # [B, 1]

        # [B, 11] component logits
        component_logits = torch.cat(component_logits, dim=-1)

        # Confidence: max sigmoid across components
        confidence = torch.sigmoid(component_logits).max(dim=-1, keepdim=True).values

        return torch.cat([component_logits, confidence], dim=-1)  # [B, 12]


# ============================================================================
# Feature Encoder (Per-frame MLP)
# ============================================================================


class TransitionFeatureEncoder(nn.Module):
    """
    Encodes FPN pyramid features (P3+P4+P5 -> concat 768-D) into
    a compact 256-D representation for the causal transformer.

    Architecture:
      Linear(768, 512) -> LayerNorm -> GELU -> Dropout(0.1)
      -> Linear(512, 256) -> LayerNorm
    """

    def __init__(
        self,
        feat_dim: int = 768,
        hidden_dim: int = 512,
        output_dim: int = 256,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(feat_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
            nn.LayerNorm(output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, 768] concat(GAP(P3), GAP(P4), GAP(P5))

        Returns:
            [B, 256] encoded features
        """
        return self.mlp(x)


# ============================================================================
# Causal Transformer
# ============================================================================


class CausalTransformerLayer(nn.Module):
    """
    Single causal transformer layer with pre-norm.

    Architecture:
      x -> LayerNorm -> MultiheadSelfAttention(causal) -> +x
      -> LayerNorm -> FFN(GELU) -> +x
    """

    def __init__(
        self,
        d_model: int = 256,
        nhead: int = 4,
        dim_feedforward: int = 1024,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.self_attn = nn.MultiheadAttention(
            d_model, nhead, dropout=dropout, batch_first=True
        )
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, dim_feedforward),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim_feedforward, d_model),
            nn.Dropout(dropout),
        )

    def forward(
        self,
        x: torch.Tensor,
        causal_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            x: [B, T, d_model]
            causal_mask: [T, T] causal mask or None (auto-generated)

        Returns:
            [B, T, d_model]
        """
        T = x.shape[1]
        if causal_mask is None:
            # Generate causal mask
            causal_mask = torch.triu(
                torch.full((T, T), float("-inf"), device=x.device), diagonal=1
            )

        # Pre-norm + self-attention
        x_norm = self.norm1(x)
        attn_out, _ = self.self_attn(x_norm, x_norm, x_norm, attn_mask=causal_mask)
        x = x + attn_out

        # Pre-norm + FFN
        x_norm = self.norm2(x)
        ffn_out = self.ffn(x_norm)
        x = x + ffn_out

        return x


class CausalTransformer(nn.Module):
    """
    Stack of causal transformer layers.

    3 layers, 4 heads, d_model=256, FFN=1024, pre-norm, GELU, dropout=0.2
    """

    def __init__(
        self,
        d_model: int = 256,
        nhead: int = 4,
        num_layers: int = 3,
        dim_feedforward: int = 1024,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.layers = nn.ModuleList(
            [
                CausalTransformerLayer(d_model, nhead, dim_feedforward, dropout)
                for _ in range(num_layers)
            ]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, T, d_model] -- T=1 during per-frame, T>1 during sequence batch

        Returns:
            [B, T, d_model] -- only the last timestep used for per-component heads
        """
        T = x.shape[1]
        causal_mask = torch.triu(
            torch.full((T, T), float("-inf"), device=x.device), diagonal=1
        )

        for layer in self.layers:
            x = layer(x, causal_mask)

        return x


# ============================================================================
# Full PSR Transition Model (Repaired)
# ============================================================================


class PSRTransitionModel(nn.Module):
    """
    Full PSR transition model with repaired transition heads.

    Flow:
      1. Encode FPN features (P3+P4+P5) -> 256-D embedding
      2. Apply causal transformer (T=1 no-op, T>1 temporal reasoning)
      3. Per-component transition heads -> [B, 12]
    """

    def __init__(
        self,
        fpn_channels: int = 256,
        feat_dim: int = 768,
        encoder_hidden: int = 512,
        encoder_output: int = 256,
        d_model: int = 256,
        nhead: int = 4,
        num_layers: int = 3,
        dim_feedforward: int = 1024,
        num_components: int = 11,
        head_hidden: int = 64,
        encoder_dropout: float = 0.1,
        transformer_dropout: float = 0.2,
        head_dropout: float = 0.06,
    ):
        super().__init__()
        self.fpn_channels = fpn_channels
        self.feat_dim = feat_dim

        # Per-frame encoder (FPN -> 256-D embedding)
        self.encoder = TransitionFeatureEncoder(
            feat_dim=feat_dim,
            hidden_dim=encoder_hidden,
            output_dim=encoder_output,
            dropout=encoder_dropout,
        )

        # Causal transformer for temporal reasoning
        self.transformer = CausalTransformer(
            d_model=d_model,
            nhead=nhead,
            num_layers=num_layers,
            dim_feedforward=dim_feedforward,
            dropout=transformer_dropout,
        )

        # Repaired per-component transition heads
        self.transition_heads = TransitionHeads(
            num_components=num_components,
            hidden_dim=head_hidden,
            input_dim=d_model,
            dropout=head_dropout,
        )

    @staticmethod
    def pool_fpn_features(
        p3: torch.Tensor,
        p4: torch.Tensor,
        p5: torch.Tensor,
    ) -> torch.Tensor:
        """
        GAP-pool FPN features and concatenate.

        Args:
            p3: [B, 256, H/8, W/8]
            p4: [B, 256, H/16, W/16]
            p5: [B, 256, H/32, W/32]

        Returns:
            [B, 768] concat(gap(p3), gap(p4), gap(p5))
        """
        pooled = []
        for feat in [p3, p4, p5]:
            # Global average pool over spatial dims
            pooled.append(feat.mean(dim=(-2, -1)))  # [B, 256]
        return torch.cat(pooled, dim=-1)  # [B, 768]

    def forward(
        self,
        p3: torch.Tensor,
        p4: torch.Tensor,
        p5: torch.Tensor,
        seq_length: int = 1,
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            p3: [B, 256, H/8, W/8] or [B*T, 256, ...] for T=1
            p4: [B, 256, H/16, W/16] same as above
            p5: [B, 256, H/32, W/32] same as above
            seq_length: temporal sequence length (1=per-frame, >1=sequence batch)

        Returns:
            [B, 12] transition logits
        """
        B = p3.shape[0]
        T = seq_length

        # GAP + concat
        x = self.pool_fpn_features(p3, p4, p5)  # [B, 768] or [B*T, 768]

        if T > 1:
            # Sequence batch: reshape to [B//T, T, 768]
            x = x.view(-1, T, self.feat_dim)

        # Encode to 256-D
        x = self.encoder(x)  # [B, 256] or [B//T, T, 256]

        if T > 1:
            # Apply causal transformer
            x = self.transformer(x)  # [B//T, T, 256]
            # Take only the last timestep for per-component heads
            x = x[:, -1, :]  # [B//T, 256]

        # Per-component transition heads
        logits = self.transition_heads(x)  # [B, 12] or [B//T, 12]

        return logits  # [B, 12]

    def forward_sequence(
        self,
        p3_seq: torch.Tensor,
        p4_seq: torch.Tensor,
        p5_seq: torch.Tensor,
    ) -> torch.Tensor:
        """
        Convenience wrapper for sequence batch forward.

        Args:
            p3_seq: [B, T, 256, H/8, W/8]
            p4_seq: [B, T, 256, H/16, W/16]
            p5_seq: [B, T, 256, H/32, W/32]

        Returns:
            [B, 12] transition logits
        """
        B, T = p3_seq.shape[:2]
        # Flatten to [B*T, ...]
        p3 = p3_seq.view(B * T, *p3_seq.shape[2:])
        p4 = p4_seq.view(B * T, *p4_seq.shape[2:])
        p5 = p5_seq.view(B * T, *p5_seq.shape[2:])
        return self.forward(p3, p4, p5, seq_length=T)
