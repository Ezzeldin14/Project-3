"""
Image processing utilities.

Each function takes a PIL Image and returns a processed PIL Image.
- DE_BLUR: Calls HuggingFace Space API (NAFNet model hosted remotely).
- SUPER_RESOLUTION: Calls HuggingFace Space API (Real-ESRGAN model hosted remotely).
- COLORIZATION: Calls HuggingFace Space API (DeOldify-style model hosted remotely).
- BILATERAL_FILTER: OpenCV bilateral filter (edge-preserving smoothing).
- GAUSSIAN_FILTER: OpenCV Gaussian blur.
- GUIDED_FILTER: OpenCV guided filter (edge-aware smoothing).
- MEDIAN_FILTER: OpenCV median blur (salt-and-pepper noise removal).
"""

import cv2
import numpy as np
from PIL import Image

from .hf_client import run_hf_colorize, run_hf_deblur, run_hf_super_resolution


# ---------------------------------------------------------------------------
# Helper: PIL ↔ OpenCV conversion
# ---------------------------------------------------------------------------

def _pil_to_cv2(image: Image.Image) -> np.ndarray:
    """Convert PIL Image (RGB) to OpenCV array (BGR)."""
    if image.mode != "RGB":
        image = image.convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _cv2_to_pil(img_bgr: np.ndarray) -> Image.Image:
    """Convert OpenCV array (BGR) to PIL Image (RGB)."""
    return Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))


# ---------------------------------------------------------------------------
# AI-powered features (ONNX models)
# ---------------------------------------------------------------------------

def apply_super_resolution(image: Image.Image) -> Image.Image:
    """
    Upscale an image using Real-ESRGAN model hosted on HuggingFace Space.
    Sends the image to HF, model runs remotely, returns enhanced image.
    """
    return run_hf_super_resolution(image)


def apply_colorization(image: Image.Image) -> Image.Image:
    """
    Colorize a grayscale image using a DeOldify-style model hosted on HuggingFace Space.
    Sends the image to HF, model runs remotely, returns colorized image.
    """
    return run_hf_colorize(image)


def apply_deblur(image: Image.Image) -> Image.Image:
    """
    Deblur an image using NAFNet model hosted on HuggingFace Space.
    Sends the image to HF, model runs remotely, returns processed image.
    """
    return run_hf_deblur(image)


# ---------------------------------------------------------------------------
# Basic OpenCV filters
# ---------------------------------------------------------------------------

def apply_bilateral_filter(image: Image.Image) -> Image.Image:
    """
    Bilateral filter — smooths the image while preserving sharp edges.
    Good for reducing noise while keeping details.
    """
    img = _pil_to_cv2(image)
    # d=15: diameter of pixel neighborhood (larger = stronger)
    # sigmaColor=150: range filter (color similarity)
    # sigmaSpace=150: spatial filter (coordinate proximity)
    filtered = cv2.bilateralFilter(img, d=15, sigmaColor=150, sigmaSpace=150)
    return _cv2_to_pil(filtered)


def apply_gaussian_filter(image: Image.Image) -> Image.Image:
    """
    Gaussian blur — smooths the image uniformly.
    Good for reducing Gaussian noise.
    """
    img = _pil_to_cv2(image)
    # (15, 15): kernel size — larger = more blur
    # 0: sigma calculated automatically from kernel size
    filtered = cv2.GaussianBlur(img, (15, 15), 0)
    return _cv2_to_pil(filtered)


def apply_guided_filter(image: Image.Image) -> Image.Image:
    """
    Guided filter — edge-aware smoothing using the image itself as guide.
    Preserves edges better than bilateral filter.
    """
    img = _pil_to_cv2(image)
    # Use the image itself as the guide
    # radius=16: larger filter window = stronger smoothing
    # eps=0.4*(255**2): higher = more smoothing
    filtered = cv2.ximgproc.guidedFilter(
        guide=img, src=img, radius=16, eps=0.4 * (255 ** 2)
    )
    return _cv2_to_pil(filtered)


def apply_median_filter(image: Image.Image) -> Image.Image:
    """
    Median filter — replaces each pixel with median of its neighbors.
    Best for removing salt-and-pepper / impulse noise.
    """
    img = _pil_to_cv2(image)
    # ksize=11: kernel size — larger = stronger noise removal
    filtered = cv2.medianBlur(img, ksize=11)
    return _cv2_to_pil(filtered)


# ---------------------------------------------------------------------------
# Dispatcher — maps feature name to processing function
# ---------------------------------------------------------------------------

PROCESSING_FUNCTIONS = {
    'SUPER_RESOLUTION': apply_super_resolution,
    'COLORIZATION': apply_colorization,
    'DE_BLUR': apply_deblur,
    'BILATERAL_FILTER': apply_bilateral_filter,
    'GAUSSIAN_FILTER': apply_gaussian_filter,
    'GUIDED_FILTER': apply_guided_filter,
    'MEDIAN_FILTER': apply_median_filter,
}


def process_image(image: Image.Image, feature: str) -> Image.Image:
    """
    Dispatch image processing based on the selected feature.

    Args:
        image: PIL Image to process.
        feature: One of SUPER_RESOLUTION, COLORIZATION, DE_BLUR,
                 BILATERAL_FILTER, GAUSSIAN_FILTER, GUIDED_FILTER, MEDIAN_FILTER.

    Returns:
        Processed PIL Image.

    Raises:
        ValueError: If the feature is not recognized.
    """
    func = PROCESSING_FUNCTIONS.get(feature)
    if func is None:
        raise ValueError(f"Unknown feature: {feature}")
    return func(image)
