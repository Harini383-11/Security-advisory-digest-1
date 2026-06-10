# Security Advisory Digest - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

✅ Python 3.11+  
✅ Ollama installed and running  
✅ llama3 model pulled  

## Step 1: Install Dependencies (2 minutes)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Prepare Ollama (1 minute)

```bash
# In a separate terminal, start Ollama
ollama serve

# In another terminal, pull llama3
ollama pull llama3

# Verify it's running
curl http://localhost:11434/api/tags
```

## Step 3: Verify Setup (1 minute)

```bash
# Run verification script
python setup_verify.py
```

You should see:
```
✓ PASS - Python Version
✓ PASS - Dependencies
✓ PASS - Ollama Service
✓ PASS - Inventory File
✓ PASS - Database
```

## Step 4: Start the Server (1 minute)

```bash
# Start FastAPI server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## Step 5: Test the API

Open in browser or terminal:

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
Open browser: `http://localhost:8000/docs`

### Run a Scan
```bash
curl -X POST http://localhost:8000/scan
```

### View Results
```bash
curl http://localhost:8000/matches
```

## Example API Calls

### 1. Get Health Status
```bash
curl -X GET http://localhost:8000/health | python -m json.tool
```

### 2. List Recent Advisories
```bash
curl -X GET "http://localhost:8000/advisories?limit=5" | python -m json.tool
```

### 3. Run Security Scan
```bash
curl -X POST http://localhost:8000/scan | python -m json.tool
```

### 4. Get Matches
```bash
curl -X GET http://localhost:8000/matches | python -m json.tool
```

### 5. Get Report
```bash
curl -X GET http://localhost:8000/report | python -m json.tool
```

## Common Tasks

### Add More Software to Inventory

Edit `data/inventory.csv`:
```csv
software_name,version
Apache,2.4
Nginx,1.22
PostgreSQL,15
YourApp,3.0
```

### Customize RSS Feeds

Edit `config.py`:
```python
RSS_FEEDS = [
    "https://your-feed.com/rss",
    "https://another-feed.com/feed.xml",
]
```

### Run Tests

```bash
pytest tests/ -v

# Or specific test
pytest tests/test_ingestion.py -v
```

### Check Logs

```bash
# View real-time logs
tail -f logs/advisory_digest.log

# Search logs
grep ERROR logs/advisory_digest.log
```

### Stop the Server

```bash
# Press Ctrl+C in the terminal

# Or kill the process
kill $(lsof -t -i:8000)
```

## Troubleshooting

### Ollama Not Running
```bash
# Start Ollama in separate terminal
ollama serve
```

### Port 8000 Already in Use
```bash
# Use different port
uvicorn app:app --port 8001
```

### Database Error
```bash
# Delete old database
rm data/advisories.db

# Restart server (it will recreate automatically)
```

### No Matches Found
```bash
# Update inventory.csv with software you have
# Software names must match advisory product names
```

### Tests Failing
```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run from project root
pytest tests/
```

## Next Steps

1. **Customize Inventory** - Update `data/inventory.csv` with your software
2. **Add Feeds** - Configure additional RSS feeds in `config.py`
3. **Integrate APIs** - Connect to your security tools via the REST API
4. **Deploy** - Follow deployment guide in README.md for production use
5. **Monitor** - Set up alerts for CRITICAL and HIGH severity matches

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/advisories` | List advisories |
| GET | `/matches` | List matches |
| GET | `/report` | Get latest report |
| POST | `/scan` | Run security scan |

## Need Help?

- 📖 See **README.md** for complete documentation
- 🔧 Check **Troubleshooting** section in README.md
- 📋 Review **prompts.md** for LLM configuration
- 🧪 Run **tests** to verify components
- 🔍 Check **logs** for error messages

## Demo Workflow

```bash
# 1. Start server
uvicorn app:app --reload

# 2. Check health
curl http://localhost:8000/health

# 3. Get current advisories
curl http://localhost:8000/advisories

# 4. Run full scan (wait 1-2 minutes)
curl -X POST http://localhost:8000/scan

# 5. View results
curl http://localhost:8000/matches
curl http://localhost:8000/report

# 6. View in browser
open http://localhost:8000/docs
```

## Performance Expectations

- **Feed Ingestion**: 30-60 seconds (depends on feed size)
- **Inventory Matching**: 5-10 seconds
- **AI Summary Generation**: 15-30 seconds per advisory (Ollama overhead)
- **Total Scan**: 2-5 minutes (with AI summaries)

---

**✨ You're all set! Happy scanning!**
