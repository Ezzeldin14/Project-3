"""
Image processing utilities.

Each function takes a PIL Image and returns a processed PIL Image.
- DE_NOISE: Uses NAFNet ONNX model for AI-powered denoising.
- DE_BLUR: Placeholder — returns image unchanged (model not yet integrated).
- COLORIZATION: Placeholder — returns image unchanged (model not yet integrated).
- SUPER_RESOLUTION: Placeholder — returns image unchanged (model not yet integrated).
- BILATERAL_FILTER: OpenCV bilateral filter (edge-preserving smoothing).
- GAUSSIAN_FILTER: OpenCV Gaussian blur.
- GUIDED_FILTER: OpenCV guided filter (edge-aware smoothing).
- MEDIAN_FILTER: OpenCV median blur (salt-and-pepper noise removal).
"""

import cv2
import numpy as np
from PIL import Image

from .model_loader import run_nafnet_denoise


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
    Placeholder for super-resolution AI model.
    TODO: Replace with your actual super-resolution model call.
    """
    return image


def apply_colorization(image: Image.Image) -> Image.Image:
    """
    Placeholder for colorization AI model.
    TODO: Replace with your actual colorization model call.
    """
    return image


def apply_denoise(image: Image.Image) -> Image.Image:
    """
    Denoise an image using the NAFNet ONNX model.
    """
    if image.mode != "RGB":
        image = image.convert("RGB")
    img_np = np.array(image)
    denoised_np = run_nafnet_denoise(img_np)
    return Image.fromarray(denoised_np)


def apply_deblur(image: Image.Image) -> Image.Image:
    """
    Placeholder for deblurring AI model.
    TODO: Replace with your actual deblurring model call.
    """
    return image


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
    'DE_NOISE': apply_denoise,
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
        feature: One of SUPER_RESOLUTION, COLORIZATION, DE_NOISE, DE_BLUR,
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
