# Quick Start Guide - Security Advisory Digest

## ⚡ 5-Minute Setup

### Step 1: Install Ollama (5 min)
```bash
# Download from https://ollama.ai
# Or use package manager:

# macOS
brew install ollama

# Windows (download .exe from ollama.ai)
# Or use Chocolatey
choco install ollama

# Linux
curl https://ollama.ai/install.sh | sh
```

### Step 2: Pull llama3 Model
```bash
ollama pull llama3

# This downloads the model (takes 5-10 minutes)
# You can test with: ollama run llama3 "Hello"
```

### Step 3: Install Python Dependencies (3 min)
```bash
cd "c:\Users\ADMIN\anu infinite"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Run Application (1 min)
```bash
# Terminal 1: Keep Ollama running
ollama serve

# Terminal 2: Run Streamlit app
streamlit run app.py
```

App opens at: `http://localhost:8501`

---

## 🎯 First Actions

### 1. Ingest Advisories
1. Go to dashboard sidebar
2. Click "🔄 Ingest Advisories"
3. Wait for completion (1-5 minutes first time)

### 2. Update Vector Database
1. Click "📊 Update Vector DB"
2. Wait for vectors to be created

### 3. Upload Inventory
1. Go to "Inventory Upload" page
2. Download "Sample Inventory CSV"
3. Upload file
4. Click "Import Inventory"

### 4. Find Vulnerabilities
1. Go to "Inventory Upload"
2. Click "🔗 Match to Advisories"
3. View matches for each product

### 5. Use AI Assistant
1. Go to "AI Assistant" page
2. Ask: "What's the risk to Windows Server 2019?"
3. Get AI-powered answer

---

## 🔧 Environment Setup (Optional)

Create `.env` file for custom settings:

```bash
# Copy example
copy .env.example .env

# Edit .env (optional - defaults work)
# Only needed if:
# - Ollama on different host
# - Need NVD API key
# - Custom database location
```

---

## 📊 Dashboard Overview

| Page | Purpose | Key Action |
|------|---------|------------|
| Home | Overview dashboard | View stats & charts |
| Search | Find advisories | Search CVEs |
| Inventory | Manage assets | Upload CSV |
| AI Assistant | Ask questions | Natural language queries |
| Risk Report | View risks | See affected products |

---

## 🐛 Troubleshooting

### "Cannot connect to Ollama"
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Verify it's running
ollama list
```

### "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Database locked"
- Close Streamlit and restart
- Kill any Python processes
- Delete `data/advisory.db` to reset

### Slow response
- First run indexes the database (normal)
- Vector search creates embeddings (5-10 min)
- Check Task Manager for CPU usage

---

## 📈 Example Workflow

### Scenario: Patch Critical Vulnerabilities

1. **Dashboard** → "🔄 Ingest Advisories"
   - Downloads latest CVEs

2. **Risk Report** → See critical advisories
   - View what's affecting your inventory

3. **AI Assistant** → Ask "What should we patch first?"
   - Get prioritized recommendations

4. **Advisory Search** → Look up specific CVE
   - Get detailed information

5. **Risk Report** → Export report
   - Share with security team

---

## 🚀 Advanced Usage

### Custom Feed Ingestion
```python
from src.modules.ingest import FeedIngester
from src.core.database import AdvisoryDatabase

db = AdvisoryDatabase()
ingester = FeedIngester(db)

# Ingest from custom JSON feed
ingester.ingest_custom_feed(
    "https://your-feed.com/advisories.json",
    feed_type="json"
)
```

### Programmatic Queries
```python
from src.modules.agent import SecurityAgent

# Initialize components...
agent = SecurityAgent(db, rag, llm, matcher)

# Ask questions
response = agent.process_query("What products have critical CVEs?")
print(response["answer"])
print(f"Confidence: {response['confidence']}")
```

### Batch Testing
```bash
# Run test suite
pytest tests/test_all.py -v

# Run specific tests
pytest tests/test_all.py::TestDatabase::test_add_advisory -v
```

---

## 📋 System Requirements

- **OS**: Windows, macOS, Linux
- **Python**: 3.9+
- **Memory**: 4GB minimum (8GB recommended)
- **Disk**: 5GB for models + data
- **Network**: Internet for feed ingestion

---

## 🎓 Learning Resources

| Topic | File | Time |
|-------|------|------|
| Architecture | README.md | 15 min |
| Database | src/core/database.py | 20 min |
| RAG System | src/modules/rag.py | 15 min |
| Agent Loop | src/modules/agent.py | 20 min |
| Tests | tests/test_all.py | 30 min |

---

## 💡 Tips & Tricks

1. **Cache Clearing**: Streamlit caches resources
   ```bash
   streamlit cache clear
   ```

2. **Database Query**: Direct SQL access
   ```bash
   sqlite3 data/advisory.db
   SELECT * FROM advisories LIMIT 10;
   ```

3. **Model Selection**: Try different models
   ```bash
   ollama pull mistral
   # Edit OLLAMA_MODEL in .env
   ```

4. **Batch Operations**: Load 1000+ advisories quickly
   ```python
   advisories = db.get_all_advisories(limit=10000)
   rag.add_advisories_batch(advisories)
   ```

5. **Logging**: Check logs for debugging
   ```bash
   tail -f logs/advisory_digest.log
   ```

---

## 🆘 Getting Help

### Check Documentation
- README.md - Full documentation
- DEPLOYMENT_CHECKLIST.py - Verification script
- AI_USAGE_NOTE.md - Technical details
- tests/test_all.py - Usage examples

### Run Verification
```bash
python DEPLOYMENT_CHECKLIST.py
```

### View Logs
```bash
tail -f logs/advisory_digest.log
```

---

## ✅ Next Steps

1. ✓ Install Ollama
2. ✓ Setup Python environment
3. ✓ Run the app
4. ✓ Ingest advisories
5. ✓ Upload inventory
6. ✓ Explore dashboards
7. ✓ Try AI assistant
8. ✓ Generate reports

**You're now ready to start!** 🎉

---

For detailed information, see [README.md](README.md)
