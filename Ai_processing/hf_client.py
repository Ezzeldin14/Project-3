"""
Client for calling Hugging Face Space Gradio APIs.

Sends images to HF Spaces for AI processing, avoiding the need to load
heavy models locally. This keeps Railway RAM usage minimal.
"""

import io
import logging
import os
import tempfile

import numpy as np
import requests
from PIL import Image
from gradio_client import Client, handle_file

logger = logging.getLogger(__name__)

# ── Hugging Face Space clients (lazy-loaded singletons) ──────────────────────
_clients: dict[str, Client] = {}

# Space URLs for each AI feature
HF_SPACES = {
    "DE_BLUR": "EhabByte/finalfrfr",
}


def _get_client(space_id: str) -> Client:
    """Return a cached Gradio client for the given HF Space."""
    if space_id not in _clients:
        logger.info("Connecting to HF Space: %s", space_id)

        token = os.getenv("HF_TOKEN")

        try:
            # Works with most gradio_client versions
            if token:
                _clients[space_id] = Client(space_id, token=token)
            else:
                _clients[space_id] = Client(space_id)

        except TypeError:
            # Fallback for very old versions
            logger.warning("Token not supported in this gradio_client version")
            _clients[space_id] = Client(space_id)

        logger.info("Connected to HF Space: %s", space_id)

    return _clients[space_id]


def run_hf_deblur(image: Image.Image) -> Image.Image:
    """
    Send an image to the HF Space for deblurring and return the result.
    """
    # Ensure RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Save image to temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image.save(tmp, format="PNG")
        tmp_path = tmp.name

    try:
        client = _get_client(HF_SPACES["DE_BLUR"])

        # Debug API endpoints
        logger.info("HF API INFO:")
        try:
            logger.info(client.view_api())
        except Exception:
            logger.warning("Could not fetch API info")

        logger.info("Sending image to HF Space...")

        # Use handle_file() to properly wrap the file path for the Gradio API.
        # Passing a raw path string causes a Pydantic validation error
        # ("Input should be a valid dictionary or instance of ImageData").
        file_input = handle_file(tmp_path)

        try:
            result = client.predict(
                file_input,
                api_name="/predict"
            )
        except Exception:
            # fallback
            logger.warning("Trying fallback predict call...")
            result = client.predict(file_input)

        logger.info("Received response from HF Space")

        # Some spaces return tuple/list
        if isinstance(result, (list, tuple)):
            result = result[0]

        processed_image = Image.open(result).convert("RGB")

        return processed_image

    except Exception as e:
        logger.exception("HF Deblur failed: %s", str(e))
        raise

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)