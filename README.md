# AI Research Assistant

A locally-deployable, RAG-powered web application for financial document Q&A. Select financial data sources (e.g., Wells Fargo quarterly earnings, annual reports), scrape and index documents, and ask questions via a chat interface with retrieval-augmented generation.

## Features

- **Multi-source document ingestion** — Scrape PDFs from financial data sources (Wells Fargo earnings, annual reports, etc.)
- **RAG-powered Q&A** — Ask natural language questions answered using retrieved document context
- **Source filtering** — Select which sources to query against
- **Citations** — Every answer includes citations with source documents, URLs, and relevant text snippets
- **Extensible scraper framework** — Add new data sources by implementing a simple base class
- **Dual LLM support** — Use OpenAI API or self-hosted Ollama models
- **Local vector storage** — ChromaDB for embeddings, SQLite for document metadata

## Prerequisites

- Python 3.11+
- An OpenAI API key **or** [Ollama](https://ollama.ai/) installed locally
- (Optional) Docker and Docker Compose for containerized deployment

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd ai-research-assistant
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key (or configure Ollama)
   ```

## Configuration

Edit `.env` to configure the application:

```env
# LLM Provider
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai          # or "ollama"
LLM_MODEL=gpt-4o-mini        # or "llama3" for Ollama

# For Ollama (uncomment):
# LLM_BASE_URL=http://localhost:11434/v1

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Storage paths
CHROMA_DB_PATH=./data/chroma_db
SQLITE_DB_PATH=./data/metadata.db
DOWNLOAD_PATH=./data/downloads
```

## Running the Application

### Backend (FastAPI)

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### Frontend (Streamlit)

In a separate terminal:

```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```

The UI will be available at `http://localhost:8501`.

### Seed Initial Data

To scrape and ingest documents from all configured sources:

```bash
python scripts/seed_data.py
```

To scrape a specific source:

```bash
python scripts/seed_data.py --source wf_earnings
```

## Running Tests

```bash
# Unit tests (fast, no external dependencies)
pytest -m unit

# Component tests (may use local resources like ChromaDB)
pytest -m component

# Integration tests
pytest -m integration

# End-to-end tests
pytest -m e2e

# Smoke tests (quick health checks)
pytest -m smoke

# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## API Endpoints

| Method | Endpoint                    | Description                          |
|--------|----------------------------|--------------------------------------|
| GET    | `/health`                  | Health check                         |
| GET    | `/api/sources`             | List all registered data sources     |
| POST   | `/api/query`               | Query documents using RAG            |
| POST   | `/api/admin/scrape`        | Trigger scraping for a source        |
| GET    | `/api/admin/store/stats`   | Vector store statistics              |
| GET    | `/api/admin/llm/status`    | Check LLM connectivity              |
| POST   | `/api/admin/scrape/dry-run`| Check if source URL is reachable     |

### Query Example

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Wells Fargo net income in Q4 2025?", "sources": ["wf_earnings"]}'
```

## Adding New Sources

1. Create a new scraper in `app/scrapers/`:

```python
from app.scrapers.base_scraper import BaseScraper, ScrapedDocument

class MyNewScraper(BaseScraper):
    name = "my_source"
    display_name = "My Data Source"
    base_url = "https://example.com/data"
    doc_type = "pdf"

    def scrape(self) -> list[ScrapedDocument]:
        # Implement scraping logic
        ...
```

2. Register it in `app/scrapers/registry.py`:

```python
from app.scrapers.my_source import MyNewScraper

def _build_registry():
    scrapers = [
        WFEarningsScraper(),
        WFAnnualReportsScraper(),
        MyNewScraper(),  # Add here
    ]
    return {s.name: s for s in scrapers}
```

3. The new source will automatically appear in the UI and API.

## Docker Deployment

```bash
docker-compose up --build
```

This starts both the backend (port 8000) and frontend (port 8501).

## Project Structure

```
ai-research-assistant/
├── app/                    # Application code
│   ├── api/                # FastAPI routes and dependencies
│   ├── scrapers/           # Data source scrapers
│   ├── processing/         # PDF parsing, chunking, embeddings
│   ├── storage/            # ChromaDB and SQLite wrappers
│   ├── rag/                # RAG pipeline
│   └── utils/              # Text and URL utilities
├── frontend/               # Streamlit UI
├── tests/                  # Test suite (unit, component, integration, e2e, smoke)
├── scripts/                # Utility scripts
└── data/                   # Local data (gitignored)
```

## License

MIT
