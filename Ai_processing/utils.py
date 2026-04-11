"""
Image processing utilities.

Each function takes a PIL Image and returns a processed PIL Image.
- DE_NOISE: Uses NAFNet ONNX model for AI-powered denoising.
- DE_BLUR: Placeholder — returns image unchanged (model not yet integrated).
- COLORIZATION: Placeholder — returns image unchanged (model not yet integrated).
- SUPER_RESOLUTION: Placeholder — returns image unchanged (model not yet integrated).
"""

import numpy as np
from PIL import Image

from .model_loader import run_nafnet_denoise


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

    Converts the PIL Image to a NumPy array, runs NAFNet inference,
    and returns the denoised result as a PIL Image.
    """
    # Ensure RGB mode
    if image.mode != "RGB":
        image = image.convert("RGB")

    # PIL → NumPy (H, W, C) uint8
    img_np = np.array(image)

    # Run NAFNet denoising
    denoised_np = run_nafnet_denoise(img_np)

    # NumPy → PIL
    return Image.fromarray(denoised_np)


def apply_deblur(image: Image.Image) -> Image.Image:
    """
    Placeholder for deblurring AI model.
    TODO: Replace with your actual deblurring model call.
    """
    return image


# Dispatcher — maps feature name to processing function
PROCESSING_FUNCTIONS = {
    'SUPER_RESOLUTION': apply_super_resolution,
    'COLORIZATION': apply_colorization,
    'DE_NOISE': apply_denoise,
    'DE_BLUR': apply_deblur,
}


def process_image(image: Image.Image, feature: str) -> Image.Image:
    """
    Dispatch image processing based on the selected feature.

    Args:
        image: PIL Image to process.
        feature: One of SUPER_RESOLUTION, COLORIZATION, DE_NOISE, DE_BLUR.

    Returns:
        Processed PIL Image.

    Raises:
        ValueError: If the feature is not recognized.
    """
    func = PROCESSING_FUNCTIONS.get(feature)
    if func is None:
        raise ValueError(f"Unknown feature: {feature}")
    return func(image)
