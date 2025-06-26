from celery import Celery
from PIL import Image
import os

app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

@app.task
def process_image(task_id: str, file_path: str):
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
