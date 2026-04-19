# Concrete Defect AI

AI-powered concrete pathology analysis. Upload a photo, get an 8-section engineering report, an annotated defect map, and a PDF export — all in under 60 seconds.

## Stack

- **Backend**: FastAPI + Anthropic Claude API
- **Image annotation**: Pillow (server-side)
- **PDF generation**: ReportLab
- **Frontend**: Vanilla HTML/CSS/JS (single-page app)

## Setup

### 1. Clone / navigate to the project

```bash
cd concrete-defect-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-opus-4-7
APP_NAME=Concrete Defect AI
MAX_IMAGE_SIZE_MB=10
```

Get an API key at https://console.anthropic.com/

### 5. Run the app

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Landing page + analyzer |
| POST | `/api/analyze` | Generate 8-section engineering report |
| POST | `/api/annotate` | Generate crack annotations + annotated image |
| POST | `/api/export-pdf` | Generate PDF report |
| GET | `/api/docs` | Interactive API documentation |

## Project Structure

```
concrete-defect-ai/
├── app/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Pydantic settings (.env)
│   ├── routes/
│   │   ├── analyze.py        # POST /api/analyze
│   │   ├── annotate.py       # POST /api/annotate
│   │   └── pdf.py            # POST /api/export-pdf
│   └── services/
│       ├── claude.py         # Anthropic API client
│       ├── imaging.py        # Pillow image annotation
│       └── pdf_gen.py        # ReportLab PDF generation
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── index.html            # Full SPA
├── .env.example
├── requirements.txt
└── README.md
```

## Disclaimer

This tool provides AI-assisted preliminary visual assessments only. It does not replace a comprehensive on-site inspection by a licensed Professional Engineer. Reports have no legal or contractual standing.
