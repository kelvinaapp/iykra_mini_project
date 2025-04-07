#!/bin/bash

# Exit on any error
set -e

# Configuration
PROJECT_ID="iykra-sentiment-analysis"
SERVICE_NAME="motorcycle-service-prediction"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "Building and deploying ${SERVICE_NAME} to Cloud Run..."

# Build the Docker image
echo "Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Push the image to Google Container Registry
echo "Pushing image to Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300s \
  --startup-cpu-boost \
  --cpu-throttling \
  --startup-cpu 2

# Set IAM policy to allow public access
echo "Setting IAM policy to allow public access..."
gcloud beta run services add-iam-policy-binding \
  --region=${REGION} \
  --member=allUsers \
  --role=roles/run.invoker \
  ${SERVICE_NAME}

echo "Deployment complete! Your service is now available at:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)"
