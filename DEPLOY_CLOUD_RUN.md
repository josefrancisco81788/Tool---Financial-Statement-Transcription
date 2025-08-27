# Deploying the Financial Statement Transcription API to Google Cloud Run

This guide deploys the FastAPI service (`api/main.py`) as a container on Cloud Run.

## 1) Prerequisites
- Google Cloud project and billing enabled
- gcloud CLI installed and authenticated
- Permissions to use Cloud Build and Cloud Run
- OpenAI API key

## 2) Containerize the API
A Dockerfile is provided at the repo root. It:
- Installs `requirements-api.txt`
- Optionally installs `poppler-utils` (for `pdf2image`); PyMuPDF is also included as fallback
- Runs Uvicorn on `$PORT` (8080)

Build locally:
```bash
docker build -t fin-api:alpha1 .
```

Run locally:
```bash
docker run -p 8080:8080 -e OPENAI_API_KEY=sk-... fin-api:alpha1
# Then open http://localhost:8080/health
```

## 3) Build the image with Cloud Build
```bash
gcloud auth login
gcloud config set project <PROJECT_ID>

gcloud builds submit --tag gcr.io/<PROJECT_ID>/fin-api:alpha1
```

Artifacts can be stored in Artifact Registry as well (replace `gcr.io` with your registry path if needed).

## 4) Deploy to Cloud Run
```bash
gcloud run deploy fin-api \
  --image gcr.io/<PROJECT_ID>/fin-api:alpha1 \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --cpu 2 \
  --memory 4Gi \
  --timeout 60m \
  --concurrency 1 \
  --max-instances 2 \
  --set-env-vars OPENAI_API_KEY=YOUR_KEY
```

Notes:
- For non-POC, prefer Secret Manager instead of plain env var (see below).
- Adjust CPU/RAM for larger PDFs. Start with `--cpu=2 --memory=4Gi`.
- Keep `--concurrency` low (1–2) due to memory/CPU intensity.
- `--timeout` can be up to 60 minutes if long PDFs are expected.

## 5) Use Secret Manager (recommended)
Create a secret and grant access to Cloud Run's runtime service account.
```bash
echo -n "YOUR_KEY" | gcloud secrets create OPENAI_API_KEY --data-file=-
# Update service to use secret
gcloud run services update fin-api \
  --update-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest
```

## 6) Test the service
```bash
SERVICE_URL=$(gcloud run services describe fin-api --region us-central1 --format='value(status.url)')

curl "$SERVICE_URL/api/v1/health"

# Test a small PDF (replace file path)
curl -X POST "$SERVICE_URL/api/v1/extract-financial-data/sync" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_financial_statement.pdf" \
  -F "processing_approach=whole_document" \
  -F "output_format=csv"
```

## 7) Handling large files
Cloud Run's request body limit is ~32 MB. For larger PDFs:
- Upload the file to Google Cloud Storage using a signed URL
- Send the GCS URL to the API (add a URL parameter/field) and have the service fetch the file server-side

## 8) Optional: Put Cloudflare or API Gateway in front
- DNS/TLS/WAF and basic rate limiting via Cloudflare
- Or use GCP API Gateway for API keys/quotas and authentication

## 9) Observability
- Logs: Cloud Logging (stdout/stderr)
- Metrics: Cloud Monitoring; set alerts on latency/errors/memory

## 10) Cost tips
- Scale-to-zero saves cost when idle
- Use low `--max-instances` for POC; increase as needed
- Keep concurrency low for predictable resource usage

---

### Troubleshooting
- 403/401 on deploy: ensure Cloud Run and Cloud Build APIs are enabled, and your IAM role allows deploy
- 500 during processing: verify `OPENAI_API_KEY`, check logs for exceptions
- Timeouts: increase `--timeout`, reduce `--concurrency`, or offload to background processing
- Poppler missing: either keep `poppler-utils` in the Dockerfile, or rely on PyMuPDF code paths

### Repository files added
- `Dockerfile` — builds the API container for Cloud Run
- `.dockerignore` — reduces build context and avoids secret leakage
