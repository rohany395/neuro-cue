# Resonate

> **Neural Stimulus Optimizer for Speech-Language Pathology**
> Brain-encoding model for predicting neural engagement to therapy stimuli.

[![Live Demo](https://img.shields.io/badge/HF_Spaces-Live_Demo-blue)](https://huggingface.co/spaces/rohany395/neuro-cue)
[![License](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey)](LICENSE)

🔗 **[Live Demo on Hugging Face Spaces →](https://huggingface.co/spaces/rohany395/neuro-cue)**

---

## What It Does

Resonate predicts which language regions of the brain (Broca's, Wernicke's, SMA, Angular Gyrus) are engaged when a speech-language pathology patient is exposed to a therapy stimulus — whether video, audio, or text. It wraps Meta's [TRIBE v2](https://huggingface.co/facebook/tribev2) brain-encoding model with a clinical ROI scoring layer designed for SLP educational research.

**This is a research prototype. Not a medical device.**

## Why This Matters

SLP curriculum and clinical training often relies on intuition or expensive fMRI studies to evaluate stimulus design. Resonate gives clinicians and educators an instant, free preview of which brain regions a stimulus is likely to engage — based on a state-of-the-art foundation model trained on 700+ subjects' fMRI data.

## How It Works

1. **Input:** Upload a video, audio, or text sample (a therapy stimulus)
2. **Inference:** TRIBE v2 predicts BOLD response across 20,484 cortical vertices
3. **Clinical layer:** Predictions are mapped to four language ROIs using the Destrieux atlas
4. **Visualization:** Interactive 3D brain heatmap + ROI score breakdown

## Architecture

The deployed app runs on Hugging Face Spaces with ZeroGPU (free, queue-based GPU access):
┌─────────────────────────────────────────────────┐
│  Hugging Face Spaces (ZeroGPU - Free Tier)      │
│                                                 │
│   Gradio UI                                     │
│      ↓                                          │
│   TRIBE v2 (LLaMA + V-JEPA2 + Wav2Vec-BERT)     │
│      ↓                                          │
│   Clinical ROI scoring                          │
│      ↓                                          │
│   3D brain visualization (Plotly)               │
└─────────────────────────────────────────────────┘

## Repository Structure
## Tech Stack

**Inference & ML:**
- [TRIBE v2](https://huggingface.co/facebook/tribev2) (Meta's brain encoder, 2026)
- LLaMA 3.2-3B, V-JEPA2, Wav2Vec-BERT (TRIBE's frozen encoders)
- PyTorch + ZeroGPU (Hugging Face's serverless GPU)

**Deployment:**
- Gradio 6.10 (UI + auto-generated API)
- nilearn (Destrieux atlas, fsaverage5 mesh)
- Plotly (3D brain visualization)

**Frontend (React variant, in progress):**
- React 18 + Vite + TailwindCSS
- @react-three/fiber + drei (3D visualization)
- Recharts (temporal engagement charts)

## What I Built vs. What I Used

**Used (off-the-shelf):**
- TRIBE v2 model weights and inference API
- Gradio framework
- nilearn brain visualization utilities

**Built:**
- Clinical ROI scoring layer (Destrieux atlas → 4 SLP-relevant regions)
- Interactive 3D brain visualization with timestep slider
- Custom UI design and information hierarchy
- Deployment pipeline targeting ZeroGPU
- React + Three.js alternative frontend (in `/frontend`)

## Citation

If you reference this project, please also cite the underlying TRIBE v2 paper:

```bibtex
@article{dAscoli2026TribeV2,
  title={A foundation model of vision, audition, and language for in-silico neuroscience},
  author={d'Ascoli, Stéphane and Rapin, Jérémy and Benchetrit, Yohann and others},
  year={2026}
}
```

## License

CC BY-NC 4.0 — inherited from TRIBE v2's license. Educational and research use only. Not for commercial use.

---

Built by [Rohan](https://github.com/rohany395) — M.S. Information Systems, Syracuse University (2026).