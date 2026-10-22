# PackGuard AI - Render Deployment Guide

This guide provides end-to-end instructions for deploying **PackGuard AI** on [Render](https://render.com/) as a production-ready Python web service.

---

## Architecture & Deployment Overview

PackGuard AI is configured natively for Render:
- **Runtime**: Native Python 3.10+ (managed via `runtime.txt` and `.python-version`)
- **Production Server**: Gunicorn with multi-threading (`gthread`) and a 120s worker timeout to accommodate high-resolution artwork vision checks and regulatory reasoning
- **Reverse Proxy Support**: Werkzeug `ProxyFix` middleware automatically handles Render's SSL/TLS termination and forwarded headers
- **Health Checks**: `/health` endpoint configured for automated uptime checks
- **Security**: Injected production HTTP security headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`)

---

## Option 1: Automatic 1-Click Deployment (Render Blueprint)

The repository includes a ready-to-use [`render.yaml`](file:///c:/Users/Aditya_Work/Desktop/esko/render.yaml) specification.

1. Push your repository to **GitHub** or **GitLab**.
2. Log in to [dashboard.render.com](https://dashboard.render.com/).
3. Click **New +** in the top navigation and select **Blueprint**.
4. Connect your GitHub repository containing PackGuard AI.
5. Render will automatically detect `render.yaml` and configure:
   - **Service Name**: `packguard-ai`
   - **Runtime**: `Python`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `python -m gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   - **Health Check Path**: `/health`
6. Under **Environment Variables**, provide your `GEMINI_API_KEY`:
   - `GEMINI_API_KEY`: Your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)
7. Click **Apply**. Render will provision and launch your service!

---

## Option 2: Manual Deployment via Render Dashboard

If you prefer setting up the web service manually:

### Step 1: Create a New Web Service
1. In the [Render Dashboard](https://dashboard.render.com/), click **New +** -> **Web Service**.
2. Choose **Build and deploy from a Git repository** and click **Next**.
3. Select your repository and click **Connect**.

### Step 2: Configure Service Settings
Fill in the following fields:

| Field | Recommended Value |
|---|---|
| **Name** | `packguard-ai` |
| **Region** | Choose nearest (e.g., `Oregon (US West)` or `Frankfurt (EU)`) |
| **Branch** | `main` |
| **Root Directory** | *(Leave blank / project root)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install --upgrade pip && pip install -r requirements.txt` |
| **Start Command** | `python -m gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120` |
| **Instance Type** | `Free` or `Starter` |

> [!IMPORTANT]
> Always include `--timeout 120` in the start command. Artwork PDF rendering and multimodal Gemini vision processing can take 15–30 seconds. The default Gunicorn timeout (30s) may kill active requests prematurely.

### Step 3: Add Environment Variables
Scroll down to the **Environment Variables** section and add:

| Key | Value | Notes |
|---|---|---|
| `GEMINI_API_KEY` | `your_actual_api_key_here` | From [Google AI Studio](https://aistudio.google.com/) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Default model |
| `PYTHON_VERSION` | `3.10.11` | Ensures matching Python environment |
| `FLASK_DEBUG` | `false` | Production mode |
| `WEB_CONCURRENCY` | `2` | Number of Gunicorn worker processes |
| `GUNICORN_THREADS` | `4` | Threads per worker for handling concurrent uploads |
| `GUNICORN_TIMEOUT` | `120` | Request timeout in seconds |

### Step 4: Configure Health Check Path
1. Under **Advanced Settings**, find **Health Check Path**.
2. Set the path to: `/health`
3. Render will poll this endpoint to verify zero-downtime deploys.

### Step 5: Deploy
Click **Create Web Service**. Render will clone your repository, install dependencies, run health checks, and allocate an HTTPS URL (e.g. `https://packguard-ai.onrender.com`).

---

## Verifying Deployment

Once deployed, verify your live service:

1. **Health Check**:
   ```bash
   curl -i https://your-service-name.onrender.com/health
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "app_name": "PackGuard AI",
     "version": "1.0.0",
     "gemini_configured": true
   }
   ```

2. **System Status**:
   ```bash
   curl https://your-service-name.onrender.com/api/status
   ```

3. **Web Dashboard**:
   Open `https://your-service-name.onrender.com` in your browser. Select any test preset (e.g. *Dancing Fish Granola*) and click **Run Compliance Audit** to confirm full end-to-end functionality.

---

## Important Production Considerations

### 1. Free Tier Sleeping & Cold Starts
On Render's Free tier, services spin down after 15 minutes of inactivity. The first request after spinning down may take 30–50 seconds to boot. For mission-critical production usage, upgrading to Render's **Starter** plan (\$7/mo) guarantees 24/7 continuous uptime.

### 2. File Upload Limits
PackGuard AI is configured with a 32MB upload limit (`MAX_CONTENT_LENGTH = 32 * 1024 * 1024`) which comfortably accommodates multi-page PDF dielines and ultra-high-resolution packaging proofs.

### 3. Graceful Fallback
If the Gemini API key is omitted, exhausted, or experiences temporary rate limiting (HTTP 503 spikes), PackGuard AI automatically falls back to its deterministic Python validation engine (checking mandatory identity, dual-unit net weight, FALCPA allergen declarations, and UPC barcodes) so users never experience complete outages.
