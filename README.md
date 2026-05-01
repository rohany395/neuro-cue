# Resonate 🧠

An educational research prototype that predicts how speech therapy stimuli engage clinically relevant language regions of the brain — built on Meta's TRIBE v2 brain encoding model.

> **Note:** This is a research/educational tool, not a medical device. It is not intended for clinical decision-making.

## The Problem

Speech-language pathologists (SLPs) select therapy stimuli (videos, audio, prompts) based on experience and trial-and-error. There's no objective way to predict which stimulus will most effectively engage a patient's damaged language regions before using it in a session.

## The Solution

Resonate wraps Meta's [TRIBE v2](https://huggingface.co/facebook/tribev2) — a foundation model that predicts fMRI brain responses to video, audio, and text — with a clinical layer that:

- Maps predicted activations to four language-relevant regions of interest (Broca's, Wernicke's, SMA, Angular Gyrus)
- Surfaces per-ROI engagement scores with clinical interpretation
- Visualizes engagement over time
- Generates plain-language recommendations

The result: SLP educators and researchers can screen stimuli in seconds, with data backing what experience already suggests.

## Tech Stack

**Backend:** FastAPI · Python 3.12 · TRIBE v2 · Nilearn · NumPy
**Frontend:** React · Vite · TailwindCSS · Axios · react-three-fiber
**Deployment:** Hugging Face Spaces (backend with GPU) · Vercel (frontend)

## Project Structure
neuro-cue/
├── backend/          FastAPI app, TRIBE v2 wrapper, ROI logic
├── frontend/         React UI
├── notebooks/        Colab experiments
└── docs/             Architecture & design notes

## License

CC BY-NC 4.0 — inherited from TRIBE v2. Educational and academic use permitted; no commercial use.

## Acknowledgments

Built on [TRIBE v2](https://huggingface.co/facebook/tribev2) by Meta FAIR.
ROI mapping uses the [Destrieux 2009 atlas](https://nilearn.github.io/) via nilearn.