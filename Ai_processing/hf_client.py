"""
Client for calling Hugging Face Space Gradio APIs.

Sends images to HF Spaces for AI processing, avoiding the need to load
heavy models locally. This keeps Railway RAM usage minimal.
"""

import io
import logging
import requests

import numpy as np
from PIL import Image
from gradio_client import Client

logger = logging.getLogger(__name__)

# ── Hugging Face Space clients (lazy-loaded singletons) ──────────────────────
_clients: dict[str, Client] = {}

# Space URLs for each AI feature
HF_SPACES = {
    "DE_NOISE": "EhabByte/finalfrfr",
}


def _get_client(space_id: str) -> Client:
    """Return a cached Gradio client for the given HF Space."""
    if space_id not in _clients:
        logger.info("Connecting to HF Space: %s", space_id)
        _clients[space_id] = Client(space_id)
        logger.info("Connected to HF Space: %s", space_id)
    return _clients[space_id]


def run_hf_denoise(image: Image.Image) -> Image.Image:
    """
    Send an image to the HF Space for denoising and return the result.
    """
    # Ensure RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Save image to a temporary file-like buffer (Gradio client needs a file path)
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image.save(tmp, format="PNG")
        tmp_path = tmp.name

    try:
        client = _get_client(HF_SPACES["DE_NOISE"])

        # Call the Gradio predict function — it takes an image and returns an image
        result = client.predict(
            input_img=tmp_path,
            api_name="/predict",
        )

        # result is a file path to the processed image
        processed_image = Image.open(result).convert("RGB")
        return processed_image

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
