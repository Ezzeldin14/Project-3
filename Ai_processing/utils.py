"""
Image processing utilities.

Each function takes a PIL Image and returns a processed PIL Image.
Currently all functions return the image UNCHANGED (pass-through).
Replace each one with your actual AI model inference call.
"""

from PIL import Image


def apply_super_resolution(image: Image.Image) -> Image.Image:
    """
    Placeholder for super-resolution AI model.
    Currently: returns image unchanged.
    TODO: Replace with your actual super-resolution model call.
    """
    return image


def apply_basic_filter(image: Image.Image) -> Image.Image:
    """
    Placeholder for basic filter processing.
    Currently: returns image unchanged.
    TODO: Replace with your actual filter logic.
    """
    return image


def apply_denoise(image: Image.Image) -> Image.Image:
    """
    Placeholder for denoising AI model.
    Currently: returns image unchanged.
    TODO: Replace with your actual denoising model call.
    """
    return image


def apply_deblur(image: Image.Image) -> Image.Image:
    """
    Placeholder for deblurring AI model.
    Currently: returns image unchanged.
    TODO: Replace with your actual deblurring model call.
    """
    return image


def apply_shadow_removal(image: Image.Image) -> Image.Image:
    """
    Placeholder for shadow removal AI model.
    Currently: returns image unchanged.
    TODO: Replace with your actual shadow removal model call.
    """
    return image


# Dispatcher — maps feature name to processing function
PROCESSING_FUNCTIONS = {
    'SUPER_RESOLUTION': apply_super_resolution,
    'BASIC_FILTER': apply_basic_filter,
    'DE_NOISE': apply_denoise,
    'DE_BLUR': apply_deblur,
    'SHADOW_REMOVAL': apply_shadow_removal,
}


def process_image(image: Image.Image, feature: str) -> Image.Image:
    """
    Dispatch image processing based on the selected feature.

    Args:
        image: PIL Image to process.
        feature: One of SUPER_RESOLUTION, BASIC_FILTER, DE_NOISE, DE_BLUR, SHADOW_REMOVAL.

    Returns:
        Processed PIL Image.

    Raises:
        ValueError: If the feature is not recognized.
    """
    func = PROCESSING_FUNCTIONS.get(feature)
    if func is None:
        raise ValueError(f"Unknown feature: {feature}")
    return func(image)
