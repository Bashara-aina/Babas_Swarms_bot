---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/016-tfilm-birnbaum-2019.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.319558"
}
---

---
paper_id: 016
title: "Temporal FiLM: Capturing Long-Range Sequence Dependencies with Feature-Wise Modulations"
authors: "Birnbaum, Kuleshov, Enam, Koh, Ermon"
venue: "NeurIPS 2019"
url: "https://arxiv.org/abs/1909.06628"
arxiv: "1909.06628"
code: "https://github.com/tobran/DFiLM"
tags:
  - temporal-fiilm
  - sequence-modeling
  - long-range-dependencies
  - audio-processing
---

## Why This Paper Matters

TFiLM (Temporal FiLM) was a breakthrough in **applying FiLM to sequential data** by using a recurrent network to generate FiLM parameters. Unlike standard FiLM where parameters come from a static conditioning input, TFiLM's parameters evolve over time based on accumulated context—enabling the model to capture **long-range dependencies** without the computational cost of full recurrence.

The key insight: **a lightweight RNN can generate time-varying FiLM parameters that modulate a convolutional backbone**, effectively giving the convnet a "global workspace" of temporal context. This is computationally efficient (parallel convolutions) while being temporally flexible (RNN provides context).

---

## Core Contribution

**Temporal Feature-wise Linear Modulation (TFiLM):**
1. Uses an RNN to accumulate temporal context over the input sequence
2. The RNN's hidden state generates FiLM parameters at each time step
3. These parameters modulate the activations of a parallel convolutional network
4. Result: Convnet with effective global receptive field via temporal conditioning

**Architecture:**
```
Input Sequence X_1, X_2, ..., X_T
         |
         v
+----------------+
|  RNN (FiLM     |  h_t = RNN(h_{t-1}, x_t)
|   Generator)   |  γ_t, β_t = W_γβ * h_t
+----------------+
         |
         v
+---------------------+
|  ConvNet Backbone   |  f_t = Conv(X_t)
|  (FiLM-ed network)  |  y_t = γ_t ⊙ f_t + β_t
+---------------------+
         |
         v
    Output y_t
```

---

## Key Technical Details

**Standard Convolution:**
- Only captures local receptive field
- Long-range dependencies require many layers or large kernels
- Slow to train due to sequential nature if many layers needed

**TFiLM Solution:**
1. Convolutional backbone processes each frame independently (parallel)
2. RNN processes sequence to accumulate context
3. At each time step, RNN hidden state generates FiLM parameters
4. FiLM modulation effectively gives convnet "access" to all previous frames

**FiLM Parameters from RNN Hidden State:**
$$\gamma_t, \beta_t = W_{\gamma\beta} h_t$$

Where $h_t$ is the RNN hidden state after processing $x_1, ..., x_t$.

**Modulation Application:**
$$y_t = \gamma_t \odot f(x_t) + \beta_t$$

Where $f(x_t)$ is the convolutional feature extraction at time $t$.

---

## Critical Results

| Task | Dataset | TFiLM vs Baselines |
|------|---------|-------------------|
| Text classification | DBpedia, Yahoo | +3-5% accuracy over conv baselines |
| Audio generation | Speech commands | Better long-range structure |
| Audio super-resolution | VCTK | Improved perceptual quality |

**Key findings:**
- TFiLM significantly improves learning speed over pure conv or pure RNN approaches
- Captures long-range dependencies without slow RNN processing of full sequence
- Works especially well when global context is important (text classification, audio prosody)

---

## What POPW Can Steal Directly

1. **RNN-generated FiLM parameters:**
   - The pattern of using hidden state to generate γ,β is directly applicable
   - POPW could use agent-level RNN to generate population-level FiLM parameters

2. **Temporal context accumulation:**
   - TFiLM shows how to give a "memory" to architectures that are otherwise stateless
   - POPW could use similar technique to give stateless agents temporal memory

3. **Efficient long-range modeling:**
   - Avoids full recurrence by modulating conv features
   - POPW could use similar efficiency for long-horizon agent interactions

4. **Implementation pattern:**
```python
# TFiLM in POPW context
rnn_hidden = agent_rnn(population_history)
gamma, beta = modulation_head(rnn_hidden)
# Apply to agent's current observation
modulated_obs = gamma * current_obs + beta
```

---

## Failure Modes

1. **RNN bottleneck:** The RNN must compress all temporal context into its hidden state. If hidden dimension is too small, information is lost.

2. **Modulation delay:** FiLM parameters are generated from hidden state, which itself has delay from RNN processing. Not suitable for tasks requiring immediate response.

3. **Training instability:** Combined training of RNN and convnet can be unstable. Gradient interactions between the two networks.

4. **Fixed modulation frequency:** TFiLM applies modulation at each time step identically. Cannot selectively modulate at decision points.

5. **Memory complexity:** RNN hidden state adds memory overhead proportional to sequence length.

---

## Key Equations

**RNN Hidden State Update:**
$$h_t = \text{RNN}(h_{t-1}, x_t)$$

**FiLM Parameter Generation:**
$$\gamma_t, \beta_t = W_{\gamma\beta} h_t$$

**TFiLM Modulation:**
$$\tilde{f}_t = \gamma_t \odot f_t + \beta_t$$

Where $f_t$ is the convolutional feature at time $t$.

**Alternative formulation (from paper):**
$$h_t = \sigma(W_h [h_{t-1}, x_t] + b_h)$$
$$g_t = \sigma(W_g h_t + b_g)$$
$$f'_t = g_t \odot f_t$$

(Where gating is a special case of full affine modulation)

---

## Researcher Intelligence

**Author Lab:** Stanford University (Ermon group)

**Motivation:** Standard feed-forward convnets have finite receptive fields. RNNs can capture long-range but are slow. The authors wanted a way to give convnets "global vision" through conditioning.

**What led here:**
1. FiLM had shown success in visual reasoning
2. Recurrent networks are standard for sequences but slow
3. Insight: combine parallel convolutions with recurrent context
4. The RNN generates conditioning that modulates conv features

**Key insight:** Modulation provides an efficient "communication channel" from RNN to convnet. Instead of the convnet having to learn to store context in its weights, the RNN directly conditions the feature maps.

---

## Key Citations

```bibtex
@inproceedings{birnbaum2019temporal,
  title={Temporal {F}i{L}M: Capturing Long-Range Sequence Dependencies with Feature-Wise Modulations},
  author={Birnbaum, Sawyer and Kuleshov, Volodymyr and Enam, Zayd and Koh, Pang Wei and Ermon, Stefano},
  booktitle={NeurIPS},
  year={2019}
}
```

---

## Engineer's Implementation Notes

**PyTorch implementation of TFiLM:**
```python
class TFiLM(nn.Module):
    """Temporal FiLM for POPW agent temporal modeling."""
    
    def __init__(self, input_dim, rnn_dim, feature_dim):
        super().__init__()
        # RNN to accumulate temporal context
        self.rnn = nn.GRUCell(input_dim, rnn_dim)
        
        # FiLM parameter generator
        self.film_generator = nn.Sequential(
            nn.Linear(rnn_dim, feature_dim * 2)
        )
    
    def forward(self, conv_features, rnn_hidden, current_input):
        """
        Args:
            conv_features: (B, feature_dim) - convnet output for current frame
            rnn_hidden: (B, rnn_dim) - previous RNN hidden state
            current_input: (B, input_dim) - current observation
        Returns:
            modulated_features, new_rnn_hidden
        """
        # Update RNN with new input
        new_rnn_hidden = self.rnn(current_input, rnn_hidden)
        
        # Generate FiLM parameters from RNN state
        gamma_beta = self.film_generator(new_rnn_hidden)
        gamma, beta = gamma_beta.chunk(2, dim=-1)
        
        # Apply modulation to conv features
        modulated = gamma * conv_features + beta
        
        return modulated, new_rnn_hidden
```

**Integration with POPW:**
```python
class POPWAgentWithTFiLM(nn.Module):
    """POPW agent using TFiLM for temporal modeling."""
    
    def __init__(self, obs_dim, action_dim, rnn_dim=64, feature_dim=128):
        super().__init__()
        # Observation encoder
        self.obs_encoder = nn.Linear(obs_dim, feature_dim)
        
        # TFiLM for temporal modulation
        self.tfilm = TFiLM(feature_dim, rnn_dim, feature_dim)
        
        # Policy head
        self.actor = nn.Linear(feature_dim, action_dim)
        
        # Hidden state
        self.rnn_hidden = None
    
    def forward(self, obs):
        if self.rnn_hidden is None:
            self.rnn_hidden = torch.zeros(obs.size(0), self.tfilm.rnn.hidden_size)
        
        # Encode observation
        feat = self.obs_encoder(obs)
        
        # Apply TFiLM (with recurrent hidden as modulator)
        feat_modulated, self.rnn_hidden = self.tfilm(
            feat, 
            self.rnn_hidden, 
            obs  # Use raw obs for RNN input
        )
        
        # Policy
        return self.actor(feat_modulated)
```

---

## Connections to Other Wiki Papers

**From foundational FiLM (013):**
- TFiLM is FiLM applied temporally
- Same core equation: $\gamma(z) \odot x + \beta(z)$
- Different: $z$ evolves over time via RNN

**Related to:**
- **014 (GNN-FiLM):** Spatial (graph) vs temporal conditioning
- **015 (Motion Modulation):** Motion-guided temporal modulation
- **017 (Conditional Batch Norm):** CBN is FiLM with batch statistics
- **018 (AdaIN):** AdaIN is FiLM where main network generates parameters

**For POPW:** TFiLM provides the template for giving POPW agents temporal memory. The RNN generates conditioning that modulates current representations based on history.

---

## POPW Action Item

**Specific file:** `agents/temporal.py` (create if missing)

**Specific change:** Implement TFiLM layer for POPW temporal modeling:

```python
class TemporalFiLMLayer(nn.Module):
    """TFiLM: RNN-generated FiLM parameters for temporal modulation.
    
    Use case: Give POPW agents memory of past population states.
    """
    
    def __init__(self, feature_dim: int, rnn_dim: int):
        super().__init__()
        self.feature_dim = feature_dim
        self.rnn_dim = rnn_dim
        
        # RNN for temporal context
        self.rnn = nn.GRUCell(feature_dim, rnn_dim)
        
        # Generate FiLM parameters from RNN state
        self.film_params = nn.Sequential(
            nn.Linear(rnn_dim, feature_dim * 2),
            nn.Tanh()  # Bound gamma to [-1, 1] initially
        )
        
        # Default: start with identity modulation
        nn.init.zeros_(self.film_params[0].bias)
        nn.init.zeros_(self.film_params[0].weight[:, :self.rnn_dim//2])
        nn.init.ones_(self.film_params[0].weight[:, self.rnn_dim//2:])
    
    def forward(self, x_t, h_tm1):
        """
        Args:
            x_t: Current features (B, feature_dim)
            h_tm1: Previous RNN hidden state (B, rnn_dim)
        Returns:
            modulated_features, new_hidden_state
        """
        # Update temporal context
        h_t = self.rnn(x_t, h_tm1)
        
        # Generate FiLM parameters
        gamma_beta = self.film_params(h_t)
        gamma, beta = gamma_beta.chunk(2, dim=-1)
        
        # Apply modulation
        x_modulated = gamma * x_t + beta
        
        return x_modulated, h_t
```
