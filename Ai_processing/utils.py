"""
Image processing utilities.

Each function takes a PIL Image and returns a processed PIL Image.
These are PLACEHOLDER implementations using basic Pillow filters.
Replace them with your actual AI model inference calls.
"""

from PIL import Image, ImageFilter, ImageEnhance


def apply_super_resolution(image: Image.Image) -> Image.Image:
    """
    Placeholder for super-resolution AI model.
    Currently: upscales 2x with LANCZOS resampling + sharpens.
    TODO: Replace with your actual super-resolution model call.
    """
    width, height = image.size
    upscaled = image.resize((width * 2, height * 2), Image.LANCZOS)
    sharpened = upscaled.filter(ImageFilter.SHARPEN)
    return sharpened


def apply_basic_filter(image: Image.Image) -> Image.Image:
    """
    Placeholder for basic filter processing.
    Currently: enhances contrast + color saturation.
    TODO: Replace with your actual filter logic.
    """
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.3)
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.2)
    return image


def apply_denoise(image: Image.Image) -> Image.Image:
    """
    Placeholder for denoising AI model.
    Currently: applies a smooth filter.
    TODO: Replace with your actual denoising model call.
    """
    return image.filter(ImageFilter.SMOOTH_MORE)


def apply_deblur(image: Image.Image) -> Image.Image:
    """
    Placeholder for deblurring AI model.
    Currently: applies an unsharp mask.
    TODO: Replace with your actual deblurring model call.
    """
    return image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))


def apply_shadow_removal(image: Image.Image) -> Image.Image:
    """
    Placeholder for shadow removal AI model.
    Currently: brightens the image.
    TODO: Replace with your actual shadow removal model call.
    """
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(1.4)


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
