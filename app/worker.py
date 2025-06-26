from celery import Celery
from PIL import Image
import os

# Configure Celery for Fargate deployment
app = Celery("worker")

app.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL", "sqs://"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "s3://your-image-processing-bucket-1750868832"),
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_transport_options={
        'region': os.getenv('AWS_DEFAULT_REGION', 'ap-south-1'),
        'visibility_timeout': 3600,
        'polling_interval': 1,
    },
    # S3 backend configuration
    s3_bucket=os.getenv('S3_BUCKET_NAME', 'your-image-processing-bucket-1750868832'),
    s3_key_prefix='celery-results/',
    s3_endpoint_url=None,
    s3_retry_policy={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
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
