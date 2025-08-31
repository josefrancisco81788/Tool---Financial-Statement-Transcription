# Cloud Run Deployment Verification Guide

## Overview
This guide helps verify whether the updated code with the CSV fix is actually deployed and active on Cloud Run.

## Current Issue
The CSV output still shows the missing year mapping row, indicating the Cloud Run service might not be using the updated code.

## Verification Steps

### 1. Check Current Deployment Status

#### 1.1 Using gcloud CLI (if available)
```bash
# Check the current deployment
gcloud run services describe financial-statement-transcription-api \
  --region=asia-southeast1 \
  --format="value(status.url,status.latestReadyRevisionName,status.conditions[0].status)"

# List all revisions
gcloud run revisions list \
  --service=financial-statement-transcription-api \
  --region=asia-southeast1 \
  --format="table(metadata.name,metadata.creationTimestamp,status.conditions[0].status)"
```

#### 1.2 Using Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Cloud Run** > **financial-statement-transcription-api**
3. Check the **Revisions** tab to see deployment history
4. Look for the latest revision and its status

### 2. Check Deployment Timestamp

#### 2.1 Check Last Deployment Time
```bash
# Get deployment information
gcloud run services describe financial-statement-transcription-api \
  --region=asia-southeast1 \
  --format="value(metadata.creationTimestamp,status.latestReadyRevisionName)"
```

#### 2.2 Compare with Code Changes
- Check when the CSV fix was implemented in the code
- Verify the deployment timestamp is after the code changes
- If deployment is older than code changes, a new deployment is needed

### 3. Force New Deployment

#### 3.1 Using deploy_fix.sh Script
```bash
# Run the deployment script we created earlier
./deploy_fix.sh
```

#### 3.2 Manual Deployment Commands
```bash
# Set project and region
gcloud config set project financial-statement-transcription
gcloud config set run/region asia-southeast1

# Build and push new image
docker build -t gcr.io/financial-statement-transcription/fin-api:csv-fix-v2 .
docker push gcr.io/financial-statement-transcription/fin-api:csv-fix-v2

# Deploy with new image
gcloud run deploy financial-statement-transcription-api \
  --image gcr.io/financial-statement-transcription/fin-api:csv-fix-v2 \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --cpu 2 \
  --memory 4Gi \
  --timeout 60m \
  --concurrency 1 \
  --max-instances 2
```

### 4. Add Version Identifier to Code

#### 4.1 Add Version Endpoint
Add this to your FastAPI app to track which version is deployed:

```python
# In api/main.py or app.py
@app.get("/version")
async def get_version():
    return {
        "version": "csv-fix-v2",
        "deployment_date": "2024-08-30",
        "fixes": ["Added year mapping row to CSV output"]
    }
```

#### 4.2 Check Version via API
```bash
# Test the version endpoint
curl -X GET "https://financial-statement-transcription-api-1027259334816.asia-southeast1.run.app/version"
```

### 5. Verify Deployment with Test

#### 5.1 Quick Deployment Test
```bash
# Create a deployment verification script
cat > verify_deployment.sh << 'EOF'
#!/bin/bash

API_URL="https://financial-statement-transcription-api-1027259334816.asia-southeast1.run.app"

echo "🔍 Verifying Cloud Run Deployment"
echo "================================="

# Check version (if endpoint exists)
echo "📋 Checking API version..."
curl -s "$API_URL/version" 2>/dev/null || echo "Version endpoint not available"

# Test with small file first
echo -e "\n🧪 Testing with sample data..."
curl -X POST "$API_URL/api/v1/extract-financial-data/sync" \
  -F "file=@AFS2024 - statement extracted.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=csv" \
  --max-time 60 \
  -o test_deployment.json

if [ $? -eq 0 ]; then
    echo "✅ API call successful"
    
    # Extract CSV and check for year mapping row
    jq -r '.csv_data' test_deployment.json > test_deployment.csv
    
    echo -e "\n📊 Checking for year mapping row..."
    YEAR_ROW=$(sed -n '2p' test_deployment.csv)
    echo "Line 2: $YEAR_ROW"
    
    if echo "$YEAR_ROW" | grep -q "2024\|2023"; then
        echo "✅ FIXED: Year mapping row is present!"
    else
        echo "❌ NOT FIXED: Year mapping row is still missing"
        echo "   This indicates the old code is still deployed"
    fi
    
    # Show first few lines
    echo -e "\n📋 CSV Preview:"
    head -3 test_deployment.csv
    
else
    echo "❌ API call failed"
fi

echo -e "\n🎯 Deployment verification complete!"
EOF

chmod +x verify_deployment.sh
./verify_deployment.sh
```

### 6. Alternative: Check Container Logs

#### 6.1 View Recent Logs
```bash
# Check recent logs for deployment activity
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=financial-statement-transcription-api" \
  --limit=20 \
  --format="value(timestamp,textPayload)"
```

#### 6.2 Check for Error Messages
```bash
# Look for deployment errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=financial-statement-transcription-api AND severity>=ERROR" \
  --limit=10
```

### 7. Force Traffic to New Revision

#### 7.1 Update Traffic
```bash
# Get the latest revision name
LATEST_REVISION=$(gcloud run revisions list \
  --service=financial-statement-transcription-api \
  --region=asia-southeast1 \
  --format="value(metadata.name)" \
  --limit=1)

# Update traffic to latest revision
gcloud run services update-traffic financial-statement-transcription-api \
  --region=asia-southeast1 \
  --to-revisions=$LATEST_REVISION=100
```

### 8. Verify Fix is Active

#### 8.1 Run Complete Test
```bash
# Run the full test to verify the fix
export API_URL="https://financial-statement-transcription-api-1027259334816.asia-southeast1.run.app"

curl -X POST "$API_URL/api/v1/extract-financial-data/sync" \
  -F "file=@AFS2024 - statement extracted.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=both" \
  --max-time 300 \
  -o final_test_response.json

# Extract and check CSV
jq -r '.csv_data' final_test_response.json > final_test.csv

echo "=== CHECKING FOR YEAR MAPPING ROW ==="
sed -n '2p' final_test.csv

echo -e "\n=== EXPECTED FORMAT ==="
echo "Date,Year,Year,,0.0,2024,2023,,"

echo -e "\n=== ACTUAL FORMAT ==="
head -3 final_test.csv
```

## Common Issues and Solutions

### Issue 1: Deployment Not Triggered
**Symptoms**: Code changes not reflected in API
**Solution**: Force new deployment with different image tag

### Issue 2: Old Revision Still Active
**Symptoms**: New deployment exists but old code still running
**Solution**: Update traffic to new revision

### Issue 3: Build Cache Issues
**Symptoms**: Docker build uses cached layers
**Solution**: Use `--no-cache` flag in docker build

### Issue 4: Environment Variables
**Symptoms**: Code changes not taking effect
**Solution**: Check if environment variables need updating

## Next Steps

1. **Run deployment verification script**
2. **Check Cloud Run console for latest revision**
3. **Force new deployment if needed**
4. **Test with the verification commands**
5. **Confirm year mapping row is present**

The key is to ensure the deployment timestamp is **after** the CSV fix was implemented in the code.
