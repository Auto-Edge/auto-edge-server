"""
CoreML Converter

Handles conversion from PyTorch to CoreML with FP16 quantization.
"""

import logging
from pathlib import Path

import coremltools as ct
import torch

logger = logging.getLogger(__name__)


class CoreMLConverter:
    """Converts traced PyTorch models to CoreML format."""

    def __init__(self, output_path: Path):
        """
        Initialize the converter.

        Args:
            output_path: Directory for output files.
        """
        self.output_path = output_path
        self.output_path.mkdir(parents=True, exist_ok=True)

    def convert(
        self,
        traced_model: torch.jit.ScriptModule,
        model_name: str,
    ) -> Path:
        """
        Convert a traced PyTorch model to CoreML with FP16 quantization.

        Args:
            traced_model: The traced PyTorch model.
            model_name: Name for the output model.

        Returns:
            Path to the converted .mlmodel file.
        """
        logger.info("Converting to CoreML with FLOAT16 precision...")

        # Define input shape for CoreML
        input_shape = ct.Shape(shape=(1, 3, 224, 224))

        # Convert using neuralnetwork format (more compatible with Linux/Docker)
        mlmodel = ct.convert(
            traced_model,
            inputs=[ct.TensorType(name="input", shape=input_shape)],
            convert_to="neuralnetwork",
        )

        # Apply FP16 quantization for edge optimization
        mlmodel = ct.models.neural_network.quantization_utils.quantize_weights(
            mlmodel,
            nbits=16,
        )

        # Determine output path
        output_file = self.output_path / f"{model_name}.mlmodel"

        # Remove existing if present
        if output_file.exists():
            output_file.unlink()

        # Save the model
        mlmodel.save(str(output_file))
        logger.info(f"CoreML model saved to: {output_file}")

        return output_file
