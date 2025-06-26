
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import shutil
from celery import Celery

app = FastAPI(title="Image Processing API")

# Configure Celery for Fargate deployment
celery_app = Celery("worker")
celery_app.conf.update(
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

@app.get("/")
def root():
    return {"message": "Image Processing API", "status": "running"}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("processed", exist_ok=True)
    
    file_extension = file.filename.split(".")[-1]
    original_filename = f"uploads/{task_id}_original.{file_extension}"
    
    with open(original_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    celery_task = celery_app.send_task(
        "worker.process_image",
        args=[task_id, original_filename]
    )
    
    return {
        "task_id": task_id,
        "celery_task_id": celery_task.id,
        "status": "processing",
        "message": "Image uploaded and processing started",
        "status_url": f"/status/{task_id}"
    }

@app.get("/status/{task_id}")
def get_task_status(task_id: str):
    result_file = f"processed/{task_id}_processed.jpg"
    
    # Check multiple possible original file extensions
    original_file = None
    for ext in ['jpeg', 'jpg', 'png']:
        potential_file = f"uploads/{task_id}_original.{ext}"
        if os.path.exists(potential_file):
            original_file = potential_file
            break
    
    if os.path.exists(result_file) and original_file:
        original_size = os.path.getsize(original_file) / (1024 * 1024)
        processed_size = os.path.getsize(result_file) / (1024 * 1024)
        compression_ratio = ((original_size - processed_size) / original_size) * 100
        
        return {
            "task_id": task_id,
            "status": "COMPLETED",
            "message": "Image processing completed",
            "result": {
                "original_file": original_file,
                "processed_file": result_file,
                "original_size_mb": round(original_size, 2),
                "processed_size_mb": round(processed_size, 2),
                "compression_ratio": round(compression_ratio, 1),
                "download_url": f"/download/{task_id}"
            }
        }
    else:
        return {
            "task_id": task_id,
            "status": "PROCESSING", 
            "message": "Image is being processed"
        }

@app.get("/download/{file_id}")
def download_file(file_id: str):
    file_path = f"processed/{file_id}_processed.jpg"
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            filename=f"{file_id}_processed.jpg",
            media_type="image/jpeg"
        )
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/test")
def test_worker():
    task = celery_app.send_task("worker.test_task")
    return {"message": "Test task sent", "task_id": task.id}
