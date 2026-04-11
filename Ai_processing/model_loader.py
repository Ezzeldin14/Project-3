"""
Singleton model loader for ONNX Runtime inference.

Loads AI models once at first request and reuses them across all subsequent
requests to minimise memory usage and startup time on constrained hosts
(e.g. Railway free tier with 1 GB RAM).
"""

import os
import logging

import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)

# Directory where .onnx model files are stored
_MODELS_DIR = os.path.join(os.path.dirname(__file__), "models_data")

# Cache for loaded ONNX sessions (singleton pattern)
_sessions: dict[str, ort.InferenceSession] = {}


def _get_session(model_filename: str) -> ort.InferenceSession:
    """
    Return a cached ONNX InferenceSession, creating it on first call.
    """
    if model_filename not in _sessions:
        model_path = os.path.join(_MODELS_DIR, model_filename)
        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"Model file not found: {model_path}. "
                f"Please place your .onnx file in {_MODELS_DIR}/"
            )

        logger.info("Loading ONNX model: %s", model_path)

        # Optimise for CPU – keep memory low
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = 2  # Railway free gives 2 vCPU
        opts.inter_op_num_threads = 1

        _sessions[model_filename] = ort.InferenceSession(
            model_path,
            sess_options=opts,
            providers=["CPUExecutionProvider"],
        )
        logger.info("Model loaded successfully: %s", model_filename)

    return _sessions[model_filename]


def run_nafnet_denoise(image_np: np.ndarray) -> np.ndarray:
    """
    Run NAFNet denoising on a NumPy image (H, W, C) in uint8 [0-255].

    The model expects input as float32 in [0, 1] with shape (1, C, H, W).
    Input dimensions must be multiples of 32; this function handles padding.

    Returns a uint8 NumPy image (H, W, C) in [0-255].
    """
    session = _get_session("nafnet_denoise.onnx")

    h, w, c = image_np.shape

    # --- Pad to multiples of 32 (NAFNet requirement) ---
    pad_h = (32 - h % 32) % 32
    pad_w = (32 - w % 32) % 32
    if pad_h or pad_w:
        image_np = np.pad(
            image_np,
            ((0, pad_h), (0, pad_w), (0, 0)),
            mode="reflect",
        )

    # --- Preprocess: HWC uint8 → NCHW float32 [0, 1] ---
    img_float = image_np.astype(np.float32) / 255.0
    img_nchw = np.transpose(img_float, (2, 0, 1))  # HWC → CHW
    img_batch = np.expand_dims(img_nchw, axis=0)     # CHW → NCHW

    # --- Run inference ---
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    result = session.run([output_name], {input_name: img_batch})[0]

    # --- Postprocess: NCHW float32 → HWC uint8 ---
    result = np.squeeze(result, axis=0)              # NCHW → CHW
    result = np.transpose(result, (1, 2, 0))         # CHW → HWC
    result = np.clip(result * 255.0, 0, 255).astype(np.uint8)

    # --- Remove padding ---
    if pad_h or pad_w:
        result = result[:h, :w, :]

    return result
