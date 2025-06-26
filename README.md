# image-processing-system
Image processing API with FastAPI and Celery

# Image Processing Service
A image processing service built with FastAPI and Celery, deployed on AWS using ECS Fargate, SQS, and S3.

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


1. **Clone the repository**
   
   ```bash
   git clone https://github.com/athira31-ally/image-processing-service.git
   cd image-processing-service
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and configuration
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/



### Environment Variables

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-south-1

# S3 Configuration
S3_BUCKET_NAME=your-image-processing-bucket-1750868832

# SQS Configuration
SQS_QUEUE_URL=https://sqs.ap-south-1.amazonaws.com/534211282949/celery-queue

# Application Configuration
API_PORT=8000
WORKER_CONCURRENCY=4
```

## 🌩️ AWS Deployment

### Prerequisites

1. **AWS CLI configured**
2. **ECR repositories created**
3. **ECS cluster setup**
4. **S3 bucket created**
5. **SQS queue created**

### Step-by-Step Deployment

1. **Building and Push Docker Images**
   ```bash
   **# Build API image**
   docker build -f docker/Dockerfile.api -t image-processor-api .
   docker tag image-processor-api:latest 534211282949.dkr.ecr.ap-south-1.amazonaws.com/image-processor-api:latest
   docker push 534211282949.dkr.ecr.ap-south-1.amazonaws.com/image-processor-api:latest

   # Build Worker image
   docker build -f docker/Dockerfile.worker -t image-processor-worker .
   docker tag image-processor-worker:latest 534211282949.dkr.ecr.ap-south-1.amazonaws.com/image-processor-worker:latest
   docker push 534211282949.dkr.ecr.ap-south-1.amazonaws.com/image-processor-worker:latest
   ```

2. **Creating ECS Task Definitions**
   ```bash
   aws ecs register-task-definition --cli-input-json file://aws/api-task-definition.json
   aws ecs register-task-definition --cli-input-json file://aws/worker-task-definition.json
   ```

3. **Creating ECS Services**
   ```bash
   # Create API service
   aws ecs create-service \
     --cluster your-cluster-name \
     --service-name image-processor-api \
     --task-definition image-processor-api \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"

   # Create Worker service
   aws ecs create-service \
     --cluster your-cluster-name \
     --service-name image-processor-worker \
     --task-definition image-processor-worker \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
   ```

### Local Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run API locally**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

3. **Run Worker locally**
   ```bash
   celery -A app.worker.app worker --loglevel=info
   ```



