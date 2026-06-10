# Security Advisory Digest

A production-grade Python system for automatically ingesting, analyzing, and matching security advisories against organizational software inventory using AI-powered insights.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Running the System](#running-the-system)
9. [API Usage](#api-usage)
10. [Database Schema](#database-schema)
11. [Assumptions](#assumptions)
12. [Limitations](#limitations)
13. [Future Improvements](#future-improvements)
14. [Troubleshooting](#troubleshooting)

---

## Project Overview

**Security Advisory Digest** is an enterprise-grade solution for security teams overwhelmed with daily security advisories. The system:

1. **Automatically ingests** security advisories from multiple RSS feeds
2. **Identifies vulnerable assets** by matching advisories against your software inventory
3. **Generates AI summaries** using Ollama's llama3 model for executive insights
4. **Produces actionable reports** with remediation guidance
5. **Exposes REST APIs** for integration with existing security tools

### Problem Statement

Security teams receive 100+ advisories daily, making manual triage impossible. This system automates the matching process and prioritizes threats based on your actual inventory.

### Solution Highlights

- ✅ Automatic RSS feed ingestion from GitHub and CISA
- ✅ Inventory-based advisory matching
- ✅ AI-powered executive summaries and remediation advice
- ✅ SQLite persistence with efficient querying
- ✅ REST API for programmatic access
- ✅ Comprehensive logging for audit trails
- ✅ Production-ready error handling
- ✅ Full test coverage (happy path)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  Endpoints: /health, /advisories, /matches, /report, /scan   │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼────┐                  ┌──────▼──────┐
    │  Agent  │                  │  Database   │
    └────┬────┘                  │  (SQLite)   │
         │                       │             │
         │                       │ advisories  │
    ┌────▼─────────┬──────────┬──▼─────────┐ │
    │              │          │            │ │
    │  Ingestion   │ Inventory│  Matches   │ │
    ├──────────────┤ Matching │            │ │
    │              │          │            │ │
    │ • RSS Feed   │ • Loader │ • Storage  │ │
    │ • JSON Feed  │ • Matcher│ • Querying │ │
    │              │          │            │ │
    └──────────────┴──────────┴────────────┘ │
                                             │
    ┌────────────────────────────────────────▼─────┐
    │  LLM Service (Ollama + llama3)               │
    ├──────────────────────────────────────────────┤
    │ • Executive Summaries                        │
    │ • Business Impact Analysis                   │
    │ • Remediation Advice                         │
    └──────────────────────────────────────────────┘

    ┌────────────────────────────────────────────┐
    │  Report Generator                          │
    ├────────────────────────────────────────────┤
    │ • JSON Reports                             │
    │ • Console Output                           │
    │ • Trend Analysis                           │
    └────────────────────────────────────────────┘
```

---

## Features

### Core Features

- **🔍 Advisory Ingestion**
  - RSS feed parsing from GitHub and CISA
  - JSON feed support for custom sources
  - Automatic deduplication
  - Feed retry logic

- **🎯 Inventory Matching**
  - Product name matching (exact and fuzzy)
  - Vendor name matching
  - Similarity-based matching (60%+ threshold)
  - Version-aware matching

- **🤖 AI-Powered Analysis**
  - Executive summaries (C-level friendly)
  - Business impact assessment
  - Remediation step generation
  - Customizable prompts

- **📊 Reporting**
  - JSON report export
  - Risk level calculation
  - Aggregate statistics
  - Console-friendly formatting

- **🔌 REST API**
  - Health checks
  - Advisory listing
  - Match queries
  - On-demand scanning
  - Real-time reporting

- **💾 Data Persistence**
  - SQLite database with optimized indices
  - Relationship tracking
  - Historical data retention

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | 3.11+ |
| **Web Framework** | FastAPI | 0.109.0 |
| **Server** | Uvicorn | 0.27.0 |
| **Database** | SQLite3 | Bundled |
| **LLM** | Ollama + llama3 | Local |
| **Data Validation** | Pydantic | 2.5.3 |
| **Feed Parsing** | feedparser | 6.0.10 |
| **HTTP Client** | requests | 2.31.0 |
| **Testing** | pytest | 7.4.4 |
| **Logging** | Python logging | Builtin |

---

## Project Structure

```
security_advisory_digest/
├── app.py                          # FastAPI application
├── config.py                       # Configuration management
├── models.py                       # Pydantic data models
├── agent.py                        # Main orchestration agent
│
├── ingestion/                      # Advisory ingestion
│   ├── __init__.py
│   ├── rss.py                     # RSS feed parser
│   └── json_feed.py               # JSON feed parser
│
├── inventory/                      # Inventory management
│   ├── __init__.py
│   ├── matcher.py                 # Matching algorithm
│   └── inventory_match.py         # Service layer
│
├── llm/                           # LLM integration
│   ├── __init__.py
│   ├── ollama.py                  # Ollama client
│   └── llm_service.py             # LLM service
│
├── db/                            # Database operations
│   ├── __init__.py
│   └── sqlite.py                  # SQLite interface
│
├── vector/                        # Vector embeddings
│   ├── __init__.py
│   └── embeddings.py              # Placeholder
│
├── reports/                       # Report generation
│   ├── __init__.py
│   └── report_generator.py        # Report builder
│
├── tests/                         # Test suite
│   ├── test_agent.py              # Agent tests
│   ├── test_ingestion.py          # Ingestion tests
│   ├── test_inventory_match.py    # Matching tests
│   ├── test_database.py           # Database tests
│   └── test_llm.py                # LLM tests
│
├── data/                          # Data files
│   ├── inventory.csv              # Sample inventory
│   ├── advisories.db              # SQLite database
│   └── report.json                # Latest report
│
├── requirements.txt               # Python dependencies
├── prompts.md                     # LLM prompts documentation
└── README.md                      # This file
```

---

## Installation

### Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/)
- **Ollama** - [Download](https://ollama.ai/)
- **Git** (optional)

### Step 1: Clone or Download the Project

```bash
git clone https://github.com/your-org/security-advisory-digest.git
cd security_advisory_digest
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Ollama

```bash
# Install Ollama (if not already installed)
# Then pull the llama3 model
ollama pull llama3

# Verify installation
ollama list
```

### Step 5: Verify Installation

```bash
# Check Python packages
pip list

# Check Ollama
ollama --version
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=sqlite:///./data/advisories.db

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=120

# FastAPI Configuration
API_HOST=127.0.0.1
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Request Timeout
REQUEST_TIMEOUT=30
```

### Inventory File

Edit `data/inventory.csv` to match your organization's software:

```csv
software_name,version
Apache,2.4
Nginx,1.22
OpenSSL,3.0
MySQL,8
```

### RSS Feeds

Modify `config.py` to add/remove RSS feeds:

```python
RSS_FEEDS = [
    "https://github.blog/security/feed/",
    "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "https://your-custom-feed.com/rss"  # Add custom feeds
]
```

---

## Running the System

### Option 1: Run FastAPI Server

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Option 2: Run Agent Directly

```bash
python agent.py
```

### Option 3: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_ingestion.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

---

## API Usage

### 1. Health Check

```bash
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000",
  "ollama_available": true,
  "database_available": true
}
```

### 2. List Advisories

```bash
curl http://localhost:8000/advisories?limit=10

# Response
{
  "total": 10,
  "advisories": [
    {
      "id": 1,
      "advisory_id": "github_001",
      "title": "Critical Vulnerability",
      "severity": "CRITICAL",
      "vendor": "Apache",
      "product": "Apache HTTP Server",
      "published_date": "2024-01-15T10:00:00",
      "url": "https://..."
    }
  ]
}
```

### 3. List Matches

```bash
curl http://localhost:8000/matches

# Response
{
  "total_matches": 5,
  "matches": [
    {
      "match_id": 1,
      "advisory": {
        "id": 1,
        "advisory_id": "github_001",
        "title": "Critical Vulnerability",
        "severity": "CRITICAL",
        "product": "Apache HTTP Server"
      },
      "inventory_item": {
        "asset_id": "app_001",
        "software_name": "Apache",
        "version": "2.4"
      },
      "risk_level": "CRITICAL",
      "created_at": "2024-01-15T11:00:00"
    }
  ]
}
```

### 4. Get Report

```bash
curl http://localhost:8000/report

# Response
{
  "status": "success",
  "report": {
    "scan_time": "2024-01-15T11:30:00",
    "total_advisories": 150,
    "matched_count": 5,
    "matches": [...],
    "executive_summary": "..."
  }
}
```

### 5. Run Scan (POST)

```bash
curl -X POST http://localhost:8000/scan

# Optional: Force refresh
curl -X POST "http://localhost:8000/scan?force_refresh=true"

# Response
{
  "status": "success",
  "message": "Scan completed successfully",
  "report": {
    "scan_time": "2024-01-15T12:00:00",
    "total_advisories": 150,
    "matched_count": 5,
    "matches": [...]
  }
}
```

---

## Database Schema

### advisories Table

```sql
CREATE TABLE advisories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    advisory_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    vendor TEXT NOT NULL,
    product TEXT NOT NULL,
    published_date TIMESTAMP NOT NULL,
    source_feed TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### inventory_items Table

```sql
CREATE TABLE inventory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT UNIQUE NOT NULL,
    software_name TEXT NOT NULL,
    version TEXT NOT NULL
);
```

### matches Table

```sql
CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    advisory_id INTEGER NOT NULL,
    inventory_item_id INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (advisory_id) REFERENCES advisories(id),
    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id),
    UNIQUE(advisory_id, inventory_item_id)
);
```

---

## Assumptions

1. **Ollama Availability**: System assumes Ollama is running locally on port 11434
2. **llama3 Model**: Assumes llama3 model is pulled and available
3. **CSV Format**: Inventory must be valid CSV with `software_name` and `version` columns
4. **Network Access**: RSS feeds are publicly accessible
5. **Advisory Format**: Advisories follow standard RSS/Atom format
6. **Vendor Names**: Vendor/product extraction uses heuristics (not ML)
7. **Matching Threshold**: 60% similarity for fuzzy matching
8. **Single Inventory**: System handles one inventory file
9. **No Authentication**: API endpoints have no built-in authentication
10. **Local Execution**: System designed for single-machine deployment

---

## Limitations

### Current Limitations

1. **Feed Parsing**
   - Only RSS and JSON feed formats supported
   - HTML feeds not supported
   - Some malformed feeds may fail

2. **Matching**
   - Fuzzy matching uses simple string similarity
   - No ML-based matching
   - Vendor extraction is rule-based (not ML)
   - No version range matching (exact versions only)

3. **LLM Integration**
   - Only local Ollama supported (no cloud APIs)
   - Limited to first 5 advisories per scan for summaries
   - No caching of summaries
   - Slow response times (10-30s per advisory)

4. **Database**
   - SQLite only (no PostgreSQL/MySQL)
   - Single-file database (not distributed)
   - No full-text search indices

5. **API**
   - No authentication/authorization
   - No rate limiting
   - No caching headers
   - Synchronous endpoints (long scans block)

6. **Reporting**
   - Basic JSON format only
   - No PDF export
   - No email notifications
   - Limited visualization

---

## Future Improvements

### High Priority

1. **Advanced Matching**
   - ML-based product name extraction
   - CVSS score integration
   - Version range matching (e.g., "2.4.0-2.4.50")
   - NLP-based vulnerability categorization

2. **Performance**
   - Async API endpoints
   - Background job queues (Celery)
   - Caching layer (Redis)
   - Batch processing

3. **LLM Enhancement**
   - Summary caching to avoid regeneration
   - Cloud LLM support (OpenAI, Anthropic)
   - Custom model fine-tuning
   - Multi-model fallback

### Medium Priority

4. **Database**
   - PostgreSQL support
   - Full-text search indices
   - Time-series analysis
   - Historical trend reporting

5. **API**
   - OAuth2 authentication
   - Rate limiting
   - API key management
   - Webhook support for notifications

6. **Integration**
   - Slack/Teams notifications
   - JIRA ticket creation
   - ServiceNow integration
   - SIEM integration (Splunk, ELK)

### Low Priority

7. **Advanced Analytics**
   - Vulnerability trending
   - Risk scoring algorithm
   - Predictive patching recommendations
   - Compliance dashboard

8. **UI/UX**
   - Web dashboard
   - Real-time monitoring
   - Custom report builder
   - Data visualization

---

## Troubleshooting

### Issue: Ollama Connection Refused

**Problem**: `Error connecting to Ollama: Connection refused`

**Solution**:
```bash
# Check if Ollama is running
ollama serve

# Check if llama3 model is pulled
ollama list

# Verify connectivity
curl http://localhost:11434/api/tags
```

### Issue: No Advisories Found

**Problem**: Scan completes but returns 0 advisories

**Solution**:
```bash
# Check RSS feeds are accessible
curl https://github.blog/security/feed/

# Verify feed parsing
python -c "import feedparser; feed = feedparser.parse('https://github.blog/security/feed/'); print(len(feed.entries))"

# Check network connectivity
ping github.com
```

### Issue: No Inventory Matches

**Problem**: Advisories found but no matches

**Solution**:
```bash
# Verify inventory file exists
cat data/inventory.csv

# Check advisory product names
# Edit data/inventory.csv to include matching software names

# Increase similarity threshold
# Modify inventory/matcher.py: self.similarity_threshold = 0.5
```

### Issue: Database Locked

**Problem**: `Database is locked` error

**Solution**:
```bash
# Ensure only one process accessing database
ps aux | grep python

# Remove any stuck processes
kill -9 <PID>

# Delete corrupted database
rm data/advisories.db

# Recreate database (automatic on startup)
```

### Issue: Tests Failing

**Problem**: Pytest tests fail with import errors

**Solution**:
```bash
# Reinstall in development mode
pip install -e .

# Or add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run tests from project root
cd /path/to/security_advisory_digest
pytest tests/
```

### Issue: Slow Performance

**Problem**: Scan takes 5+ minutes

**Solution**:
```bash
# Check Ollama resource usage
ollama list

# Reduce advisory processing
# Modify agent.py: advisories = advisories[:10]  # Limit to 10

# Use faster model
ollama pull neural-chat  # Lighter model
# Update config.py: OLLAMA_MODEL = "neural-chat"

# Disable AI summaries
# Modify agent.py: skip _step_5_generate_summaries()
```

---

## Support & Contributing

For issues, questions, or contributions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `tail -f logs/advisory_digest.log`
3. Open a GitHub issue with:
   - Error message
   - Python version
   - Ollama version
   - Steps to reproduce

---

## License

[Your License Here]

---

## Authors

- **Security Team** - Initial implementation

---

## Changelog

### v1.0.0 - January 2024
- Initial release
- RSS/JSON feed ingestion
- Inventory matching
- Ollama integration
- FastAPI server
- SQLite persistence
- Comprehensive test suite
