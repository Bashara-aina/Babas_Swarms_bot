#!/usr/bin/env python3
"""
PSR Head Activation Diagnostic — Agent 1 / Q1 Opus Answer.

Measures per-component pre-GELU activations and transition-head outputs
to determine whether the PSR head is dead at initialization/current weights.

Architecture (PSRHead from model.py lines 1433-1638):
  1. Multi-scale GAP(P3+P4+P5) -> 768-D
  2. per_frame_mlp: Linear(768,512) -> LN -> GELU -> Drop(0.1) -> Linear(512,256) -> LN
  3. Causal Transformer: 3L, 4H, d_model=256, FFN=1024, pre-norm, GELU
  4. 11 output_heads: Linear(256,64) -> GELU -> Drop(0.06) -> Linear(64,1)

Dead-head criterion: ≥50% of components have pre-GELU activation ≤ 0 across batch.

Usage:
    python src/evaluation/psr_head_activation_diagnostic.py

Output:
    src/runs/rf_stages/checkpoints/psr_head_activation_diagnostic.json
"""

from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CKPT_DIR = PROJECT_ROOT / "src" / "runs" / "rf_stages" / "checkpoints"
CKPT_PATH = CKPT_DIR / "best.pth"
OUTPUT_PATH = CKPT_DIR / "psr_head_activation_diagnostic.json"

NUM_COMPONENTS = 11
D_MODEL = 256

# ---------------------------------------------------------------------------
# PSR Head Architecture (reconstructed from agent4-model.md + agent10-psr.md)
# ---------------------------------------------------------------------------


class PSRHead(nn.Module):
    """
    Full PSR head as described in model.py lines 1433-1638.

    Includes per-frame MLP, causal transformer, and 11 per-component output
    heads.  Bias on first linear of output_heads: +0.1 (fresh init) or 0.0
    (--reinit-heads path).
    """

    def __init__(
        self,
        d_model: int = D_MODEL,
        num_heads: int = 4,
        num_layers: int = 3,
        num_components: int = NUM_COMPONENTS,
        dropout: float = 0.2,
        ff_mult: int = 4,
        reinit_init: bool = False,
    ):
        super().__init__()

        # 1. Per-frame MLP: 768 -> 512 -> 256
        self.per_frame_mlp = nn.Sequential(
            nn.Linear(768, 512),
            nn.LayerNorm(512),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(512, d_model),
            nn.LayerNorm(d_model),
        )

        # 2. Causal transformer — 3 layers, 4 heads, d_model=256, FFN=1024
        self.transformer = nn.ModuleList(
            [
                CausalTransformerLayer(
                    d_model=d_model,
                    num_heads=num_heads,
                    ff_dim=d_model * ff_mult,
                    dropout=dropout,
                )
                for _ in range(num_layers)
            ]
        )

        # 3. LayerNorm before output heads (pre-norm design)
        self.output_norm = nn.LayerNorm(d_model)

        # 4. 11 per-component output heads
        #    Linear(256,64) -> GELU -> Dropout(0.06) -> Linear(64,1)
        self.output_heads = nn.ModuleList()
        for _ in range(num_components):
            head = nn.Sequential(
                nn.Linear(d_model, 64),
                nn.GELU(),
                nn.Dropout(0.06),
                nn.Linear(64, 1),
            )
            if reinit_init:
                # --reinit-heads path: zero bias (train.py line 2384)
                nn.init.constant_(head[0].bias, 0.0)
            else:
                # Normal init: +0.1 bias (model.py lines 1500-1505)
                nn.init.constant_(head[0].bias, 0.1)
            self.output_heads.append(head)

        # Confidence logit (shared, index 11)
        self.confidence_head = nn.Linear(d_model, 1)

        self._init_weights(reinit_init)

    def _init_weights(self, reinit_init: bool = False):
        """Apply weight initialization matching model.py defaults."""
        for name, m in self.named_modules():
            if isinstance(m, nn.Linear) and "output_heads" not in name and "confidence_head" not in name:
                # PyTorch default (Kaiming uniform) for most layers
                pass  # keeping defaults
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

        if reinit_init:
            # --reinit-heads path: xavier for transformer, std=0.02 for per_frame_mlp
            for m in self.transformer.modules():
                if isinstance(m, nn.Linear):
                    nn.init.xavier_uniform_(m.weight)
                    if m.bias is not None:
                        nn.init.zeros_(m.bias)
            for layer in self.per_frame_mlp:
                if isinstance(layer, nn.Linear):
                    nn.init.trunc_normal_(layer.weight, std=0.02)
                    if layer.bias is not None:
                        nn.init.zeros_(layer.bias)

    def forward(
        self, p3: torch.Tensor, p4: torch.Tensor, p5: torch.Tensor
    ) -> dict[str, torch.Tensor]:
        """
        Args:
            p3: [B, 256, H/8, W/8] — FPN P3
            p4: [B, 256, H/16, W/16] — FPN P4
            p5: [B, 256, H/32, W/32] — FPN P5

        Returns:
            dict with:
              - "logits": [B, 12] — 11 component logits + 1 confidence
              - "pre_gelu": [B, 11, 64] — pre-GELU activations per component
              - "pre_sigmoid": [B, 11] — final logits (pre-sigmoid)
              - "transformer_out": [B, 256] — transformer output
        """
        B = p3.shape[0]

        # 1. Multi-scale GAP -> concat -> 768-D
        p3_pooled = p3.mean(dim=(2, 3))  # [B, 256]
        p4_pooled = p4.mean(dim=(2, 3))  # [B, 256]
        p5_pooled = p5.mean(dim=(2, 3))  # [B, 256]
        fused = torch.cat([p3_pooled, p4_pooled, p5_pooled], dim=-1)  # [B, 768]

        # 2. Per-frame MLP
        x = self.per_frame_mlp(fused)  # [B, 256]

        # 3. Causal transformer (T=1 for per-frame, T>1 for sequence)
        #    In per-frame mode (T=1), transformer is essentially a no-op
        x = x.unsqueeze(1)  # [B, 1, 256]
        for layer in self.transformer:
            x = layer(x)
        x = x.squeeze(1)  # [B, 256]

        # 4. Output norm
        x = self.output_norm(x)  # [B, 256]

        # 5. Per-component output heads with hook-compatible collection
        pre_gelu_list = []
        pre_sigmoid_list = []
        for head in self.output_heads:
            # Linear(256, 64) — capture pre-GELU
            h = head[0](x)  # [B, 64] — pre-GELU activation
            pre_gelu_list.append(h.detach())
            # GELU -> Dropout -> Linear(64,1)
            h = head[1](h)  # GELU
            h = head[2](h)  # Dropout
            logit = head[3](h)  # [B, 1] — pre-sigmoid
            pre_sigmoid_list.append(logit.detach())

        pre_gelu = torch.stack(pre_gelu_list, dim=1)  # [B, 11, 64]
        pre_sigmoid = torch.cat(pre_sigmoid_list, dim=-1)  # [B, 11]

        # Confidence
        conf = self.confidence_head(x).sigmoid()  # [B, 1]

        logits = torch.cat([pre_sigmoid, conf], dim=-1)  # [B, 12]

        return {
            "logits": logits,
            "pre_gelu": pre_gelu,
            "pre_sigmoid": pre_sigmoid,
            "transformer_out": x,
        }


class CausalTransformerLayer(nn.Module):
    """
    Single causal transformer layer with pre-norm, GELU activation.

    Architecture (model.py lines 1480-1510):
      - LayerNorm -> MultiheadAttention(causal) -> residual
      - LayerNorm -> FFN(Linear->GELU->Linear) -> residual
    """

    def __init__(
        self,
        d_model: int = 256,
        num_heads: int = 4,
        ff_dim: int = 1024,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.ffn = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Pre-norm attention with causal mask
        x_norm = self.norm1(x)
        B, T, _ = x_norm.shape
        # Build causal mask for MultiheadAttention
        if T > 1:
            attn_mask = torch.triu(
                torch.full((T, T), float("-inf"), device=x.device),
                diagonal=1,
            )
        else:
            attn_mask = None
        attn_out, _ = self.attn(x_norm, x_norm, x_norm, attn_mask=attn_mask)
        x = x + attn_out

        # Pre-norm FFN
        x = x + self.ffn(self.norm2(x))
        return x


# ---------------------------------------------------------------------------
# FPN stub — generates synthetic FPN features for diagnostic
# ---------------------------------------------------------------------------


def make_fpn_features(
    batch_size: int = 4,
    img_h: int = 640,
    img_w: int = 640,
    device: torch.device = torch.device("cpu"),
    seed: int = 42,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Create synthetic FPN P3/P4/P5 feature maps with realistic channel
    dimensions and spatial scales.

    P3:  [B, 256, H/8,  W/8]   =  [B, 256, 80, 80]
    P4:  [B, 256, H/16, W/16]  =  [B, 256, 40, 40]
    P5:  [B, 256, H/32, W/32]  =  [B, 256, 20, 20]
    """
    rng = torch.Generator(device=device).manual_seed(seed)

    p3 = torch.randn(batch_size, 256, img_h // 8, img_w // 8, device=device, generator=rng)
    p4 = torch.randn(batch_size, 256, img_h // 16, img_w // 16, device=device, generator=rng)
    p5 = torch.randn(batch_size, 256, img_h // 32, img_w // 32, device=device, generator=rng)

    return p3, p4, p5


# ---------------------------------------------------------------------------
# Diagnostic
# ---------------------------------------------------------------------------


def run_diagnostic(
    model: nn.Module,
    device: torch.device,
    label: str = "fresh_init",
) -> dict:
    """Run forward pass and collect pre-GELU/pre-sigmoid statistics."""
    p3, p4, p5 = make_fpn_features(batch_size=4, device=device)

    model.eval()
    with torch.no_grad():
        output = model(p3, p4, p5)

    pre_gelu = output["pre_gelu"]  # [B, 11, 64]
    pre_sigmoid = output["pre_sigmoid"]  # [B, 11]
    logits = output["logits"]  # [B, 12]
    transformer_out = output["transformer_out"]  # [B, 256]

    B = pre_gelu.shape[0]

    # Per-component statistics (aggregated across batch and the 64-D vector)
    results = {}
    neg_mask = torch.zeros(NUM_COMPONENTS, dtype=torch.bool, device=device)

    for c in range(NUM_COMPONENTS):
        comp_act = pre_gelu[:, c, :]  # [B, 64] — pre-GELU

        comp_mean = comp_act.mean().item()
        comp_min = comp_act.min().item()
        comp_max = comp_act.max().item()
        comp_std = comp_act.std().item()

        # Fraction of entries ≤ 0
        frac_non_positive = (comp_act <= 0).float().mean().item()

        # Pre-sigmoid (logit) value
        logit_val = pre_sigmoid[:, c].mean().item()
        sigmoid_val = torch.sigmoid(pre_sigmoid[:, c]).mean().item()

        # Component is "dead" if mean pre-GELU ≤ 0
        is_dead = frac_non_positive > 0.5
        neg_mask[c] = is_dead

        results[f"component_{c}"] = {
            "pre_gelu_mean": round(float(comp_mean), 6),
            "pre_gelu_min": round(float(comp_min), 6),
            "pre_gelu_max": round(float(comp_max), 6),
            "pre_gelu_std": round(float(comp_std), 6),
            "frac_non_positive": round(float(frac_non_positive), 6),
            "pre_sigmoid_logit_mean": round(float(logit_val), 6),
            "sigmoid_output_mean": round(float(sigmoid_val), 6),
            "dead": bool(is_dead),
        }

    num_dead = neg_mask.sum().item()
    dead_components = [c for c in range(NUM_COMPONENTS) if neg_mask[c]]

    # Transformer output statistics
    transformer_stats = {
        "mean": round(float(transformer_out.mean().item()), 6),
        "std": round(float(transformer_out.std().item()), 6),
        "min": round(float(transformer_out.min().item()), 6),
        "max": round(float(transformer_out.max().item()), 6),
        "frac_non_positive": round(
            float((transformer_out <= 0).float().mean().item()), 6
        ),
    }

    # Overall verdict
    verdict = "DEAD" if num_dead >= NUM_COMPONENTS / 2 else "ALIVE"

    summary = {
        "label": label,
        "num_components": NUM_COMPONENTS,
        "num_dead_components": num_dead,
        "dead_component_indices": dead_components,
        "frac_components_dead": round(num_dead / NUM_COMPONENTS, 4),
        "verdict": verdict,
        "transformer_output": transformer_stats,
        "per_component": results,
    }

    return summary


def print_diagnostic(summary: dict) -> None:
    """Print diagnostic results in a readable format."""
    sep = "=" * 72
    print(f"\n{sep}")
    print(f"  PSR HEAD ACTIVATION DIAGNOSTIC — {summary['label']}")
    print(f"{sep}")
    print(f"  Verdict: {summary['verdict']}")
    print(f"  Dead components: {summary['num_dead_components']}/{summary['num_components']} "
          f"({summary['frac_components_dead']*100:.1f}%)")
    if summary["dead_component_indices"]:
        print(f"  Dead indices: {summary['dead_component_indices']}")
    print(f"{sep}")

    print(f"\n  Transformer output stats:")
    ts = summary["transformer_output"]
    print(f"    mean={ts['mean']:.4f}  std={ts['std']:.4f}  "
          f"min={ts['min']:.4f}  max={ts['max']:.4f}")
    print(f"    fraction <= 0: {ts['frac_non_positive']:.4f}")

    print(f"\n  Per-component pre-GELU activations:")
    print(f"  {'Comp':>5s}  {'Mean':>10s}  {'Min':>10s}  {'Max':>10s}  "
          f"{'Std':>10s}  {'Frac<=0':>8s}  {'Logit':>10s}  {'Sig':>8s}  {'Status':>6s}")
    print(f"  {'-'*5}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  "
          f"{'-'*8}  {'-'*10}  {'-'*8}  {'-'*6}")
    for c in range(NUM_COMPONENTS):
        comp = summary["per_component"][f"component_{c}"]
        status = "DEAD" if comp["dead"] else "ALIVE"
        print(
            f"  {c:5d}  {comp['pre_gelu_mean']:10.4f}  {comp['pre_gelu_min']:10.4f}  "
            f"{comp['pre_gelu_max']:10.4f}  {comp['pre_gelu_std']:10.4f}  "
            f"{comp['frac_non_positive']:8.4f}  {comp['pre_sigmoid_logit_mean']:10.4f}  "
            f"{comp['sigmoid_output_mean']:8.4f}  {status:>6s}"
        )

    print(f"\n  Dead-head criterion: ≥50% of components with pre-GELU ≤ 0 across batch")
    print(f"  Criterion {'MET' if summary['verdict'] == 'DEAD' else 'NOT MET'}")
    print(f"{sep}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nUsing device: {device}")
    print(f"Project root: {PROJECT_ROOT}")

    # Try loading checkpoint; fall back to freshly initialized model
    summaries = []

    if CKPT_PATH.exists():
        print(f"\nLoading checkpoint: {CKPT_PATH}")
        try:
            ckpt = torch.load(CKPT_PATH, map_location=device, weights_only=True)

            # Determine init mode from checkpoint key presence
            reinit_mode = "reinit" if "reinit" in str(CKPT_PATH) or any(
                "psr_head.per_frame_mlp.0.weight" in k for k in ckpt.keys()
            ) else False

            model = PSRHead(reinit_init=reinit_mode).to(device)

            # Load PSR head weights from checkpoint
            psr_state = {}
            for k, v in ckpt.items():
                if k.startswith("psr_head."):
                    psr_key = k[len("psr_head."):]
                    psr_state[psr_key] = v

            if psr_state:
                # Filter to only PSRHead keys
                model_keys = model.state_dict()
                compatible = {k: v for k, v in psr_state.items() if k in model_keys}
                if compatible:
                    missing, unexpected = model.load_state_dict(compatible, strict=False)
                    print(f"  Loaded {len(compatible)}/{len(model_keys)} PSR params")
                    if missing:
                        print(f"  Missing keys: {missing[:5]}...")
                    if unexpected:
                        print(f"  Unexpected keys: {unexpected[:3]}...")
                else:
                    print(f"  WARNING: No compatible PSR keys found in checkpoint")
            else:
                print(f"  WARNING: No 'psr_head.' prefix keys in checkpoint, "
                      f"trying raw keys")
                # Maybe the state dict IS the PSR head directly
                try:
                    model.load_state_dict(psr_state, strict=False)
                except Exception:
                    print(f"  Could not load checkpoint state, using random init")

            label = f"checkpoint ({'reinit' if reinit_mode else 'fresh'} init)"
            summary = run_diagnostic(model, device, label=label)
            summaries.append(summary)
            print_diagnostic(summary)
        except Exception as e:
            print(f"  Error loading checkpoint: {e}")
            print(f"  Falling back to fresh initialization")
            CKPT_PATH.unlink(missing_ok=True)  # mark as failed for next run

    if not summaries:
        # Run diagnostics on ALL initialization modes
        for reinit_mode, label in [(False, "fresh_init_p0.1"), (True, "reinit_init_p0.0")]:
            print(f"\n{'='*72}")
            print(f"  Creating model with {label} initialization")
            print(f"{'='*72}")
            model = PSRHead(reinit_init=reinit_mode).to(device)
            summary = run_diagnostic(model, device, label=label)
            summaries.append(summary)
            print_diagnostic(summary)

    # Save combined results
    output = {
        "diagnostics": summaries,
        "command": "python src/evaluation/psr_head_activation_diagnostic.py",
        "architecture": {
            "per_frame_mlp": "Linear(768,512)->LN->GELU->Drop(0.1)->Linear(512,256)->LN",
            "transformer": "3Lx4H d_model=256 FFN=1024 pre-norm GELU causal",
            "output_heads": "11x Sequential(Linear(256,64)->GELU->Drop(0.06)->Linear(64,1))",
            "bias_init": "+0.1 (fresh) / 0.0 (reinit)",
        },
    }

    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDiagnostic JSON saved to: {OUTPUT_PATH}")

    # Final verdict across all modes
    for s in summaries:
        print(f"\n  [{s['label']}] PSR head: {s['verdict']} "
              f"({s['num_dead_components']}/{s['num_components']} components dead)")


if __name__ == "__main__":
    main()
