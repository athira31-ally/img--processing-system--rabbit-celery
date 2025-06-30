from celery import Celery
import os
from PIL import Image, ImageFilter, ImageEnhance

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)

# Get broker URL from environment (Render will provide this)
broker_url = os.getenv('CELERY_BROKER_URL', 'pyamqp://guest:guest@localhost:5672//')

# Celery configuration with RabbitMQ
celery_app = Celery(
    'image_processor',
    broker=broker_url,
    backend='rpc://'
)

# Celery task configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(bind=True)
def process_image_task(self, image_path: str, operation: str, **kwargs):
    """Process image using Celery task"""
    try:
        print(f"Processing image: {image_path} with operation: {operation}")
        
        # Open image
        image = Image.open(image_path)
        
        # Apply operation
        if operation == "blur":
            intensity = kwargs.get('intensity', 2)
            processed_image = image.filter(ImageFilter.GaussianBlur(radius=intensity))
        
        elif operation == "sharpen":
            intensity = kwargs.get('intensity', 1)
            processed_image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150*intensity, threshold=3))
        
        elif operation == "grayscale":
            processed_image = image.convert('L')
        
        elif operation == "resize":
            width = kwargs.get('width', 800)
            height = kwargs.get('height', 600)
            processed_image = image.resize((width, height))
        
        elif operation == "brightness":
            intensity = kwargs.get('intensity', 1.5)
            enhancer = ImageEnhance.Brightness(image)
            processed_image = enhancer.enhance(intensity)
        
        elif operation == "contrast":
            intensity = kwargs.get('intensity', 1.5)
            enhancer = ImageEnhance.Contrast(image)
            processed_image = enhancer.enhance(intensity)
        
        else:
            # Default: just copy the image
            processed_image = image
        
        # Save processed image
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        processed_filename = f"{name}_processed{ext}"
        processed_path = os.path.join("processed", processed_filename)
        
        processed_image.save(processed_path)
        
        print(f"Image processed successfully: {processed_path}")
        return {
            "status": "success",
            "processed_image": processed_path,
            "original_image": image_path,
            "operation": operation
        }
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
