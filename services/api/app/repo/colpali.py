"""ColPali visual-embedding wrapper.

ColPali produces *multi-vector* (late-interaction) embeddings: each page image
and each text query becomes a set of per-patch / per-token vectors, scored with
MaxSim (see repo/faiss_index.py). This module is the only place the model is
loaded and called; torch / colpali-engine / transformers are imported lazily
inside the functions so importing the app (structural + contract tests) never
pulls in the multi-GB stack, and the weights are downloaded only on first real
use — never during the build.

Device: runtime autodetect. CUDA is used when present; otherwise CPU. Apple
MPS is intentionally skipped in autodetect because PaliGemma/ColPali float ops
are unstable on MPS (NaNs / unsupported kernels). Set COLPALI_DEVICE=mps to
force it, or COLPALI_DEVICE=cuda|cpu to pin. Never hard-requires a GPU — CPU is
the default when nothing else is available.
"""

import functools
import io

import numpy as np
from PIL import Image

from app.config import settings


def select_device() -> str:
    """Autodetect the compute device. Order: explicit override -> CUDA -> CPU."""
    override = settings.colpali_device.strip().lower()
    if override:
        return override
    import torch

    if torch.cuda.is_available():
        return "cuda"
    # MPS deliberately omitted here (flaky for this model family); override to
    # opt in. Falls through to CPU as the safe default.
    return "cpu"


def _model_classes(model_name: str):
    """Pick the right colpali-engine model/processor classes for the model id."""
    from colpali_engine.models import (
        ColPali,
        ColPaliProcessor,
        ColQwen2,
        ColQwen2Processor,
    )

    if "colqwen2" in model_name.lower():
        return ColQwen2, ColQwen2Processor
    return ColPali, ColPaliProcessor


@functools.lru_cache(maxsize=2)
def _load(model_name: str):
    """Load (and cache) the model + processor. First call downloads weights."""
    import torch

    device = select_device()
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    model_cls, processor_cls = _model_classes(model_name)

    token = settings.hf_token or None
    model = model_cls.from_pretrained(
        model_name,
        torch_dtype=dtype,
        device_map=device,
        token=token,
    ).eval()
    processor = processor_cls.from_pretrained(model_name, token=token)
    return model, processor, device


def _to_numpy(tensor) -> np.ndarray:
    """Detach a per-item embedding tensor to L2-normalized float32 numpy."""
    arr = tensor.to("cpu").float().numpy().astype("float32")
    norms = np.linalg.norm(arr, axis=-1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def embed_images(images: list[bytes], model_name: str | None = None) -> list[np.ndarray]:
    """Embed rendered page PNGs. Returns one [num_patches, dim] array per page."""
    import torch

    model, processor, _ = _load(model_name or settings.colpali_model)
    pil_images = [Image.open(io.BytesIO(b)).convert("RGB") for b in images]

    out: list[np.ndarray] = []
    # Small batches keep peak memory bounded on CPU for multi-page decks.
    for start in range(0, len(pil_images), 2):
        chunk = pil_images[start : start + 2]
        batch = processor.process_images(chunk).to(model.device)
        with torch.no_grad():
            embeddings = model(**batch)
        for i in range(embeddings.shape[0]):
            out.append(_to_numpy(embeddings[i]))
    return out


def embed_query(text: str, model_name: str | None = None) -> np.ndarray:
    """Embed a natural-language query. Returns a [num_tokens, dim] array."""
    import torch

    model, processor, _ = _load(model_name or settings.colpali_model)
    batch = processor.process_queries([text]).to(model.device)
    with torch.no_grad():
        embeddings = model(**batch)
    return _to_numpy(embeddings[0])
