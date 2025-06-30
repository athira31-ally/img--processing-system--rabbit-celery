from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from celery_app import celery_app, process_image_task
import os
import uuid
import shutil
import pika
from typing import Optional
import uvicorn

# FastAPI app
app = FastAPI(title="Image Processing API with RabbitMQ")

def check_rabbitmq():
    """Check RabbitMQ connection"""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        connection.close()
        return True
    except Exception as e:
        print(f"RabbitMQ connection failed: {e}")
        return False

@app.get("/")
async def root():
    """Health check endpoint"""
    rabbitmq_status = check_rabbitmq()
    
    return {
        "message": "Image Processing API with RabbitMQ",
        "status": "running",
        "rabbitmq_connected": rabbitmq_status,
        "available_operations": ["blur", "sharpen", "grayscale", "resize", "brightness", "contrast"]
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    rabbitmq_status = check_rabbitmq()
    
    # Check if directories exist
    uploads_exist = os.path.exists("uploads")
    processed_exist = os.path.exists("processed")
    
    return {
        "api_status": "healthy",
        "rabbitmq_connected": rabbitmq_status,
        "uploads_directory": uploads_exist,
        "processed_directory": processed_exist,
        "celery_configured": True
    }

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join("uploads", filename)
    
    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "Image uploaded successfully",
            "file_id": file_id,
            "filename": filename,
            "file_path": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

@app.post("/process/{file_id}")
async def process_image(
    file_id: str,
    operation: str = Form(...),
    intensity: Optional[float] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None)
):
    """Process an uploaded image"""
    
    # Find the uploaded file
    uploads_dir = "uploads"
    uploaded_file = None
    
    for filename in os.listdir(uploads_dir):
        if filename.startswith(file_id):
            uploaded_file = os.path.join(uploads_dir, filename)
            break
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Prepare task parameters
    task_params = {}
    if intensity is not None:
        task_params["intensity"] = intensity
    if width is not None:
        task_params["width"] = width
    if height is not None:
        task_params["height"] = height
    
    # Send task to Celery
    try:
        task = process_image_task.delay(uploaded_file, operation, **task_params)
        
        return {
            "message": "Image processing started",
            "task_id": task.id,
            "file_id": file_id,
            "operation": operation,
            "parameters": task_params
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Check processing task status"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                "task_id": task_id,
                "status": "processing",
                "message": "Task is being processed"
            }
        elif task_result.state == 'SUCCESS':
            response = {
                "task_id": task_id,
                "status": "completed",
                "result": task_result.result
            }
        else:
            response = {
                "task_id": task_id,
                "status": "failed",
                "error": str(task_result.info)
            }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@app.get("/download/{task_id}")
async def download_processed_image(task_id: str):
    """Download processed image"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state != 'SUCCESS':
            raise HTTPException(status_code=400, detail="Task not completed successfully")
        
        result = task_result.result
        if result["status"] != "success":
            raise HTTPException(status_code=400, detail="Image processing failed")
        
        processed_path = result["processed_image"]
        
        if not os.path.exists(processed_path):
            raise HTTPException(status_code=404, detail="Processed image not found")
        
        return FileResponse(
            processed_path,
            media_type='image/jpeg',
            filename=os.path.basename(processed_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download image: {str(e)}")

@app.get("/list")
async def list_images():
    """List uploaded and processed images"""
    uploads = []
    processed = []
    
    if os.path.exists("uploads"):
        uploads = os.listdir("uploads")
    
    if os.path.exists("processed"):
        processed = os.listdir("processed")
    
    return {
        "uploaded_images": uploads,
        "processed_images": processed,
        "total_uploads": len(uploads),
        "total_processed": len(processed)
    }

if __name__ == "__main__":
    print("🚀 Starting Image Processing API with RabbitMQ")
    print("📊 Health check: http://localhost:8000/health")
    print("📚 API docs: http://localhost:8000/docs")
    print("🐰 RabbitMQ dashboard: http://localhost:15672 (guest/guest)")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
