
# Image Processing System - RabbitMQ + Celery

A scalable image processing API built with FastAPI, Celery, and RabbitMQ for background task processing.

## Repository
https://github.com/athira31-ally/img--processing-system--rabbit-celery

## Features

- 🚀 **FastAPI** - High-performance async web framework
- 🐰 **RabbitMQ** - Message broker for reliable task queuing
- ⚡ **Celery** - Distributed task queue for background processing
- 🖼️ **Image Processing** - Multiple operations (blur, sharpen, grayscale, resize, brightness, contrast)
- 📚 **Interactive Docs** - Automatic API documentation

## Local Setup

1. **Start RabbitMQ:**
   ```bash
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
