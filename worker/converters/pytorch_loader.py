"""
PyTorch Model Loader

Handles loading and tracing PyTorch models for conversion.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import torch
import torchvision.models as models

logger = logging.getLogger(__name__)


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
                model = torch.load(file_path, map_location="cpu", weights_only=False)

                if isinstance(model, dict):
                    # If it's a state dict, we need a model architecture
                    logger.warning("State dict detected, falling back to MobileNetV2")
                    raise ValueError("State dict requires model architecture")

                model_name = Path(file_path).stem
                return model, model_name, Path(file_path)

            except Exception as e:
                logger.warning(f"Failed to load model: {e}. Using fallback.")

        # Fallback: Use pretrained MobileNetV2
        return self._load_fallback_model()

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
