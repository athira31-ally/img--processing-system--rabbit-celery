# image-processing-system
Image processing API with FastAPI and Celery

# Image Processing Service
An image processing service built with FastAPI and Celery, deployed on AWS using ECS Fargate, SQS, and S3.

# Architecture flow
       
   FastAPI API   ────------   Amazon SQS               ────  Celery Worker  
   (ECS Fargate)             (Message Queue, Broker)         (ECS Fargate)  
       
         │                                                       │
         │                                                       │
         ▼                                                       ▼
                           
   Amazon S3     ◄───────────────────────────------     Image         
   (File Storage)                                      Processing    
                           
## Features

- Upload images and get an immediate response while processing happens in the background
- Images stored securely in Amazon S3 buckets
-  Automatic resizing, format conversion, and compression
-  Containerised with Docker, deployed on AWS ECS Fargate


### Step 1: Clone and Setup
```bash
git clone https://github.com/athira31-ally/image-processing-system.git
cd image-processing-system
cp .env.example .env
```

### Step 2: Adding Your AWS Keys to .env
```bash
nano .env
```
Replace with your real AWS credentials:
```
AWS_ACCESS_KEY_ID=AKIA...your_key_here
AWS_SECRET_ACCESS_KEY=...your_secret_here
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET_NAME=your-image-processing-bucket-1750868832
```

### Step 3: Start the Application
```bash
docker-compose up --build
```


### Step 4: Test It Works
```bash
# Test API
curl http://localhost:8000/

# Upload an image
curl -o test.jpg "https://picsum.photos/800/600"
curl -X POST "http://localhost:8000/upload-image/" -F "file=@test.jpg"

# Check processing status (replace task_id with actual ID from response to know the status)
curl "http://localhost:8000/status/YOUR_TASK_ID"
```
**##Deployment**


aws configure ( enter access key,secret key ,region)


# 1. Login to ECR
 ```aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 534211282949.dkr.ecr.ap-south-1.amazonaws.com```

# 2. Build for AMD64 platform (critical for Fargate compatibility)
```docker build --platform linux/amd64 -t 534211282949.dkr.ecr.ap-south-1.amazonaws.com/image-processor-api:latest .
docker build --platform linux/amd64 -f Dockerfile.worker -t 534211282949.dkr.ecr.ap-south-1.amazonaws.com/image-processor-worker:latest .```

# **3. Push images
```docker push 534211282949.dkr.ecr.ap-south-1.amazonaws.com/image-processor-api:latest
docker push 534211282949.dkr.ecr.ap-south-1.amazonaws.com/image-processor-worker:latest```

# 4. Update ECS services (triggers deployment)
```aws ecs update-service --cluster image-processor-cluster --service api-service --force-new-deployment
aws ecs update-service --cluster image-processor-cluster --service worker-service --force-new-deployment```

# 5. Monitor deployment
```aws ecs describe-services --cluster image-processor-cluster --services api-service worker-service --query 'services[*].[serviceName,runningCount,desiredCount]' --output table```


Live Demo: http://image-processor-alb-1146437516.ap-south-1.elb.amazonaws.com
# Upload image
curl -X POST "http://image-processor-alb-1146437516.ap-south-1.elb.amazonaws.com/upload" -F "file=@test-image.jpg"

