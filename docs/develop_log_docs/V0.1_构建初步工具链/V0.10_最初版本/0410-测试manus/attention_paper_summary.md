# Summary of "Attention Is All You Need"

## Abstract
The paper introduces the **Transformer**, a novel neural network architecture based solely on **attention mechanisms**, eliminating recurrence and convolutions. It achieves superior performance on machine translation tasks (e.g., 28.4 BLEU on English-to-German and 41.8 BLEU on English-to-French) while being highly parallelizable and efficient.

## Methodology
### Transformer Architecture
- **Encoder**: 6 identical layers with:
  - Multi-head self-attention.
  - Position-wise feed-forward networks.
  - Residual connections and layer normalization.
- **Decoder**: Similar to encoder but adds:
  - Encoder-decoder attention.
  - Masking for autoregressive properties.

### Attention Mechanisms
- **Scaled Dot-Product Attention**: Computes attention weights with scaling by `√dk`.
- **Multi-Head Attention**: Uses 8 parallel attention heads for diverse subspace focus.

### Positional Encoding
- Sinusoidal functions inject positional information into the model.

## Key Results
- **Machine Translation**:
  - 28.4 BLEU (English-to-German).
  - 41.8 BLEU (English-to-French), a new state-of-the-art.
- **Efficiency**: Trained in **12 hours on 8 GPUs**.
- **Generalization**: Applied successfully to English constituency parsing.

## Innovations
- Eliminates recurrence and convolutions.
- Enables global dependencies via attention.
- Highly parallelizable and scalable.