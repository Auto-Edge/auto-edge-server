import os
import tempfile
import logging
import requests
import boto3
import coremltools as ct
import torch
from pathlib import Path
from celery import Task
from botocore.exceptions import ClientError

from celery_app import app
from config import settings
from converters.coreml_converter import CoreMLConverter
from converters.pytorch_loader import PyTorchLoader

# Setup Logging
logger = logging.getLogger(__name__)

# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

class MLCleaningTask(Task):
    """Abstract task to ensure temporary files are cleaned up."""
    abstract = True
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        # Implementation for cleanup if needed beyond tempfile context managers
        pass

@app.task(bind=True, base=MLCleaningTask, name="tasks.conversion.convert_model")
def convert_model(self, job_id: str, s3_key: str):
    """
    Downloads a PyTorch model from S3, converts to CoreML, uploads back to S3,
    and notifies the Go API via Webhook.
    """
    logger.info(f"Starting job {job_id} for key {s3_key}")
    
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        input_path = temp_dir / "model.pt"
        
        # Initialize helper classes
        loader = PyTorchLoader(temp_dir)
        converter = CoreMLConverter(temp_dir)
        
        try:
            # 1. Download from S3
            downloaded_model_path = None
            if s3_key and s3_key != "demo":
                logger.info(f"Downloading s3://{settings.S3_BUCKET_NAME}/{s3_key}")
                try:
                    s3_client.download_file(settings.S3_BUCKET_NAME, s3_key, str(input_path))
                    downloaded_model_path = str(input_path)
                except Exception as s3_err:
                    logger.error(f"Failed to download from S3: {s3_err}")
                    raise s3_err
            else:
                 logger.info("Demo mode requested, using fallback model.")

            # 2. Load and Trace
            logger.info("Loading PyTorch model...")
            model, model_name, original_path = loader.load_model(downloaded_model_path)
            
            logger.info(f"Tracing model {model_name}...")
            traced_model = loader.trace_model(model)
            
            # 3. Convert to CoreML
            logger.info("Converting to CoreML...")
            # We use job_id as the model name for uniqueness in the output filename
            output_file = converter.convert(traced_model, f"{job_id}") 
            
            # 4. Upload Result to S3
            # The converter produces a .mlmodel file (neuralnetwork)
            s3_compiled_key = f"compiled/{job_id}.mlmodel"
            
            logger.info(f"Uploading to s3://{settings.S3_BUCKET_NAME}/{s3_compiled_key}")
            s3_client.upload_file(str(output_file), settings.S3_BUCKET_NAME, s3_compiled_key)

            original_size = loader.get_file_size_mb(original_path)
            optimized_size = loader.get_file_size_mb(output_file)

            # 5. Success Webhook
            payload = {
                "job_id": job_id,
                "status": "completed",
                "s3_compiled_key": s3_compiled_key,
                "metadata": {
                    "original_size_mb": original_size,
                    "optimized_size_mb": optimized_size,
                    "model_name": model_name
                }
            }
            send_webhook(payload)
            
            return payload
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            # 6. Failure Webhook
            payload = {
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            }
            send_webhook(payload)
            # Re-raise to mark task as failed in Celery
            raise e

def send_webhook(json_payload: dict):
    """Sends a POST request to the Go API Gateway."""
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Secret": settings.WEBHOOK_SECRET
    }
    
    try:
        response = requests.post(
            settings.WEBHOOK_URL, 
            json=json_payload, 
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Webhook sent successfully: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send webhook: {e}")
