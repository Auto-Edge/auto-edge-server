"""
PyTorch Model Loader

Handles loading and tracing PyTorch models for conversion.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple

import torch
import torchvision.models as models

logger = logging.getLogger(__name__)

# Map filename patterns to torchvision model constructors
TORCHVISION_MODELS = {
    "vit_b_16": models.vit_b_16,
    "vit_b_32": models.vit_b_32,
    "vit_l_16": models.vit_l_16,
    "vit_l_32": models.vit_l_32,
    "resnet18": models.resnet18,
    "resnet34": models.resnet34,
    "resnet50": models.resnet50,
    "resnet101": models.resnet101,
    "resnet152": models.resnet152,
    "mobilenet_v2": models.mobilenet_v2,
    "mobilenet_v3_small": models.mobilenet_v3_small,
    "mobilenet_v3_large": models.mobilenet_v3_large,
    "efficientnet_b0": models.efficientnet_b0,
    "efficientnet_b1": models.efficientnet_b1,
    "efficientnet_b2": models.efficientnet_b2,
    "efficientnet_b3": models.efficientnet_b3,
    "efficientnet_b4": models.efficientnet_b4,
    "efficientnet_v2_s": models.efficientnet_v2_s,
    "efficientnet_v2_m": models.efficientnet_v2_m,
    "densenet121": models.densenet121,
    "densenet169": models.densenet169,
    "densenet201": models.densenet201,
    "squeezenet1_0": models.squeezenet1_0,
    "squeezenet1_1": models.squeezenet1_1,
    "shufflenet_v2_x0_5": models.shufflenet_v2_x0_5,
    "shufflenet_v2_x1_0": models.shufflenet_v2_x1_0,
    "alexnet": models.alexnet,
    "vgg11": models.vgg11,
    "vgg13": models.vgg13,
    "vgg16": models.vgg16,
    "vgg19": models.vgg19,
    "googlenet": models.googlenet,
    "inception_v3": models.inception_v3,
    "regnet_x_400mf": models.regnet_x_400mf,
    "regnet_y_400mf": models.regnet_y_400mf,
    "convnext_tiny": models.convnext_tiny,
    "convnext_small": models.convnext_small,
    "convnext_base": models.convnext_base,
    "swin_t": models.swin_t,
    "swin_s": models.swin_s,
    "swin_b": models.swin_b,
}


class PyTorchLoader:
    """Loads and prepares PyTorch models for conversion."""

    def __init__(self, shared_data_path: Path):
        """
        Initialize the loader.

        Args:
            shared_data_path: Path to shared data directory.
        """
        self.shared_data_path = shared_data_path
        self.shared_data_path.mkdir(parents=True, exist_ok=True)

    def load_model(
        self,
        file_path: Optional[str],
    ) -> Tuple[torch.nn.Module, str, Path]:
        """
        Load a PyTorch model from file or use fallback MobileNetV2.

        Args:
            file_path: Path to the PyTorch model file, or None for fallback.

        Returns:
            Tuple of (model, model_name, original_model_path).
        """
        if file_path and Path(file_path).exists():
            logger.info(f"Loading model from: {file_path}")
            try:
                # Try loading as a full model first
                loaded = torch.load(file_path, map_location="cpu", weights_only=False)

                if isinstance(loaded, dict):
                    # State dict detected - try to infer architecture from filename
                    model_name = self._infer_model_name(file_path)
                    if model_name and model_name in TORCHVISION_MODELS:
                        logger.info(f"State dict detected, using architecture: {model_name}")
                        model = TORCHVISION_MODELS[model_name](weights=None)
                        model.load_state_dict(loaded)
                        return model, model_name, Path(file_path)
                    else:
                        logger.warning(f"Unknown model architecture for: {file_path}")
                        raise ValueError("Cannot infer model architecture from filename")

                model_name = Path(file_path).stem
                return loaded, model_name, Path(file_path)

            except Exception as e:
                logger.warning(f"Failed to load model: {e}. Using fallback.")

        # Fallback: Use pretrained MobileNetV2
        return self._load_fallback_model()

    def _infer_model_name(self, file_path: str) -> Optional[str]:
        """
        Infer torchvision model name from filename.

        Args:
            file_path: Path to the model file.

        Returns:
            Model name if recognized, None otherwise.
        """
        filename = Path(file_path).stem.lower()

        # Try exact match first, then prefix match
        for model_name in TORCHVISION_MODELS:
            # Match patterns like "vit_b_16-c867db91" or "resnet50"
            pattern = rf"^{re.escape(model_name)}([_-]|$)"
            if re.match(pattern, filename):
                return model_name

        return None

    def _load_fallback_model(self) -> Tuple[torch.nn.Module, str, Path]:
        """Load the fallback MobileNetV2 model."""
        logger.info("Using fallback model: MobileNetV2 (pretrained)")

        model = models.mobilenet_v2(
            weights=models.MobileNet_V2_Weights.IMAGENET1K_V1
        )
        model_name = "mobilenet_v2_demo"

        # Save the model to get accurate size measurement
        temp_path = self.shared_data_path / f"{model_name}.pt"
        torch.save(model, temp_path)

        return model, model_name, temp_path

    def trace_model(self, model: torch.nn.Module) -> torch.jit.ScriptModule:
        """
        Trace a PyTorch model for conversion.

        Args:
            model: The PyTorch model to trace.

        Returns:
            Traced ScriptModule ready for CoreML conversion.
        """
        model.eval()

        # Standard ImageNet input shape
        example_input = torch.rand(1, 3, 224, 224)

        with torch.no_grad():
            traced_model = torch.jit.trace(model, example_input)

        return traced_model

    def get_file_size_mb(self, path: Path) -> float:
        """
        Calculate the size of a file or directory in megabytes.

        Args:
            path: Path to the file or directory.

        Returns:
            Size in megabytes rounded to 2 decimal places.
        """
        if not path.exists():
            return 0.0

        if path.is_file():
            size_bytes = path.stat().st_size
        elif path.is_dir():
            size_bytes = sum(
                f.stat().st_size for f in path.rglob("*") if f.is_file()
            )
        else:
            return 0.0

        return round(size_bytes / (1024 * 1024), 2)
