from celery import Celery
from PIL import Image
import os

# Celery configuration with SQS
app = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL", "sqs://"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "s3://image-processor-bucket/celery-results/")
)

# Configure Celery for SQS
app.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL", "sqs://"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "s3://image-processor-bucket/celery-results/"),
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_transport_options={
        'region': os.getenv("AWS_DEFAULT_REGION", "ap-south-1"),
        'visibility_timeout': 3600,
        'polling_interval': 1,
    }
)

@app.task
def process_image(task_id: str, file_path: str):
    """Process image: resize and compress"""
    try:
        with Image.open(file_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            
            output_path = f"processed/{task_id}_processed.jpg"
            img.save(output_path, "JPEG", quality=85, optimize=True)
            
        return {
            "status": "completed",
            "original_file": file_path,
            "processed_file": output_path,
            "task_id": task_id
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@app.task
def test_task():
    return {"status": "success", "message": "Worker is running"}
