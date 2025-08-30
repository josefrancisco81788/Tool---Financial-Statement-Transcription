#!/bin/bash

# Deploy the CSV fix to Cloud Run
echo "🚀 Deploying CSV fix to Cloud Run..."

# Build the new image
echo "📦 Building new Docker image..."
docker build -t gcr.io/financial-statement-transcription/fin-api:csv-fix .

# Push to Google Container Registry
echo "📤 Pushing to Google Container Registry..."
docker push gcr.io/financial-statement-transcription/fin-api:csv-fix

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy financial-statement-transcription-api \
  --image gcr.io/financial-statement-transcription/fin-api:csv-fix \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --cpu 2 \
  --memory 4Gi \
  --timeout 60m \
  --concurrency 1 \
  --max-instances 2

echo "✅ Deployment complete!"
echo "🌐 Your API URL: https://financial-statement-transcription-api-1027259334816.asia-southeast1.run.app"
echo ""
echo "🧪 Test the fix with:"
echo "python test_cloudrun_afs2024.py"
