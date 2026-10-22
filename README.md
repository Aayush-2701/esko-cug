# PackGuard AI
### Intelligent Packaging Artwork Pre-Flight & Regulatory Checker

PackGuard AI is a focused, high-precision packaging artwork verification application built with Flask, Vanilla JavaScript, HTML5, CSS3, and Google Gemini 2.5 Flash.

It inspects packaging dielines, labels, and cartons against master brand rulebooks, specification content sheets, and FDA/FSSAI labeling regulations using dual-layer verification: deterministic Python rules combined with multimodal Gemini vision.

---

## Key Features

1. Two-Stage AI & Dual-Engine Verification Architecture:
   - Stage 1 (Vision Inspector): Specifically inspects high-resolution artwork image renders to identify packaging panels (PDP vs Info panel), detect certification logos/badges (USDA Organic, Certified Vegan, How2Recycle), evaluate barcode quiet zones, and spot dieline safety boundaries.
   - Stage 2 (Text Regulatory Reasoning Engine): Combines the Stage 1 visual audit report with extracted vector text, the master rulebook, and deterministic checks to perform deep regulatory reconciliation (FDA 21 CFR, FALCPA, Metrology, GS1).
   - Deterministic Python Engine (validator.py): Instant mathematical and statutory checks for required fields, exact brand names, dual net quantity requirements (Metric + US Customary ounces under FDA 21 CFR § 101.105), allergen disclosure rules (FALCPA tree nuts), and UPC barcodes.
2. Clear Discrepancy Categorization:
   - Distinguishes Confirmed Discrepancies (direct specification violations or statutory errors) from Needs Review / Ambiguous findings (aesthetic suggestions, formulation verification).
   - Severity tags: CRITICAL, HIGH, MEDIUM, LOW, and INFO / PASSED.
3. Comprehensive Artwork & Rulebook Support:
   - Artwork: PNG, JPG/JPEG, PDF (renders dielines at 150 DPI and extracts vector text layers).
   - Rulebooks: JSON, TXT, PDF, and Excel Content Sheets (.xlsx).
4. Interactive Regulatory Follow-Up Assistant:
   - Ask clarifying follow-up questions directly on the findings (e.g., "Why is the 480g net weight flagged?", "How should the allergen statement be formatted for US FDA?").
5. Zero Frontend Frameworks:
   - Pure HTML5, modern CSS3, and vanilla ES6 JavaScript. No React, Next.js, Node.js, or bundlers required.
6. Multi-Category Test Datasets Included:
   - One-click testing presets across multiple packaging formats (cereals, confectionery wrappers, RTD beverage cans, spouted baby food pouches).
   - Realistic vector artwork proofs (.pdf and 150 DPI .png) and multi-format rulebooks (.json, .txt, .xlsx).

---

## Project Structure

```text
esko/
|-- app.py                      # Flask server, API routes, and file handlers
|-- analyzer.py                 # Gemini API integration, multimodal analysis, and document extraction
|-- validator.py                # Deterministic rule checks (mandatory fields, net quantity, allergens, UPC)
|-- templates/
|   `-- index.html              # Responsive single-page dashboard
|-- static/
|   |-- style.css               # Clean minimal responsive styling (solid colors, white theme)
|   `-- script.js               # File dropzones, API communications, and dynamic findings renderer
|-- sample_data/
|   |-- sample_rulebook.json    # Master rulebook specification
|   `-- sample_rulebook.txt     # Plain-text packaging guidelines
|-- requirements.txt            # Python dependencies
|-- .env.example                # Template for environment configuration
`-- README.md                   # Setup and usage guide
```

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- (Optional for live Gemini) A Google Gemini API key from Google AI Studio.
  Note: If no API key is provided, PackGuard AI runs with its deterministic validation engine and built-in packaging intelligence.

### 2. Installation

1. Navigate to the project directory:
   ```bash
   cd c:\Users\Aditya_Work\Desktop\esko
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Environment Configuration

Copy the .env.example file to .env:
```bash
copy .env.example .env
```

Open .env and set your GEMINI_API_KEY:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
FLASK_PORT=5000
FLASK_DEBUG=false
```

### 4. Run the Application Locally

Start the Flask server:
```bash
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## Deploy to Render (Production)

PackGuard AI is fully optimized for 1-click cloud deployment on [Render](https://render.com/).

### Quick Deploy via Render Blueprint:
1. Push this repository to GitHub or GitLab.
2. In the Render Dashboard, select **New +** -> **Blueprint**.
3. Select your repository. Render automatically reads [`render.yaml`](render.yaml) to configure:
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `python -m gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   - **Health Check Path**: `/health`
4. Set your `GEMINI_API_KEY` in Render's environment settings and click **Apply**.

For complete manual setup instructions and production considerations, refer to [**DEPLOYMENT.md**](DEPLOYMENT.md).

---

## Testing the Workflow

### Method A: One-Click Instant Test (Recommended)
1. Click the "Load Sample Files" button in the top navigation bar.
2. The application will immediately populate the sample artwork dieline and the master specification.
3. Click "Analyze Artwork" to run the complete dual-engine inspection.
4. Review the dynamically generated findings, filter by severity, and type questions in the follow-up box.

### Method B: Upload Your Own Files
1. Drop Packaging Artwork: Upload any label or dieline (PDF, PNG, JPG).
2. Drop Rulebook: Upload your brand specification or regulatory requirements (JSON, TXT, PDF).
3. Click "Analyze Artwork" to view real-time compliance readiness scores, detailed comparisons, and recommendations.

---

## Regulatory & Quality Assurance Disclaimer

PackGuard AI is an automated packaging verification assistant designed to support human packaging engineers, graphic production artists, and regulatory reviewers. It does not constitute certified legal counsel, formal regulatory compliance advice, or statutory agency approval. Always obtain certified pre-press sign-off before manufacturing plates.
