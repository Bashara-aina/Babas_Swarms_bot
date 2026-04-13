---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/022-cones-2024.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.348052"
}
---

---
paper_id: 022
title: "CoNeS: Conditional Neural Fields with Shift Modulation for Multi-Sequence MRI Translation"
authors: "Chen, Staring, Neve, Romeijn, Hensen, Verbist, Wolterink, Tao"
venue: "MELBA 2024"
url: "https://arxiv.org/abs/2309.03320"
arxiv: "2309.03320"
code: "https://github.com/yunjiechen/CoNeS"
tags:
  - neural-fields
  - conditional-neural-fields
  - shift-modulation
  - multi-sequence-mri
---

## Why This Paper Matters

CoNeS introduced **Conditional Neural Fields (CoNF)** with **shift modulation** — a novel approach using MLPs as decoders (neural fields) instead of CNNs, conditioned on source images via shift modulation. This overcomes the **spectral bias** problem of CNNs (difficulty representing high-frequency details).

The key insight for POPW: **shift modulation** is a simpler alternative to FiLM's $\gamma \odot x + \beta$ — it uses only additive shift $\beta$ with a learned latent code, avoiding the multiplicative interaction. This can be more stable and still effective.

---

## Core Contribution

**Conditional Neural Fields with Shift Modulation (CoNeS):**
1. **Neural Field as decoder:** MLP maps 3D coordinates → image intensity
   $$I(x, y, z) = \text{MLP}([x, y, z])$$

2. **Source-conditioned via shift modulation:** 
   $$I_{target} = I_{source} + \text{MLP}_{shift}(z)$$
   where $z$ is a latent code encoding the transformation needed

3. **Conditioning on source image:**
   - Extract features from source image
   - Use as conditioning for the neural field
   - Shift modulation adapts the field to generate target modality

**Key innovation over standard FiLM:**
- Shift-only modulation ($\beta$) instead of scale+shift ($\gamma, \beta$)
- Simpler, more stable, avoids vanishing gradients from $\gamma \approx 0$

---

## Key Technical Details

**Standard Neural Field:**
$$F(v) = \text{MLP}_\theta(v)$$
where $v$ is a coordinate (e.g., 3D voxel position).

**CoNeS Architecture:**
```
Source MRI → Encoder → Latent code z
                           |
Coordinate v → MLP decoder → I_target(v) + shift(z)
```

**Shift Modulation:**
$$F_{target}(v) = F_{source}(v) + \gamma \odot \text{MLP}_{shift}(z)$$

Or simplified (no scale):
$$F_{target}(v) = F_{source}(v) + \text{MLP}_{shift}(z)$$

**Why shift instead of scale+shift:**
1. Scale modulation ($\gamma$) can cause vanishing if $\gamma \approx 0$
2. Shift-only is more stable for neural fields
3. Sufficient for translation tasks (adding details/differences)

**Spectral Analysis:** CoNeS shows better high-frequency reconstruction than CNN baselines — overcoming spectral bias.

---

## Critical Results

| Method | BraTS 2018 SSIM | High-freq PSNR |
|--------|-----------------|----------------|
| Pix2Pix (CNN) | 0.78 | Lower |
| CUT (CNN) | 0.81 | Lower |
| **CoNeS (NeRF)** | **0.85** | **Higher** |

**Key findings:**
- CoNeS outperforms CNN baselines on MRI translation
- Better at capturing fine details (high-frequency)
- Shift modulation sufficient for multi-sequence translation

---

## What POPW Can Steal Directly

1. **Shift-only modulation:**
   ```python
   # Instead of FiLM: gamma * x + beta
   # Shift-only: x + beta
   def shift_modulation(x, z):
       shift = mlp(z)
       return x + shift
   ```
   - More stable than full FiLM
   - Avoids vanishing gradients from small gamma

2. **Neural field paradigm:**
   - MLP over coordinates instead of convolutions
   - Infinite resolution potential
   - POPW could use coordinate-based representations

3. **Source + latent shift:**
   - Condition on source representation
   - Generate additive shift based on latent code
   - POPW: population aggregate as "source", agent as "target"

4. **Hypernetwork modulation:**
   - Shift modulation is lightweight hypernetwork
   - MLP(z) generates the shift parameters

---

## Failure Modes

1. **Training complexity:** Neural fields can be harder to train than CNNs (coordinate-based optimization).

2. **Inference speed:** MLP evaluation at each coordinate is slower than convolutions.

3. **Coordinate encoding:** Requires positional encodings for good high-frequency reconstruction.

4. **Limited to coordinate-based tasks:** Works well for image synthesis but not for arbitrary structured prediction.

5. **Shift capacity:** May not capture scale variations well.

---

## Key Equations

**Neural Field:**
$$F(v; \theta) = \text{MLP}_\theta(v)$$

**Shift Modulation:**
$$F_{target}(v) = F_{source}(v) + \Delta(v; \phi)$$
where $\Delta(v; \phi) = \text{MLP}_\phi(z)$ is the shift generated from latent code $z$.

**Full CoNeS formulation:**
$$I_{target}(v) = \sigma(W_{source} I_{source}) + \text{MLP}_{shift}(z; \phi)$$

---

## Researcher Intelligence

**Author Lab:** Leiden University Medical Center + University of Twente

**Motivation:** MRI often has missing sequences due to acquisition constraints. Standard CNNs for synthesizing missing MRI suffer from spectral bias (poor high-frequency detail).

**What led here:**
1. Neural radiance fields (NeRF) showed MLPs could represent images
2. Conditional neural fields (CoNF) extended to conditional generation
3. Shift modulation is simpler than full FiLM
4. Applied to multi-sequence MRI translation

**Key insight:** For translation tasks (source → target), additive shift may be sufficient. No need for scale modulation.

---

## Key Citations

```bibtex
@article{chen2024cones,
  title={CoNeS: Conditional Neural Fields with Shift Modulation for Multi-Sequence MRI Translation},
  author={Chen, Yunjie and Staring, Marius and Neve, Olaf M and Romeijn, Stephan R and Hensen, Erik F and Verbist, Berit M and Wolterink, Jelmer M and Tao, Qian},
  journal={Machine Learning for Biomedical Imaging (MELBA)},
  year={2024}
}
```

---

## Engineer's Implementation Notes

**PyTorch implementation of shift modulation:**
```python
class ShiftModulation(nn.Module):
    """Shift modulation from CoNeS.
    
    Instead of FiLM (gamma * x + beta), use shift only (x + beta).
    More stable, avoids vanishing gradients.
    """
    
    def __init__(self, feature_dim: int, latent_dim: int):
        super().__init__()
        # Shift generator
        self.shift_mlp = nn.Sequential(
            nn.Linear(latent_dim, feature_dim),
            nn.ReLU(),
            nn.Linear(feature_dim, feature_dim)
        )
    
    def forward(self, x: Tensor, latent: Tensor) -> Tensor:
        """
        Args:
            x: Source features (B, D)
            latent: Latent conditioning (B, latent_dim)
        Returns:
            Shifted features (B, D)
        """
        shift = self.shift_mlp(latent)
        return x + shift


class ConditionalNeuralField(nn.Module):
    """Neural field with shift modulation for POPW.
    
    Maps coordinates to features, conditioned on latent.
    Could represent spatial population structure.
    """
    
    def __init__(self, coord_dim: int, feature_dim: int, latent_dim: int, hidden_dim: int = 128):
        super().__init__()
        
        # Coordinate encoder
        self.coord_encoder = nn.Sequential(
            nn.Linear(coord_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Shift modulator
        self.shift_mod = ShiftModulation(hidden_dim, latent_dim)
        
        # Output head
        self.output = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, feature_dim)
        )
    
    def forward(self, coords: Tensor, latent: Tensor) -> Tensor:
        """
        Args:
            coords: Coordinate tensor (B, N, coord_dim) or (B, coord_dim)
            latent: Latent conditioning (B, latent_dim)
        Returns:
            Field values at coordinates (B, N, feature_dim) or (B, feature_dim)
        """
        # Encode coordinates
        features = self.coord_encoder(coords)
        
        # Apply shift modulation
        features = self.shift_mod(features, latent)
        
        # Output
        return self.output(features)
```

**POPW application - Spatial population field:**
```python
class POPWSpatialField(nn.Module):
    """Model POPW population as a continuous field.
    
    Different positions in "agent space" have different properties.
    Use CoNeS-style shift modulation.
    """
    
    def __init__(self, agent_dim: int, property_dim: int, hidden_dim: int = 64):
        super().__init__()
        
        # Agent coordinate encoder (position → feature)
        self.agent_encoder = nn.Sequential(
            nn.Linear(agent_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Shift modulation from population latent
        self.population_shift = ShiftModulation(hidden_dim, property_dim)
        
        # Output: agent properties at position
        self.property_predictor = nn.Linear(hidden_dim, property_dim)
    
    def forward(self, agent_states: Tensor, population_properties: Tensor) -> Tensor:
        """
        Args:
            agent_states: (B, agent_dim) positions in agent space
            population_properties: (B, property_dim) population latent
        Returns:
            Predicted properties for each agent
        """
        # Encode agent position
        encoded = self.agent_encoder(agent_states)
        
        # Apply population shift
        shifted = self.population_shift(encoded, population_properties)
        
        # Predict properties
        return self.property_predictor(shifted)
```

---

## Connections to Other Wiki Papers

**Related to:**
- **013 (Feature-wise Transformations):** Shift modulation is simplified FiLM (no scale)
- **014 (GNN-FiLM):** Graph neural fields with modulation
- **017 (Conditional Batch Norm):** CBN is batch-level shift+scale

**For POPW:** Shift modulation provides a simpler, more stable alternative to full FiLM. Useful when scale modulation isn't needed.

---

## POPW Action Item

**Specific file:** `agents/modulation.py`

**Specific change:** Add shift modulation as simpler alternative to FiLM:

```python
class ShiftModulation(nn.Module):
    """Shift modulation from CoNeS (simpler than FiLM).
    
    CoNeS insight: For translation/conditioning tasks, shift-only may be sufficient.
    More stable than gamma * x + beta (avoids vanishing gradients from gamma ≈ 0).
    
    For POPW: Use when scale modulation isn't needed.
    """
    
    def __init__(self, feature_dim: int, conditioning_dim: int):
        super().__init__()
        self.feature_dim = feature_dim
        
        # Shift generator
        self.shift_generator = nn.Sequential(
            nn.Linear(conditioning_dim, feature_dim),
            nn.Tanh(),  # Bound shift
            nn.Linear(feature_dim, feature_dim)
        )
        
        # Zero-init for stable training
        nn.init.zeros_(self.shift_generator[-1].bias)
        nn.init.zeros_(self.shift_generator[-1].weight)
    
    def forward(self, x: Tensor, conditioning: Tensor) -> Tensor:
        """
        Args:
            x: Input features (B, D)
            conditioning: Conditioning signal (B, conditioning_dim)
        Returns:
            Shift-modulated features (B, D)
        """
        shift = self.shift_generator(conditioning)
        return x + shift
```

**Usage:** When POPW only needs additive conditioning (no feature scaling), use ShiftModulation instead of FiLM.
