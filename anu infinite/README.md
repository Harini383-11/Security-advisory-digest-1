# Security Advisory Digest

A comprehensive, AI-powered security vulnerability management system combining real-time advisory ingestion, vector-based semantic search, and intelligent risk assessment.

## 🎯 Project Overview

Security Advisory Digest is a production-ready vulnerability management platform that:

- **Ingests** security advisories from CISA KEV and NVD API
- **Deduplicates** CVEs and manages advisory data using SQLite
- **Searches** using ChromaDB semantic search with embeddings
- **Matches** organizational inventory against vulnerabilities
- **Analyzes** using Ollama LLM for intelligent recommendations
- **Reports** with executive summaries and risk assessments

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                       │
│  Home │ Search │ Inventory │ AI Assistant │ Risk Report     │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼────┐      ┌─────▼──────┐    ┌─────▼─────┐
    │SQLite  │      │ChromaDB    │    │Ollama LLM │
    │Database│      │Vector DB   │    │(llama3)   │
    └────────┘      └────────────┘    └───────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
    ┌──────────────────────▼───────────────────┐
    │          Core Modules                     │
    ├──────────────────────────────────────────┤
    │• Feed Ingestion (ingest.py)              │
    │• Deduplication (dedup.py)                │
    │• Inventory Matching (inventory_match.py) │
    │• RAG Engine (rag.py)                     │
    │• Agent Loop (agent.py)                   │
    └──────────────────────────────────────────┘
```

## 📋 Quick Start

### Prerequisites

- Python 3.9+
- Ollama with llama3 model installed
- SQLite (included with Python)

### Setup

1. **Clone and setup environment:**

```bash
cd "c:\Users\ADMIN\anu infinite"
python -m venv venv
venv\Scripts\activate

# Windows
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
# Copy example config
copy .env.example .env

# Edit .env with your settings (optional, defaults work for local testing)
```

3. **Ensure Ollama is running:**

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull llama3 model if needed
ollama pull llama3
```

4. **Run Streamlit dashboard:**

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 🚀 Usage Guide

### Home Dashboard

- **Total Advisories**: See all tracked vulnerabilities
- **Severity Distribution**: Visual breakdown by severity
- **Critical Advisories**: Latest high-priority CVEs
- **Inventory Overview**: Items at risk and vulnerability counts

### Advisory Search

**Semantic Search**: Ask natural language questions about advisories
- "What Linux vulnerabilities are critical?"
- "Show me all Apache exploits"
- "Recent database vulnerabilities"

**CVE ID Search**: Look up specific CVEs

**Product Search**: Find all vulnerabilities affecting a product

**Severity Filter**: View advisories by severity level

### Inventory Upload

1. Create CSV file with columns: `Product,Version`
2. Upload CSV file
3. Click "Match to Advisories" to find vulnerabilities
4. View risk report for each item

Sample CSV:
```csv
Product,Version
Windows Server,2019
Apache Tomcat,9
OpenSSL,1.1
```

### AI Assistant

Ask natural language questions:
- "What's the risk to our Windows Server 2019 installation?"
- "Show me critical Apache vulnerabilities"
- "What should we patch first?"

The agent will:
1. Retrieve relevant advisories
2. Check your inventory
3. Generate an answer
4. Score confidence level

### Risk Report

- **Inventory Risk**: Vulnerabilities per inventory item
- **Executive Summary**: Database statistics and top risks
- **Affected Products**: Priority patching list
- **Recommendations**: Actionable next steps

## 📁 Project Structure

```
anu infinite/
├── app.py                          # Main Streamlit app
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
│
├── config/
│   └── settings.py                 # Configuration management
│
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   └── database.py             # SQLite operations
│   │
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── ingest.py               # Feed ingestion
│   │   ├── dedup.py                # Deduplication engine
│   │   ├── inventory_match.py       # Inventory matching
│   │   ├── rag.py                  # ChromaDB RAG
│   │   ├── llm_service.py           # Ollama integration
│   │   ├── agent.py                # AI agent loop
│   │   └── summary_generator.py     # Report generation
│   │
│   └── utils/
│       └── __init__.py
│
├── tests/
│   ├── __init__.py
│   └── test_all.py                 # Pytest test suite
│
└── data/
    ├── advisory.db                 # SQLite database (auto-created)
    ├── chroma_db/                  # Vector database (auto-created)
    └── sample_inventory/
        └── sample.csv              # Sample CSV
```

## 🔧 Configuration

Edit `.env` file to customize:

```env
# Database
DATABASE_PATH=data/advisory.db
VECTOR_DB_PATH=data/chroma_db

# APIs
CISA_KEV_API_URL=https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
NVD_API_KEY=YOUR_API_KEY_HERE

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

## 📊 Database Schema

### advisories table
```sql
- id (PK)
- advisory_id (UNIQUE)
- cve_id (INDEXED)
- title
- description
- severity
- vendor (INDEXED)
- product (INDEXED)
- version
- published_date (INDEXED)
- source_feed
- url
- created_at, updated_at
```

### inventory table
```sql
- id (PK)
- product
- version
- quantity
- created_at
```

### inventory_matches table
```sql
- id (PK)
- inventory_id (FK)
- advisory_id (FK)
- cve_id
- severity
- created_at
```

## 🤖 AI Features

### Ollama LLM Functions

- **Summarize Advisory**: 2-3 sentence technical summary
- **Summarize Batch**: Executive summary of multiple advisories
- **Answer Query**: Context-aware answers about advisories
- **Generate Risk Report**: Detailed recommendations for inventory
- **Categorize Vulnerability**: Attack type and impact classification
- **Patch Recommendations**: Prioritized patching guidance

### Agent Loop

1. **Retrieve**: Search vector DB for relevant advisories
2. **Check Inventory**: Match query to inventory items
3. **Generate**: Create answer using LLM
4. **Score**: Confidence evaluation
5. **Iterate**: If confidence low, retrieve more context

## 🧪 Testing

Run the pytest test suite:

```bash
pytest tests/test_all.py -v

# Run specific test class
pytest tests/test_all.py::TestDatabase -v

# Run with coverage
pytest tests/test_all.py --cov=src
```

## 📈 Sample Workflow

### Scenario: New vulnerability discovered

1. **Ingest**: Click "Ingest Advisories" in sidebar
   - Fetches latest from CISA KEV and NVD
   - Automatically deduplicates

2. **Inventory Check**: Go to "Inventory Upload"
   - If not done, upload CSV of your systems

3. **Risk Assessment**: Click "Match to Advisories"
   - Finds all affecting items

4. **Risk Report**: View "Risk Report" page
   - See affected products
   - Get prioritized patching list

5. **Ask AI**: Use "AI Assistant"
   - "What should we patch first?"
   - Agent retrieves context and suggests actions

## 🔒 Security Considerations

- **Database**: Local SQLite, no remote access by default
- **Vector DB**: Local ChromaDB, embedded in data folder
- **API Keys**: Store NVD_API_KEY in `.env` (never commit)
- **LLM**: Local Ollama, no data sent to external services
- **Inventory**: Stored locally, not shared externally

## 📝 Logging

Logs are written to `logs/advisory_digest.log`:

```python
from loguru import logger

logger.info("Information messages")
logger.warning("Warning messages")
logger.error("Error messages")
logger.debug("Debug messages")
```

## 🚨 Limitations

1. **Ollama Required**: System requires local Ollama installation
2. **No Authentication**: Dashboard has no built-in auth (add reverse proxy)
3. **No Data Sync**: Runs offline, doesn't sync across instances
4. **API Rate Limits**: NVD API has rate limits (2000 req/24h without key)
5. **Embedding Context**: ChromaDB searches limited to indexed content

## 🚀 Future Improvements

- [ ] Multi-user support with role-based access control
- [ ] Real-time feed streaming updates
- [ ] Automated patch deployment integration
- [ ] Machine learning for vulnerability prediction
- [ ] Compliance reporting (NIST, PCI-DSS)
- [ ] Integration with ticketing systems (Jira, ServiceNow)
- [ ] Email alert notifications
- [ ] Mobile app for on-the-go risk checks
- [ ] Custom threat feeds integration
- [ ] Dashboard export to PDF/Excel

## 📚 Data Sources

- **CISA Known Exploited Vulnerabilities (KEV)**: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- **NVD CVE API**: https://nvd.nist.gov/products/cpe/about
- **Ollama Models**: https://ollama.ai

## 🔗 Dependencies

- `streamlit`: Web dashboard
- `chromadb`: Vector database
- `ollama`: LLM integration
- `pandas`: Data manipulation
- `plotly`: Visualization
- `requests`: HTTP client
- `python-dotenv`: Environment configuration
- `loguru`: Logging
- `pytest`: Testing framework

## 📄 License

This project is provided as-is for hackathon and educational purposes.

## 👥 Contributing

Contributions welcome! Areas for improvement:

- Additional data source integrations
- Advanced filtering and reporting
- Performance optimizations
- Extended test coverage
- Documentation improvements

## ❓ Troubleshooting

### Ollama connection error

```
Error: Could not connect to Ollama at http://localhost:11434
Solution: Ensure Ollama is running: ollama serve
```

### Database locked error

```
Error: database is locked
Solution: Close other connections or restart the app
```

### Vector DB not updating

```
Solution: Click "Update Vector DB" in sidebar to sync
```

### Slow queries

```
Solution: 
1. Ensure indexes are created (automatic on first run)
2. Limit query results with TOP N
3. Add more RAM if system is constrained
```

## 📞 Support

For issues, questions, or suggestions:
1. Check this README
2. Review test cases for usage examples
3. Check Ollama and ChromaDB documentation
4. Review logs in `logs/advisory_digest.log`

---

**Built with ❤️ for security teams**

Happy vulnerability hunting! 🛡️
